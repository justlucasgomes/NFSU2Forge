"""
Main application window.
"""
from __future__ import annotations
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QLabel, QSplitter,
    QSizePolicy
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QIcon, QKeySequence

from src.parser.exe_loader import ExeLoader, ExeValidationError
from src.parser.vault_parser import VaultParser
from src.parser.bun_loader import BunLoader, BunValidationError
from src.parser.bun_parser import BunParser
from src.core.backup_manager import BackupManager
from src.core.preset_manager import PresetManager
from src.core.save_manager import SaveManager, SaveError
from src.models.car_data import CarPhysics

from src.ui.sidebar import Sidebar
from src.ui.editor_panel import EditorPanel

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._loader: ExeLoader | None = None
        self._vault: VaultParser | None = None
        self._backup: BackupManager | None = None
        self._save_mgr: SaveManager | None = None
        self._preset_mgr = PresetManager()
        self._pending_changes: dict[str, CarPhysics] = {}
        self._bun_loader: BunLoader | None = None
        self._bun_parser: BunParser | None = None
        self._bun_dirty: bool = False

        self._settings = QSettings("NFSU2Mods", "NFSU2CarTuning")
        self._build_ui()
        self._restore_geometry()

    # ──────────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self.setWindowTitle("NFSU2 Car Tuning  —  No file loaded")
        self.setMinimumSize(1100, 700)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status_label = QLabel("Open SPEED2.EXE to begin")
        self._status.addWidget(self._status_label)

        # Toolbar
        self._build_toolbar()

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter: sidebar | editor
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setObjectName("mainSplitter")

        self._sidebar = Sidebar()
        self._sidebar.car_selected.connect(self._on_car_selected)
        splitter.addWidget(self._sidebar)

        self._editor = EditorPanel()
        self._editor.set_preset_manager(self._preset_mgr)
        self._editor.physics_changed.connect(self._on_physics_changed)
        self._editor.binary_changed.connect(self._on_binary_changed)
        self._editor.save_requested.connect(self._on_save)
        splitter.addWidget(self._editor)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Welcome overlay
        self._show_welcome()

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        # Open EXE
        open_action = QAction("Open SPEED2.EXE", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Load SPEED2.EXE from your NFSU2 game folder")
        open_action.triggered.connect(self._on_open)
        tb.addAction(open_action)

        # Open BUN
        open_bun_action = QAction("Open GlobalB.lzc", self)
        open_bun_action.setStatusTip(
            "Load GlobalB.lzc to enable per-car binary editing (Binary Patch tab)"
        )
        open_bun_action.triggered.connect(self._on_open_bun)
        tb.addAction(open_bun_action)

        tb.addSeparator()

        # Backup
        self._backup_action = QAction("Create Backup", self)
        self._backup_action.setStatusTip("Create a timestamped backup of SPEED2.EXE")
        self._backup_action.setEnabled(False)
        self._backup_action.triggered.connect(self._on_backup)
        tb.addAction(self._backup_action)

        # Restore
        self._restore_action = QAction("Restore Backup", self)
        self._restore_action.setStatusTip("Restore the most recent backup")
        self._restore_action.setEnabled(False)
        self._restore_action.triggered.connect(self._on_restore)
        tb.addAction(self._restore_action)

        tb.addSeparator()

        # Save EXE
        self._save_action = QAction("Write to EXE", self)
        self._save_action.setShortcut(QKeySequence.Save)
        self._save_action.setStatusTip("Write all pending changes to SPEED2.EXE")
        self._save_action.setEnabled(False)
        self._save_action.triggered.connect(self._on_save)
        tb.addAction(self._save_action)

        # Save BUN
        self._save_bun_action = QAction("Write to GlobalB.lzc", self)
        self._save_bun_action.setStatusTip("Write Binary Patch changes to GlobalB.lzc")
        self._save_bun_action.setEnabled(False)
        self._save_bun_action.triggered.connect(self._on_save_bun)
        tb.addAction(self._save_bun_action)

        tb.addSeparator()

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # About
        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about)
        tb.addAction(about_action)

    def _show_welcome(self) -> None:
        self._set_status("Ready — open SPEED2.EXE to begin editing.")

    # ──────────────────────────────────────────────────────────────────────
    # File operations
    # ──────────────────────────────────────────────────────────────────────

    def _on_open(self) -> None:
        last_dir = self._settings.value("last_exe_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, "Open SPEED2.EXE",
            str(last_dir),
            "Executables (SPEED2.EXE *.exe);;All Files (*)"
        )
        if not path:
            return

        exe_path = Path(path)
        self._settings.setValue("last_exe_dir", str(exe_path.parent))

        try:
            loader = ExeLoader(exe_path)
            loader.load()
        except ExeValidationError as exc:
            QMessageBox.critical(self, "Invalid File", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", f"Failed to load EXE:\n{exc}")
            return

        self._loader = loader
        self._vault = VaultParser(loader)
        self._backup = BackupManager(exe_path)
        self._save_mgr = SaveManager(loader, self._vault, self._backup)
        self._pending_changes.clear()

        # Enable actions
        self._backup_action.setEnabled(True)
        self._restore_action.setEnabled(True)
        self._save_action.setEnabled(True)

        # Load car list
        cars = self._vault.get_car_list()
        self._sidebar.populate(cars)
        self._sidebar.select_first()

        self.setWindowTitle(f"NFSU2 Car Tuning  —  {exe_path.name}")
        self._set_status(f"Loaded: {exe_path}  |  {len(cars)} cars available")

    def _on_backup(self) -> None:
        if self._backup is None:
            return
        try:
            path = self._backup.create_backup()
            self._set_status(f"Backup created: {path.name}")
            QMessageBox.information(self, "Backup Created",
                                    f"Backup saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed", str(exc))

    def _on_restore(self) -> None:
        if self._save_mgr is None:
            return
        reply = QMessageBox.question(
            self, "Restore Backup",
            "This will overwrite SPEED2.EXE with the most recent backup.\n"
            "All unsaved changes will be lost. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        success = self._save_mgr.restore_backup()
        if success:
            self._set_status("Backup restored successfully.")
            QMessageBox.information(self, "Restored", "Backup restored successfully.")
        else:
            QMessageBox.warning(self, "Restore Failed",
                                "No backup found, or restore failed.")

    def _on_save(self) -> None:
        if self._save_mgr is None:
            return
        if not self._pending_changes:
            self._set_status("No changes to save.")
            return

        # Auto-backup on first save
        try:
            backup_path = self._save_mgr.ensure_backup()
            log.info("Auto-backup before save: %s", backup_path)
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed",
                                 f"Could not create backup before saving:\n{exc}\n\n"
                                 "Save aborted for safety.")
            return

        try:
            written, skipped = self._save_mgr.save(self._pending_changes)
            self._pending_changes.clear()
            msg = (f"Saved successfully.\n\n"
                   f"- {written} global field(s) written to EXE\n"
                   f"- {skipped} field(s) skipped (per-car offsets pending RE)")
            self._set_status(f"Saved: {written} fields written, {skipped} pending.")
            QMessageBox.information(self, "Save Complete", msg)
        except SaveError as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Save Error",
                                 f"An unexpected error occurred:\n{exc}")

    # ──────────────────────────────────────────────────────────────────────
    # Car selection & editing
    # ──────────────────────────────────────────────────────────────────────

    def _on_open_bun(self) -> None:
        last_dir = self._settings.value("last_bun_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, "Open GlobalB.lzc",
            str(last_dir),
            "LZC Files (GlobalB.lzc *.lzc);;All Files (*)"
        )
        if not path:
            return

        bun_path = Path(path)
        self._settings.setValue("last_bun_dir", str(bun_path.parent))

        try:
            loader = BunLoader(bun_path)
            loader.load()
        except BunValidationError as exc:
            QMessageBox.critical(self, "Invalid File", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", f"Failed to load GlobalB.lzc:\n{exc}")
            return

        self._bun_loader = loader
        self._bun_parser = BunParser(loader)
        self._bun_dirty = False

        self._save_bun_action.setEnabled(True)
        self._editor.set_bun_parser(self._bun_parser)

        # Reload current car so Binary Patch tab populates immediately
        if self._vault is not None:
            sidebar_selection = self._sidebar.current_car_id()
            if sidebar_selection:
                self._on_car_selected(sidebar_selection)

        self._set_status(
            f"GlobalB.lzc loaded: {bun_path.name}  "
            f"·  Binary Patch tab now active"
        )

    def _on_save_bun(self) -> None:
        if self._bun_loader is None:
            return
        try:
            bak = self._bun_loader.create_backup()
            log.info("BUN auto-backup: %s", bak)
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed",
                                 f"Could not create backup:\n{exc}\n\nSave aborted.")
            return
        try:
            self._bun_loader.save()
            self._bun_dirty = False
            self._save_bun_action.setText("Write to GlobalB.lzc")
            self._set_status(f"GlobalB.lzc saved  ·  backup → {bak.name}")
            QMessageBox.information(self, "Saved",
                                    f"GlobalB.lzc written successfully.\nBackup: {bak.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))

    def _on_binary_changed(self, car_id: str, data) -> None:
        self._bun_dirty = True
        self._save_bun_action.setText("Write to GlobalB.lzc  *")
        self._set_status(f"Binary changes pending — {car_id}  ·  click 'Write to GlobalB.lzc' to save")

    def _on_car_selected(self, car_id: str) -> None:
        if self._vault is None:
            return
        physics = self._vault.get_car_physics(car_id)
        if physics is None:
            return
        self._editor.load_car(car_id, physics)
        self._set_status(f"Editing: {physics.display_name}")

    def _on_physics_changed(self, car_id: str, physics: CarPhysics) -> None:
        self._pending_changes[car_id] = physics
        self._vault.mark_dirty(car_id, physics)
        self._set_status(f"Unsaved changes: {len(self._pending_changes)} car(s) modified")

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)
        log.info(message)

    def _on_about(self) -> None:
        QMessageBox.about(
            self, "About NFSU2 Car Tuning",
            "<h3>NFSU2 Car Tuning v1.0.0</h3>"
            "<p>A professional mod tool for Need for Speed Underground 2.</p>"
            "<p>Edits vehicle physics data stored in SPEED2.EXE.</p>"
            "<p><b>Confirmed EXE offsets:</b> Global physics block (0x38D75C), "
            "Engine defaults (0x3885BC), Steering (0x3844D0).<br>"
            "Per-car offsets are pending further reverse engineering &mdash; "
            "contributions welcome on GitHub.</p>"
            "<p>&copy; 2024 &middot; MIT License &middot; "
            "<a href='https://github.com/nfsu2-car-tuning'>GitHub</a></p>"
        )

    def _restore_geometry(self) -> None:
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1280, 800)

    def closeEvent(self, event) -> None:
        if self._pending_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                f"You have unsaved changes to {len(self._pending_changes)} car(s).\n"
                "Close without saving?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        self._settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
