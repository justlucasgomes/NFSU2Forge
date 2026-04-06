"""
SPEED2.EXE loader and validator.

Performs:
  1. File existence check
  2. PE header magic validation
  3. Expected file size check (loose tolerance)
  4. Returns raw bytes for further parsing
"""
from __future__ import annotations
from pathlib import Path
import struct
import logging

log = logging.getLogger(__name__)

# US retail version: 4,800,512 bytes
EXPECTED_SIZE = 4_800_512
# Allow +-100 KB for patched/modded executables
SIZE_TOLERANCE = 102_400

PE_MAGIC = b"MZ"


class ExeValidationError(Exception):
    pass


class ExeLoader:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._data: bytes | None = None

    @property
    def data(self) -> bytes:
        if self._data is None:
            raise RuntimeError("EXE not loaded. Call load() first.")
        return self._data

    def load(self) -> None:
        """Load SPEED2.EXE into memory and validate."""
        if not self.path.exists():
            raise ExeValidationError(f"File not found: {self.path}")

        file_size = self.path.stat().st_size
        log.info("Loading %s (%d bytes)", self.path.name, file_size)

        if abs(file_size - EXPECTED_SIZE) > SIZE_TOLERANCE:
            log.warning(
                "Unexpected file size: %d (expected ~%d). "
                "Proceeding with caution — offsets may be wrong.",
                file_size, EXPECTED_SIZE
            )

        self._data = self.path.read_bytes()

        # Validate PE magic
        if self._data[:2] != PE_MAGIC:
            raise ExeValidationError(
                f"Not a valid PE executable (missing MZ header): {self.path}"
            )

        log.info("EXE loaded and validated successfully.")

    def read_float(self, offset: int) -> float:
        """Read a little-endian 32-bit float at the given offset."""
        return struct.unpack_from("<f", self._data, offset)[0]

    def read_float_array(self, offset: int, count: int) -> list[float]:
        """Read `count` consecutive 32-bit floats starting at offset."""
        return list(struct.unpack_from(f"<{count}f", self._data, offset))

    def read_string(self, offset: int, max_len: int = 64) -> str:
        """Read a null-terminated ASCII string."""
        end = self._data.find(b"\x00", offset, offset + max_len)
        if end == -1:
            end = offset + max_len
        return self._data[offset:end].decode("ascii", errors="replace")

    def patch_float(self, offset: int, value: float) -> None:
        """Patch a 32-bit float at the given offset (in-memory only)."""
        data = bytearray(self._data)
        struct.pack_into("<f", data, offset, value)
        self._data = bytes(data)

    def save(self, path: Path | None = None) -> None:
        """
        Write (patched) data back to disk using a temp-file + replace strategy.
        This avoids Errno 13 (Permission denied) on Windows caused by antivirus,
        OneDrive sync, or file-handle locks.
        """
        import os
        import tempfile

        target = path or self.path

        # Write to a sibling temp file first
        tmp_fd, tmp_path_str = tempfile.mkstemp(
            dir=target.parent,
            prefix=".~" + target.stem,
            suffix=".tmp"
        )
        tmp_path = Path(tmp_path_str)

        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(self._data)
                f.flush()
                os.fsync(f.fileno())

            # On Windows, os.replace handles the atomic swap
            os.replace(tmp_path, target)
            log.info("Saved %d bytes to %s", len(self._data), target)

        except Exception:
            # Clean up temp file if anything went wrong
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
