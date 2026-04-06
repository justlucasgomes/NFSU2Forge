"""
BUN Loader — handles read/write of GlobalB.lzc (per-car binary physics file).

GlobalB.lzc contains one physics block per car.  Each block begins with a
car-identifier string (e.g. b'NAVIGATOR') and the manufacturer name string
sits exactly 0xC0 bytes after that identifier.  All confirmed field offsets
are relative to that manufacturer string (the "base" of the block).
"""
from __future__ import annotations
import struct
import shutil
import logging
from pathlib import Path

log = logging.getLogger(__name__)

EXPECTED_MIN_SIZE = 0x800_000   # ~8 MB sanity floor


class BunValidationError(Exception):
    pass


class BunLoader:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._data: bytearray = bytearray()

    # ── I/O ───────────────────────────────────────────────────────────────
    def load(self) -> None:
        if not self.path.exists():
            raise BunValidationError(f"File not found: {self.path}")
        raw = self.path.read_bytes()
        if len(raw) < EXPECTED_MIN_SIZE:
            raise BunValidationError(
                f"File too small ({len(raw):,} bytes). "
                "Expected GlobalB.lzc (≥ 8 MB)."
            )
        self._data = bytearray(raw)
        log.info("BunLoader: loaded %s (%d bytes)", self.path.name, len(self._data))

    def save(self) -> None:
        self.path.write_bytes(bytes(self._data))
        log.info("BunLoader: saved %s", self.path.name)

    def create_backup(self) -> Path:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = self.path.with_suffix(f".lzc.bak_{ts}")
        shutil.copy2(self.path, bak)
        log.info("BunLoader: backup → %s", bak.name)
        return bak

    # ── Low-level float access ────────────────────────────────────────────
    def read_float(self, offset: int) -> float:
        return struct.unpack_from("<f", self._data, offset)[0]

    def patch_float(self, offset: int, value: float) -> None:
        struct.pack_into("<f", self._data, offset, value)

    def find_identifier(self, identifier: bytes) -> int:
        """Return offset of first occurrence of *identifier* in the file, or -1."""
        return self._data.find(identifier)

    @property
    def loaded(self) -> bool:
        return len(self._data) > 0
