"""
Save manager: writes modified CarPhysics data back into SPEED2.EXE.

Strategy (v1.0):
  - For confirmed global physics fields: write directly to confirmed offsets.
  - For per-car fields without confirmed offsets: log a warning, skip write.
  - Always requires a backup to have been created before calling save().
"""
from __future__ import annotations
import logging
from pathlib import Path

from src.parser.exe_loader import ExeLoader
from src.parser.vault_parser import VaultParser
from src.models.car_data import CarPhysics
from .backup_manager import BackupManager

log = logging.getLogger(__name__)


class SaveError(Exception):
    pass


class SaveManager:
    def __init__(self, loader: ExeLoader, vault: VaultParser, backup: BackupManager):
        self._loader = loader
        self._vault = vault
        self._backup = backup
        self._backup_created = False

    def save(self, cars: dict[str, CarPhysics]) -> tuple[int, int]:
        """
        Write all modified cars to the EXE.

        Returns (written_fields, skipped_fields) counts.
        Raises SaveError if backup has not been created.
        """
        if not self._backup_created:
            raise SaveError(
                "Safety check failed: create a backup before saving."
            )

        written = 0
        skipped = 0

        for car_id, physics in cars.items():
            patch_map = self._vault.build_global_patch_map(car_id, physics)
            for field_name, value in patch_map.items():
                if self._vault.global_physics.write_field(field_name, value):
                    written += 1
                else:
                    skipped += 1

        # Flush to disk
        self._loader.save()
        self._vault.clear_dirty()

        log.info("Save complete: %d written, %d skipped (no confirmed offset).",
                 written, skipped)
        return written, skipped

    def ensure_backup(self) -> Path:
        """Create backup and mark it as done. Must be called before save()."""
        backup_path = self._backup.create_backup()
        self._backup_created = True
        return backup_path

    def restore_backup(self) -> bool:
        result = self._backup.restore_latest()
        if result:
            # Reload the EXE from disk after restore
            self._loader.load()
        return result
