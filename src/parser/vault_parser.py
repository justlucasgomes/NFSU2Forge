"""
NFSU2 Vault Parser

Reads physics data from SPEED2.EXE using confirmed binary offsets discovered
through hex analysis of the US retail version (4,800,512 bytes).

Architecture:
  - GlobalPhysicsBlock  : confirmed offsets, all values readable/writable
  - CarPhysics entries  : populated from NFSU2_CAR_DATABASE (per-car binary
                          offsets are pending further reverse engineering)

To contribute per-car offsets, see CONTRIBUTING.md.
"""
from __future__ import annotations
import logging
import struct
from pathlib import Path
from typing import Optional

from .exe_loader import ExeLoader, ExeValidationError
from src.models.car_data import (
    CarPhysics, NFSU2_CAR_DATABASE,
    EngineData, ChassisData, HandlingData, AeroData
)

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# Confirmed offset map for SPEED2.EXE US v1.0 (verified via hex analysis)
# ──────────────────────────────────────────────────────────────────────────
GLOBAL_PHYSICS_BASE = 0x38D75C

# Field name → byte offset relative to GLOBAL_PHYSICS_BASE
GLOBAL_PHYSICS_FIELDS: dict[str, int] = {
    "max_speed_cap":    0x00,   # 300.9   – global speed limiter (km/h)
    "friction":         0x04,   # 0.9961  – global surface friction
    "steering_range":   0x08,   # 32767.0 – steering input range
    "grip_default":     0x10,   # 0.5     – base grip multiplier
    "wheelbase":        0x14,   # 24.0    – default wheelbase
    "tire_friction":    0x18,   # 0.5     – tire friction base
    "aero_drag":        0x1C,   # 1.0     – aerodynamic drag multiplier
    "aero_lift":        0x20,   # 0.75    – aerodynamic lift multiplier
    "downforce":        0x24,   # 1.0     – downforce multiplier
    "gear_ratio_1":     0x2C,   # 2.78    – default 1st gear ratio
    "gear_ratio_2":     0x30,   # 2.78    – default 2nd gear ratio
    "gear_ratio_3":     0x34,   # 2.78    – default 3rd gear ratio
    "rpm_audio_min":    0x3C,   # 32000   – engine audio RPM floor
    "rpm_audio_max":    0x40,   # 40000   – engine audio RPM ceiling
    "idle_rpm":         0x4C,   # 3900.0  – idle RPM
    "stall_rpm":        0x50,   # 4000.0  – stall RPM threshold
}

ENGINE_DEFAULTS_BASE = 0x3885BC
ENGINE_DEFAULTS_FIELDS: dict[str, int] = {
    "engine_stall_rpm":  0x04,  # 3000.0
    "efficiency":        0x08,  # 0.85
    "peak_torque_rpm":   0x14,  # 2500.0
    "max_torque":        0x18,  # 725.0  Nm
    "max_rpm":           0x1C,  # 24000.0
    "redline":           0x20,  # 22.0
    "top_speed":         0x24,  # 90.0
    "acceleration":      0x28,  # 25.0
    "max_grip":          0x2C,  # 100.0
    "max_brake":         0x30,  # 450.0
    "mass_default":      0x4C,  # 900.0 kg
}

STEERING_DEFAULTS_BASE = 0x3844D0
STEERING_DEFAULTS_FIELDS: dict[str, int] = {
    "steering_max_angle":  0x04,   # 45.0 degrees
    "steering_min_angle":  0x0C,   # -45.0 degrees
    "steering_gain":       0x14,   # 6666.67
}


