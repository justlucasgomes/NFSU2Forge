"""
BUN Parser — reads and writes per-car physics from GlobalB.lzc.

All offsets are relative to the car's "manufacturer base": the position of
the manufacturer string (LINCOLN, CADILLAC, VOLKSWAGEN, …) inside the file,
which sits exactly 0xC0 bytes after the first car-identifier string.

Offsets were confirmed through hex analysis of GlobalB.lzc by comparing
multiple cars (NAVIGATOR, ESCALADE, HUMMER, SUPRA, SKYLINE, GOLF, RX7).
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

from .bun_loader import BunLoader

log = logging.getLogger(__name__)

# ── Offset of manufacturer string relative to first car-identifier ─────────
MFR_OFFSET = 0xC0

# ── Per-car field definitions ──────────────────────────────────────────────
# Each entry: (rel_offset, label, min, max, decimals, step, unit, tooltip)
# rel_offset is relative to the manufacturer string (base).
#
# Special: grip_rear is stored as a negative float; the parser exposes the
# absolute value and re-applies the sign on write.

FIELD_DEFS: dict[str, tuple] = {
    # ── Chassis ────────────────────────────────────────────────────────────
    "mass_tonnes":   (0x0160, "Mass",          0.5,  5.0,  3, 0.050, "t",   "Vehicle mass in tonnes  (×1000 = kg)"),
    "brake_force":   (0x02c0, "Brake Force",   0.5,  3.0,  3, 0.010, "",    "Braking force coefficient"),
    "cog_height":    (0x02c8, "CoG Height",    0.10, 1.50, 3, 0.010, "m",   "Center-of-gravity height"),

    # ── Engine ─────────────────────────────────────────────────────────────
    # NOTE: turbo_boost was removed — offset +0x0238 is actually gear 5 of a
    # secondary (stock) gear table at +0x0228, not boost pressure.
    # The real forced-induction flag lives at +0x0210 (0.0=NA, 0.5/1.0=turbo),
    # but it appears to be a category flag rather than a continuous pressure value.
    "peak_rpm":      (0x0244, "Peak RPM",    2000, 12000,   0, 100.0, "RPM", "RPM at peak power"),
    "max_rpm":       (0x0248, "Max RPM",     3000, 14000,   0, 100.0, "RPM", "Rev limiter / redline"),
    "torque_0":      (0x0250, "Torque pt 0",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 0 (idle)"),
    "torque_1":      (0x0254, "Torque pt 1",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 1"),
    "torque_2":      (0x0258, "Torque pt 2",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 2"),
    "torque_3":      (0x025c, "Torque pt 3",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 3 (peak)"),
    "torque_4":      (0x0260, "Torque pt 4",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 4"),
    "torque_5":      (0x0264, "Torque pt 5",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 5"),
    "torque_6":      (0x0268, "Torque pt 6",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 6"),
    "torque_7":      (0x026c, "Torque pt 7",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 7"),
    "torque_8":      (0x0270, "Torque pt 8",   0.0,  2.0,  4, 0.005, "",    "Normalized torque — RPM point 8 (high)"),

    # ── Transmission ───────────────────────────────────────────────────────
    # Real full gear set confirmed at +0x03C8 (supports up to 6 gears).
    # Slot 7 (+0x03E0) = reverse gear (~0.8000) — not exposed.
    # +0x0218 is an INTEGER storing the actual gear count (4, 5, or 6).
    "gear_1":        (0x03c8, "Gear 1",   0.5, 10.0, 4, 0.010, "",    "1st gear ratio  (higher = shorter/more torque)"),
    "gear_2":        (0x03cc, "Gear 2",   0.5,  6.0, 4, 0.010, "",    "2nd gear ratio"),
    "gear_3":        (0x03d0, "Gear 3",   0.3,  5.0, 4, 0.010, "",    "3rd gear ratio"),
    "gear_4":        (0x03d4, "Gear 4",   0.3,  4.0, 4, 0.010, "",    "4th gear ratio"),
    "gear_5":        (0x03d8, "Gear 5",   0.0,  3.0, 4, 0.010, "",    "5th gear ratio"),
    "gear_6":        (0x03dc, "Gear 6",   0.0,  2.0, 4, 0.010, "",    "6th gear ratio"),

    # ── Handling ───────────────────────────────────────────────────────────
    "grip_front":    (0x0064, "Front Grip",     0.3, 2.0, 4, 0.005, "",  "Front lateral grip coefficient"),
    "grip_rear":     (0x0094, "Rear Grip",      0.3, 2.0, 4, 0.005, "",  "Rear lateral grip coefficient  (stored as −value)"),
    "steer_lock":    (0x01c4, "Steer Lock",    20.0,80.0, 1, 0.500, "°", "Maximum steering angle in degrees"),
    "susp_spring_f": (0x012c, "Spring Front",  0.5, 5.0, 4, 0.010, "",   "Front suspension spring stiffness"),
    "susp_damp_f":   (0x0130, "Damper Front",  0.5, 5.0, 4, 0.010, "",   "Front suspension damping rate"),
    "susp_spring_r": (0x014c, "Spring Rear",   0.5, 5.0, 4, 0.010, "",   "Rear suspension spring stiffness"),
    "susp_damp_r":   (0x0150, "Damper Rear",   0.5, 5.0, 4, 0.010, "",   "Rear suspension damping rate"),
}

# Fields stored as negative in the binary (we expose positive values in the UI)
NEGATIVE_FIELDS = {"grip_rear"}

# ── Car identifier → binary search bytes ──────────────────────────────────
# Maps the NFSU2_CAR_DATABASE car_id to the bytes to search for in GlobalB.lzc.
# Matched against the first occurrence (which is the primary identifier block).
#
# Notes:
#  - "TT" uses 8 null bytes to avoid false positive at 0x000DEA6D
#  - "RX7" needs no null (RX8 differs at char 3)
#  - "GTO\x00" avoids matching unrelated strings
#  - LANCER and LANCEREVO8 share the same physics block (LANCEREVO8)
#  - NEON/S2000/IMPREZA do not have standalone blocks in GlobalB.lzc
CAR_IDENTIFIERS: dict[str, bytes] = {
    # ── Tuners ─────────────────────────────────────────────────────────────
    "240SX":       b"240SX",
    "CIVIC":       b"CIVIC",
    "ECLIPSE":     b"ECLIPSE",
    "RSX":         b"RSX",
    "SENTRA":      b"SENTRA",
    "LANCER":      b"LANCEREVO8",   # shares block with EVO — no standalone LANCER block
    "TIBURON":     b"TIBURON",
    "TT":          b"TT\x00\x00\x00\x00\x00\x00\x00\x00",  # long pattern avoids false positive
    "A3":          b"A3\x00",
    "GOLF":        b"GOLF\x00",     # null avoids matching GOLFR32
    "CELICA":      b"CELICA",
    "FOCUS":       b"FOCUS",
    "COROLLA":     b"COROLLA",
    "PEUGEOT_206": b"PEUGOT\x00",   # null avoids matching PEUGOT106
    "PEUGEOT_106": b"PEUGOT106",
    "CORSA":       b"CORSA",
    # ── Sport ──────────────────────────────────────────────────────────────
    "350Z":        b"350Z",
    "3000GT":      b"3000GT",
    "G35":         b"G35\x00",
    "IS300":       b"IS300",
    "RX8":         b"RX8",
    "MIATA":       b"MIATA",
    "RX7":         b"RX7\x00",      # null avoids matching RX8 if order changes
    "SKYLINE":     b"SKYLINE",
    "SUPRA":       b"SUPRA",
    # ── Muscle ─────────────────────────────────────────────────────────────
    "MUSTANGGT":   b"MUSTANGGT",
    "GTO":         b"GTO\x00",
    # ── Exotic ─────────────────────────────────────────────────────────────
    "IMPREZAWRX":  b"IMPREZAWRX",
    "LANCEREVO8":  b"LANCEREVO8",
    # ── SUV ────────────────────────────────────────────────────────────────
    "ESCALADE":    b"ESCALADE",
    "HUMMER":      b"HUMMER",
    "NAVIGATOR":   b"NAVIGATOR",
}


# Offset of the gear-count integer (uint32) relative to manufacturer base.
_GEAR_COUNT_OFFSET = 0x0218


@dataclass
class CarBinaryData:
    """All confirmed binary physics values for one car."""
    car_id: str
    base_offset: int                    # absolute offset of manufacturer string
    values: dict[str, float] = field(default_factory=dict)
    gear_count: int = 4                 # actual gear count from binary integer at +0x0218

    def get(self, field_name: str, default: float = 0.0) -> float:
        return self.values.get(field_name, default)


class BunParser:
    """
    Reads and writes per-car physics from a loaded BunLoader.

    Usage:
        parser = BunParser(loader)
        data = parser.read_car("NAVIGATOR")
        data.values["mass_tonnes"] = 1.85
        parser.write_car(data)
    """

    def __init__(self, loader: BunLoader):
        self._loader = loader
        self._cache: dict[str, CarBinaryData] = {}

    # ── Public API ─────────────────────────────────────────────────────────
    def find_base(self, car_id: str) -> int:
        """
        Locate the manufacturer-string base offset for *car_id*.
        Returns -1 if not found.
        """
        id_bytes = CAR_IDENTIFIERS.get(car_id)
        if id_bytes is None:
            # Try the car_id itself as a fallback
            id_bytes = car_id.encode("ascii")

        pos = self._loader.find_identifier(id_bytes)
        if pos == -1:
            log.debug("BunParser: identifier not found for %s", car_id)
            return -1
        return pos + MFR_OFFSET

    def read_car(self, car_id: str) -> Optional[CarBinaryData]:
        """Read all confirmed fields for *car_id* from the binary file."""
        base = self.find_base(car_id)
        if base == -1:
            return None

        values: dict[str, float] = {}
        for fname, fdef in FIELD_DEFS.items():
            rel_off = fdef[0]
            raw = self._loader.read_float(base + rel_off)
            # Expose absolute value for negative-stored fields
            values[fname] = abs(raw) if fname in NEGATIVE_FIELDS else raw

        # Read gear count from confirmed integer offset
        import struct as _struct
        data_bytes = self._loader._data
        raw_gc = _struct.unpack_from("<I", data_bytes, base + _GEAR_COUNT_OFFSET)[0]
        gear_count = int(raw_gc) if 3 <= raw_gc <= 7 else 4

        cbd = CarBinaryData(car_id=car_id, base_offset=base, values=values,
                            gear_count=gear_count)
        self._cache[car_id] = cbd
        log.debug("BunParser: read %s @ base=0x%X  gears=%d", car_id, base, gear_count)
        return cbd

    def write_car(self, data: CarBinaryData) -> None:
        """Write all values in *data* back to the binary file (in memory)."""
        base = data.base_offset
        for fname, value in data.values.items():
            if fname not in FIELD_DEFS:
                continue
            rel_off = FIELD_DEFS[fname][0]
            # Re-apply sign for fields stored as negative
            write_value = -abs(value) if fname in NEGATIVE_FIELDS else value
            self._loader.patch_float(base + rel_off, write_value)
        self._cache[data.car_id] = data
        log.info("BunParser: wrote %s @ base=0x%X", data.car_id, base)

    def get_cached(self, car_id: str) -> Optional[CarBinaryData]:
        return self._cache.get(car_id)

    def supported_car_ids(self) -> list[str]:
        """Return car IDs that are present in the loaded file."""
        return [cid for cid in CAR_IDENTIFIERS if self.find_base(cid) != -1]
