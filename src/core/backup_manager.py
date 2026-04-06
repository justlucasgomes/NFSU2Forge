"""Automatic backup management for SPEED2.EXE."""
from __future__ import annotations
import shutil
import time
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class BackupManager:
    def __init__(self, exe_path: Path):
        self.exe_path = exe_path
        self.backup_dir = exe_path.parent / "nfsu2_tuning_backups"

    def create_backup(self) -> Path:
        """
        Copy SPEED2.EXE to the backup directory with a timestamp.
        Raises RuntimeError if the backup fails.
        """
        self.backup_dir.mkdir(exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"SPEED2_{timestamp}.EXE"

        shutil.copy2(self.exe_path, backup_path)

        if not backup_path.exists():
            raise RuntimeError(f"Backup was not created at {backup_path}")

        log.info("Backup created: %s", backup_path)
        return backup_path

    def list_backups(self) -> list[Path]:
        """Return all backup files, newest first."""
        if not self.backup_dir.exists():
            return []
        return sorted(self.backup_dir.glob("SPEED2_*.EXE"), reverse=True)

    def restore_latest(self) -> bool:
        """Restore the most recent backup. Returns True on success."""
        backups = self.list_backups()
        if not backups:
            log.warning("No backups found to restore.")
            return False
        return self.restore(backups[0])

    def restore(self, backup_path: Path) -> bool:
        """Restore a specific backup file."""
        if not backup_path.exists():
            log.error("Backup file not found: %s", backup_path)
            return False
        shutil.copy2(backup_path, self.exe_path)
        log.info("Restored from backup: %s", backup_path)
        return True