class GlobalPhysics:
    """
    Wrapper around the confirmed global physics block in SPEED2.EXE.
    All values in this class can be read AND written back to the EXE.
    """
    def __init__(self, loader: ExeLoader):
        self._loader = loader
        self.values: dict[str, float] = {}
        self.engine_values: dict[str, float] = {}
        self.steering_values: dict[str, float] = {}
        self._read()

    def _read(self) -> None:
        for name, rel_off in GLOBAL_PHYSICS_FIELDS.items():
            self.values[name] = self._loader.read_float(GLOBAL_PHYSICS_BASE + rel_off)

        for name, rel_off in ENGINE_DEFAULTS_FIELDS.items():
            self.engine_values[name] = self._loader.read_float(
                ENGINE_DEFAULTS_BASE + rel_off
            )

        for name, rel_off in STEERING_DEFAULTS_FIELDS.items():
            self.steering_values[name] = self._loader.read_float(
                STEERING_DEFAULTS_BASE + rel_off
            )

        log.debug("GlobalPhysics read: %s", self.values)

    def write_field(self, field_name: str, value: float) -> bool:
        """
        Write a single global physics field back into the loaded EXE bytes.
        Returns True if the field was found and written, False otherwise.
        """
        if field_name in GLOBAL_PHYSICS_FIELDS:
            offset = GLOBAL_PHYSICS_BASE + GLOBAL_PHYSICS_FIELDS[field_name]
            self._loader.patch_float(offset, value)
            self.values[field_name] = value
            log.info("Patched global field '%s' = %f @ 0x%X", field_name, value, offset)
            return True

        if field_name in ENGINE_DEFAULTS_FIELDS:
            offset = ENGINE_DEFAULTS_BASE + ENGINE_DEFAULTS_FIELDS[field_name]
            self._loader.patch_float(offset, value)
            self.engine_values[field_name] = value
            return True

        if field_name in STEERING_DEFAULTS_FIELDS:
            offset = STEERING_DEFAULTS_BASE + STEERING_DEFAULTS_FIELDS[field_name]
            self._loader.patch_float(offset, value)
            self.steering_values[field_name] = value
            return True

        log.warning("Field '%s' has no confirmed EXE offset (not written).", field_name)
        return False


class VaultParser:
    """
    Top-level parser for the NFSU2 SPEED2.EXE vault.

    Usage:
        parser = VaultParser(exe_loader)
        car_list = parser.get_car_list()
        physics = parser.get_car_physics("SUPRA")
    """

    def __init__(self, loader: ExeLoader):
        self._loader = loader
        self._global = GlobalPhysics(loader)
        self._dirty: dict[str, CarPhysics] = {}   # car_id → modified CarPhysics

    @property
    def global_physics(self) -> GlobalPhysics:
        return self._global

    def get_car_list(self) -> list[dict]:
        """
        Return metadata for all known NFSU2 playable cars,
        sorted alphabetically by display name.
        """
        result = []
        for car_id, cp in NFSU2_CAR_DATABASE.items():
            result.append({
                "id": car_id,
                "name": cp.display_name,
                "manufacturer": cp.manufacturer,
                "class": cp.car_class,
                "drive": cp.drive_type,
            })
        return sorted(result, key=lambda x: x["name"])

    def get_car_physics(self, car_id: str) -> Optional[CarPhysics]:
        """
        Return CarPhysics for the given car ID.
        If the car has been modified this session, returns the modified copy.
        """
        if car_id in self._dirty:
            return self._dirty[car_id]

        if car_id in NFSU2_CAR_DATABASE:
            return NFSU2_CAR_DATABASE[car_id].clone()

        log.warning("Unknown car ID: %s", car_id)
        return None

    def mark_dirty(self, car_id: str, physics: CarPhysics) -> None:
        """Record a modified CarPhysics as pending save."""
        self._dirty[car_id] = physics

    def get_dirty_cars(self) -> dict[str, CarPhysics]:
        return dict(self._dirty)

    def clear_dirty(self) -> None:
        self._dirty.clear()

    def build_global_patch_map(self, car_id: str, physics: CarPhysics) -> dict[str, float]:
        """
        Build a map of {global_field_name: new_value} for any physics fields
        that correspond to confirmed global EXE offsets.

        Currently maps:
          - aero.drag_coefficient → global aero_drag
          - handling.steering_lock → global steering_max_angle
          - engine.idle_rpm       → global idle_rpm
        """
        patches: dict[str, float] = {}

        # These global fields affect ALL cars but are still useful to adjust
        patches["idle_rpm"] = physics.engine.idle_rpm
        patches["steering_max_angle"] = physics.handling.steering_lock
        patches["aero_drag"] = physics.aero.drag_coefficient

        return patches
