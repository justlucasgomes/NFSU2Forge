"""
Main application window — NFS2Forge.

Flow:
  1. User clicks "Open GlobalB.lzc"
  2. BunLoader + BunParser initialise
  3. Sidebar is populated from the cars found in the binary
  4. User selects a car → EditorPanel loads live binary values
  5. User edits → in-memory patch applied immediately
  6. User clicks Write → auto-backup, then file written to disk
"""
from __future__ import annotations
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QLabel, QSplitter,
    QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence

from src.parser.bun_loader import BunLoader, BunValidationError
from src.parser.bun_parser import BunParser
from src.models.car_data import NFSU2_CAR_DATABASE
from src.i18n.translations import tr, set_language, get_language, AVAILABLE_LANGUAGES

from src.ui.sidebar import Sidebar
from src.ui.editor_panel import EditorPanel

log = logging.getLogger(__name__)

APP_VERSION = "1.0.0"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._bun_loader: BunLoader | None = None
        self._bun_parser: BunParser | None = None
        self._bun_dirty: bool = False

        self._settings = QSettings("NFSU2Mods", "NFS2Forge")
        # Restore saved language before building UI
        saved_lang = self._settings.value("language", "en")
        set_language(saved_lang)
        self._build_ui()
        self._restore_geometry()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setWindowTitle(f"NFS2Forge v{APP_VERSION}  —  No file loaded")
        self.setMinimumSize(1100, 700)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status_label = QLabel(tr("status_ready"))
        self._status.addWidget(self._status_label)

        self._build_toolbar()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setObjectName("mainSplitter")

        self._sidebar = Sidebar()
        self._sidebar.car_selected.connect(self._on_car_selected)
        splitter.addWidget(self._sidebar)

        self._editor = EditorPanel()
        self._editor.binary_changed.connect(self._on_binary_changed)
        self._editor.save_requested.connect(self._on_save_bun)
        splitter.addWidget(self._editor)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        self._open_bun_action = QAction(tr("open_file"), self)
        self._open_bun_action.setShortcut(QKeySequence.Open)
        self._open_bun_action.setStatusTip(tr("open_file_tip"))
        self._open_bun_action.triggered.connect(self._on_open_bun)
        tb.addAction(self._open_bun_action)

        tb.addSeparator()

        self._save_bun_action = QAction(tr("write_file"), self)
        self._save_bun_action.setShortcut(QKeySequence.Save)
        self._save_bun_action.setStatusTip(tr("write_file_tip"))
        self._save_bun_action.setEnabled(False)
        self._save_bun_action.triggered.connect(self._on_save_bun)
        tb.addAction(self._save_bun_action)

        tb.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # Language selector
        lang_label = QLabel(f"  {tr('language')}: ")
        lang_label.setObjectName("langLabel")
        tb.addWidget(lang_label)

        self._lang_combo = QComboBox()
        self._lang_combo.setObjectName("langCombo")
        self._lang_combo.setFixedWidth(145)
        for code, name in AVAILABLE_LANGUAGES.items():
            self._lang_combo.addItem(name, code)
        # Set current
        idx = self._lang_combo.findData(get_language())
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        tb.addWidget(self._lang_combo)

        tb.addSeparator()

        self._about_action = QAction(tr("about"), self)
        self._about_action.triggered.connect(self._on_about)
        tb.addAction(self._about_action)

    # ── File operations ────────────────────────────────────────────────────

    def _on_language_changed(self, _index: int) -> None:
        code = self._lang_combo.currentData()
        set_language(code)
        self._settings.setValue("language", code)
        self._apply_language()

    def _apply_language(self) -> None:
        """Refresh all translatable UI strings after a language change."""
        self._open_bun_action.setText(tr("open_file"))
        self._open_bun_action.setStatusTip(tr("open_file_tip"))
        self._save_bun_action.setText(tr("write_file"))
        self._save_bun_action.setStatusTip(tr("write_file_tip"))
        self._about_action.setText(tr("about"))
        self._status_label.setText(tr("status_ready"))
        self._editor.refresh_language()
        self._sidebar.refresh_language()

    def _on_open_bun(self) -> None:
        last_dir = self._settings.value("last_bun_dir", "")
        path, _ = QFileDialog.getOpenFileName(
            self, tr("open_file"),
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
            QMessageBox.critical(self, tr("invalid_file_title"), str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, tr("load_error_title"),
                                 tr("load_error_body", err=exc))
            return

        self._bun_loader = loader
        self._bun_parser = BunParser(loader)
        self._bun_dirty = False

        self._save_bun_action.setEnabled(True)
        self._editor.set_bun_parser(self._bun_parser)

        # Populate sidebar with cars found in this binary
        cars = self._build_car_list()
        self._sidebar.populate(cars)
        self._sidebar.select_first()

        self.setWindowTitle(f"NFS2Forge v{APP_VERSION}  —  {bun_path.name}")
        self._set_status(
            f"Loaded: {bun_path}  ·  {len(cars)} {tr('cars_available')}"
        )

    def _build_car_list(self) -> list[dict]:
        """Return sidebar-ready dicts for all cars found in the loaded binary."""
        if self._bun_parser is None:
            return []
        found_ids = self._bun_parser.supported_car_ids()
        result = []
        for car_id in found_ids:
            cp = NFSU2_CAR_DATABASE.get(car_id)
            if cp is None:
                # Fallback for cars in binary but not in DB
                result.append({
                    "id": car_id,
                    "name": car_id,
                    "manufacturer": "",
                    "class": "Unknown",
                    "drive": "",
                })
            else:
                result.append({
                    "id": car_id,
                    "name": cp.display_name,
                    "manufacturer": cp.manufacturer,
                    "class": cp.car_class,
                    "drive": cp.drive_type,
                })
        return sorted(result, key=lambda x: (x["class"], x["name"]))

    def _on_save_bun(self) -> None:
        if self._bun_loader is None:
            return
        try:
            bak = self._bun_loader.create_backup()
        except Exception as exc:
            QMessageBox.critical(self, tr("backup_failed_title"),
                                 tr("backup_failed_body", err=exc))
            return
        try:
            self._bun_loader.save()
            self._bun_dirty = False
            self._save_bun_action.setText(tr("write_file"))
            self._set_status(f"{tr('status_saved')}  ·  {tr('status_backup')} → {bak.name}")
            QMessageBox.information(self, tr("saved_title"),
                                    tr("saved_body", bak=bak.name))
        except Exception as exc:
            QMessageBox.critical(self, tr("save_error_title"), str(exc))

    # ── Car selection ──────────────────────────────────────────────────────

    def _on_car_selected(self, car_id: str) -> None:
        cp = NFSU2_CAR_DATABASE.get(car_id)
        self._editor.load_car(car_id, cp)
        name = cp.display_name if cp else car_id
        self._set_status(f"{tr('status_editing')}: {name}")

    def _on_binary_changed(self, car_id: str, _data) -> None:
        self._bun_dirty = True
        self._save_bun_action.setText(f"{tr('write_file')}  *")
        cp = NFSU2_CAR_DATABASE.get(car_id)
        name = cp.display_name if cp else car_id
        self._set_status(f"{tr('status_unsaved')} — {name}")

    # ── Helpers ────────────────────────────────────────────────────────────

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)
        log.info(message)

    def _on_about(self) -> None:
        QMessageBox.about(
            self, f"About NFS2Forge v{APP_VERSION}",
            f"<h3>NFS2Forge v{APP_VERSION}</h3>"
            "<p>Car physics editor for <b>Need for Speed Underground 2</b>.</p>"
            "<p>Directly patches <code>GlobalB.lzc</code> using confirmed binary offsets "
            "for all 32 playable cars.</p>"
            "<p><b>Fields:</b> Mass · Brakes · CoG · Turbo · RPM · Torque curve (9 pts) "
            "· Gears 1–6 · Grip · Steering · Suspension</p>"
            "<p>&copy; 2024 &middot; MIT License &middot; "
            "<a href='https://github.com/justlucasgomes/NFSU2Forge'>GitHub</a></p>"
        )

    def _restore_geometry(self) -> None:
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1280, 800)

    def closeEvent(self, event) -> None:
        if self._bun_dirty:
            reply = QMessageBox.question(
                self, tr("unsaved_title"), tr("unsaved_body"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        self._settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
