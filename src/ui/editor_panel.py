"""
Editor panel — single-page layout with all confirmed binary fields.

Layout
──────
  [Car header]
  [4 stat bars]
  ┌──────────┬──────────┐
  │ Chassis  │ Engine   │  ← 2-column grid
  ├──────────┼──────────┤
  │ Gearbox  │ Handling │
  └──────────┴──────────┘
  [action bar]
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QScrollArea, QFrame, QLabel, QPushButton,
    QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor, QPainter, QPen

from src.models.car_data import CarPhysics
from src.ui.widgets.param_widget import ParamWidget
from src.parser.bun_parser import BunParser, CarBinaryData, FIELD_DEFS
from src.i18n.translations import tr


# ── Stat bar ──────────────────────────────────────────────────────────────
class _StatBar(QWidget):
    """A labelled progress bar used for the performance overview."""
    def __init__(self, label: str, color: str = "#ff8c00", parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._color = color
        self.setMinimumHeight(52)
        self.setMinimumWidth(90)
        self._label = label

    def set_value(self, v: float) -> None:
        self._value = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background track
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1a1a2e"))
        p.drawRoundedRect(0, 0, w, h, 6, 6)

        # Fill
        fill_w = int(w * self._value)
        if fill_w > 0:
            p.setBrush(QColor(self._color))
            p.drawRoundedRect(0, 0, fill_w, h, 6, 6)

        # Label
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(0, 0, w, h // 2 + 2, Qt.AlignCenter, self._label)

        # Percentage
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor("#cccccc"))
        p.drawText(0, h // 2, w, h // 2, Qt.AlignCenter,
                   f"{int(self._value * 100)}%")


# ── Placeholder ────────────────────────────────────────────────────────────
class _Placeholder(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel("🚗")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 56px;")
        layout.addWidget(icon)

        title = QLabel(tr("welcome_title"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff8c00;")
        layout.addWidget(title)

        msg = QLabel(tr("welcome_msg"))
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("color: #888; font-size: 12px; line-height: 1.8;")
        msg.setWordWrap(True)
        layout.addWidget(msg)


# ── Section group factory ──────────────────────────────────────────────────
def _make_group(title: str, fields: list[str], params: dict) -> QGroupBox:
    group = QGroupBox(title)
    group.setObjectName("binaryGroup")
    layout = QVBoxLayout(group)
    layout.setSpacing(3)
    layout.setContentsMargins(8, 10, 8, 8)
    for fname in fields:
        if fname in params:
            layout.addWidget(params[fname])
    return group


# ── Main editor panel ──────────────────────────────────────────────────────
class EditorPanel(QWidget):
    physics_changed = Signal(str, object)   # kept for compatibility
    binary_changed  = Signal(str, object)   # car_id, CarBinaryData
    save_requested  = Signal()

    # Field groups displayed in the 2×2 grid
    _GROUPS = {
        "Chassis":      ["mass_tonnes", "brake_force", "cog_height"],
        "Engine":       ["peak_rpm", "max_rpm",
                         "torque_0", "torque_1", "torque_2", "torque_3",
                         "torque_4", "torque_5", "torque_6", "torque_7",
                         "torque_8"],
        "Gearbox":      ["gear_1", "gear_2", "gear_3", "gear_4", "gear_5", "gear_6"],
        "Handling":     ["grip_front", "grip_rear", "steer_lock",
                         "susp_spring_f", "susp_damp_f",
                         "susp_spring_r", "susp_damp_r"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parser: BunParser | None = None
        self._current_car_id: str | None = None
        self._data: CarBinaryData | None = None
        self._params: dict[str, ParamWidget] = {}
        self._building = False
        self._preset_manager = None
        self._build_ui()

    # ── Compatibility shim ─────────────────────────────────────────────────
    def set_preset_manager(self, mgr) -> None:
        self._preset_manager = mgr   # not used in the new layout

    def set_bun_parser(self, parser: BunParser | None) -> None:
        self._parser = parser
        if parser is not None:
            self._stack.setCurrentWidget(self._editor_widget)
        # If a car is already selected, reload it
        if self._current_car_id and parser:
            self.load_car(self._current_car_id, None)

    # ── Build UI ───────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Stack: placeholder | editor
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._placeholder = _Placeholder()
        self._stack.addWidget(self._placeholder)

        self._editor_widget = self._build_editor()
        self._stack.addWidget(self._editor_widget)

        self._stack.setCurrentWidget(self._placeholder)

    def _build_editor(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Car header ─────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("carInfoHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 14, 20, 14)

        self._name_lbl = QLabel("—")
        self._name_lbl.setObjectName("carNameLabel")
        hl.addWidget(self._name_lbl)

        hl.addStretch()

        self._meta_lbl = QLabel("")
        self._meta_lbl.setObjectName("carMetaLabel")
        hl.addWidget(self._meta_lbl)

        outer.addWidget(header)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("separator")
        outer.addWidget(sep)

        # ── Stat bars ──────────────────────────────────────────────────────
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_frame.setFixedHeight(70)
        sl = QHBoxLayout(stats_frame)
        sl.setContentsMargins(20, 8, 20, 8)
        sl.setSpacing(10)

        bar_defs = [
            ("Acceleration", "#ff6b35"),
            ("Top Speed",    "#ff8c00"),
            ("Handling",     "#4ecdc4"),
            ("Braking",      "#e74c3c"),
            ("Drift",        "#9b59b6"),
        ]
        self._bars: dict[str, _StatBar] = {}
        for label, color in bar_defs:
            bar = _StatBar(label, color)
            sl.addWidget(bar)
            self._bars[label.lower().replace(" ", "_")] = bar

        outer.addWidget(stats_frame)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine); sep2.setObjectName("separator")
        outer.addWidget(sep2)

        # ── Offset info strip ──────────────────────────────────────────────
        self._info_strip = QLabel("Select a car to begin editing")
        self._info_strip.setObjectName("binaryOffsetLabel")
        self._info_strip.setContentsMargins(20, 4, 20, 4)
        self._info_strip.setStyleSheet(
            "color: #666; font-size: 10px; background: #0d0d1a;"
        )
        outer.addWidget(self._info_strip)

        # ── Scrollable 2×2 grid ────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll, 1)

        # Build all ParamWidgets once
        for fname, fdef in FIELD_DEFS.items():
            _, label, mn, mx, dec, step, unit, tip = fdef
            pw = ParamWidget(label, mn, mx, 0.0, dec, step, unit, tip)
            pw.value_changed.connect(
                lambda v, f=fname: self._on_field_changed(f, v)
            )
            self._params[fname] = pw

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        group_order = [
            ("Chassis",  "group_chassis",  (0, 0)),
            ("Engine",   "group_engine",   (0, 1)),
            ("Gearbox",  "group_gearbox",  (1, 0)),
            ("Handling", "group_handling", (1, 1)),
        ]
        self._groups: dict[str, QGroupBox] = {}
        for name, tr_key, (row, col) in group_order:
            grp = _make_group(tr(tr_key), self._GROUPS[name], self._params)
            grp.setProperty("tr_key", tr_key)
            grid.addWidget(grp, row, col)
            self._groups[name] = grp

        scroll.setWidget(grid_w)

        # ── Action bar ─────────────────────────────────────────────────────
        action_bar = self._build_action_bar()
        outer.addWidget(action_bar)

        return w

    def _build_action_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("actionBar")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(10)

        # Reset
        self._reset_btn = QPushButton(tr("btn_reset"))
        self._reset_btn.setObjectName("secondaryBtn")
        self._reset_btn.setFixedWidth(110)
        self._reset_btn.setToolTip("Reload values from file (discard edits)")
        self._reset_btn.clicked.connect(self._reload_car)
        layout.addWidget(self._reset_btn)

        layout.addStretch()

        # Pending indicator
        self._dirty_lbl = QLabel("")
        self._dirty_lbl.setObjectName("dirtyLabel")
        self._dirty_lbl.setStyleSheet("color: #f39c12; font-size: 11px;")
        layout.addWidget(self._dirty_lbl)

        # Write button
        self._write_btn = QPushButton(tr("btn_write"))
        self._write_btn.setObjectName("saveBtn")
        self._write_btn.setFixedWidth(240)
        self._write_btn.setFixedHeight(38)
        self._write_btn.setToolTip(tr("write_file_tip"))
        self._write_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(self._write_btn)

        return bar

    # ── Load car ───────────────────────────────────────────────────────────
    def load_car(self, car_id: str, physics: CarPhysics | None) -> None:
        self._current_car_id = car_id

        # Update header from CarPhysics if available
        if physics is not None:
            self._name_lbl.setText(physics.display_name)
            self._meta_lbl.setText(
                f"{physics.year}  ·  {physics.car_class}  ·  {physics.drive_type}"
            )
            r = physics.ratings
            self._bars["acceleration"].set_value(r.acceleration / 10)
            self._bars["top_speed"].set_value(r.top_speed / 10)
            self._bars["handling"].set_value(r.handling / 10)
            self._bars["braking"].set_value(r.braking / 10)
            self._bars["drift"].set_value(r.drift / 10)
        else:
            self._name_lbl.setText(car_id)

        # Show editor even if parser not yet set (placeholder state)
        if self._parser is None:
            return

        self._stack.setCurrentWidget(self._editor_widget)
        self._data = self._parser.read_car(car_id)

        if self._data is None:
            self._info_strip.setText(
                f"⚠  {car_id} — identifier not found in GlobalB.lzc"
            )
            self._set_params_enabled(False)
            self._write_btn.setEnabled(False)
            return

        # Gear count read from confirmed binary integer (+0x0218)
        n_gears = self._data.gear_count
        self._info_strip.setText(
            f"base 0x{self._data.base_offset:08X}  ·  "
            f"{n_gears}{tr('speed_gearbox')}  ·  {len(self._params)} {tr('editable_fields')}"
        )
        self._set_params_enabled(True)
        self._write_btn.setEnabled(True)
        self._dirty_lbl.setText("")

        # Show/hide gear slots based on actual gear count from binary
        self._update_gear_visibility(n_gears)

        self._building = True
        for fname, pw in self._params.items():
            pw.set_value(self._data.values.get(fname, 0.0))
        self._building = False

    def _set_params_enabled(self, enabled: bool) -> None:
        for pw in self._params.values():
            pw.setEnabled(enabled)

    def _update_gear_visibility(self, n_gears: int) -> None:
        """Show only the gear slots this car actually has."""
        for i in range(1, 7):
            fname = f"gear_{i}"
            if fname in self._params:
                self._params[fname].setVisible(i <= n_gears)

    # ── Field edit handler ─────────────────────────────────────────────────
    def _on_field_changed(self, field_name: str, value: float) -> None:
        if self._building or self._data is None:
            return
        self._data.values[field_name] = value
        self._parser.write_car(self._data)
        self._dirty_lbl.setText(tr("dirty_label"))
        if self._current_car_id:
            self.binary_changed.emit(self._current_car_id, self._data)

    # ── Reset ──────────────────────────────────────────────────────────────
    def _reload_car(self) -> None:
        if self._current_car_id:
            self.load_car(self._current_car_id, None)
            self._dirty_lbl.setText("")

    # ── Language refresh ───────────────────────────────────────────────────
    def refresh_language(self) -> None:
        """Re-apply translations to all dynamic UI elements."""
        self._reset_btn.setText(tr("btn_reset"))
        self._write_btn.setText(tr("btn_write"))
        self._write_btn.setToolTip(tr("write_file_tip"))
        for name, grp in self._groups.items():
            key = grp.property("tr_key")
            if key:
                grp.setTitle(tr(key))
