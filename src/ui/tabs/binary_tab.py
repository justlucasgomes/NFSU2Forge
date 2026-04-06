"""
Binary Patch tab — edits confirmed per-car fields in GlobalB.lzc.

Shows a placeholder when no file is loaded.  Once BunParser is attached
via set_parser(), selecting a car calls load_car() which populates all
widgets with live values read from the file.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QScrollArea, QFrame, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Signal, Qt

from src.ui.widgets.param_widget import ParamWidget
from src.parser.bun_parser import BunParser, CarBinaryData, FIELD_DEFS

# ── Field groupings for the UI ─────────────────────────────────────────────
GROUPS: dict[str, list[str]] = {
    "Chassis": ["mass_tonnes", "brake_force", "cog_height"],
    "Engine":  ["turbo_boost", "peak_rpm", "max_rpm",
                "torque_0", "torque_1", "torque_2", "torque_3", "torque_4",
                "torque_5", "torque_6", "torque_7", "torque_8"],
    "Transmission": ["gear_1", "gear_2", "gear_3", "gear_4"],
    "Handling": ["grip_front", "grip_rear", "steer_lock",
                 "susp_spring_f", "susp_damp_f",
                 "susp_spring_r", "susp_damp_r"],
}


class _Placeholder(QWidget):
    """Shown when GlobalB.lzc is not loaded."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("📂")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon)

        msg = QLabel(
            "<b>GlobalB.lzc not loaded</b><br><br>"
            "Use <i>File → Open GlobalB.lzc</i> to enable<br>"
            "direct per-car binary editing."
        )
        msg.setAlignment(Qt.AlignCenter)
        msg.setObjectName("placeholderLabel")
        msg.setWordWrap(True)
        layout.addWidget(msg)


class BinaryTab(QWidget):
    """
    Tab that exposes all confirmed GlobalB.lzc fields as sliders/spinboxes.

    Signals:
        binary_changed(car_id, CarBinaryData) — emitted on any field edit.
    """
    binary_changed = Signal(str, object)   # car_id, CarBinaryData

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parser: BunParser | None = None
        self._current_car_id: str | None = None
        self._data: CarBinaryData | None = None
        self._params: dict[str, ParamWidget] = {}
        self._building = False
        self._build_ui()

    # ── Setup ──────────────────────────────────────────────────────────────
    def set_parser(self, parser: BunParser | None) -> None:
        self._parser = parser
        self._stack.setCurrentWidget(
            self._editor if parser is not None else self._placeholder
        )

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Stack: placeholder ↔ editor
        from PySide6.QtWidgets import QStackedWidget
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._placeholder = _Placeholder()
        self._stack.addWidget(self._placeholder)

        self._editor = self._build_editor()
        self._stack.addWidget(self._editor)

        self._stack.setCurrentWidget(self._placeholder)

    def _build_editor(self) -> QWidget:
        editor = QWidget()
        outer = QVBoxLayout(editor)
        outer.setContentsMargins(0, 0, 0, 0)

        # Offset info bar
        info_bar = QFrame()
        info_bar.setObjectName("binaryInfoBar")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(12, 4, 12, 4)
        self._offset_label = QLabel("Offsets: GlobalB.lzc (confirmed via hex analysis)")
        self._offset_label.setObjectName("binaryOffsetLabel")
        self._offset_label.setStyleSheet("color: #888; font-size: 10px;")
        info_layout.addWidget(self._offset_label)
        info_layout.addStretch()
        outer.addWidget(info_bar)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        for group_name, field_names in GROUPS.items():
            group = QGroupBox(group_name)
            g_layout = QVBoxLayout(group)
            g_layout.setSpacing(4)

            for fname in field_names:
                if fname not in FIELD_DEFS:
                    continue
                _, label, mn, mx, dec, step, unit, tip = FIELD_DEFS[fname]
                pw = ParamWidget(label, mn, mx, 0.0, dec, step, unit, tip)
                pw.value_changed.connect(
                    lambda v, f=fname: self._on_field_changed(f, v)
                )
                g_layout.addWidget(pw)
                self._params[fname] = pw

            layout.addWidget(group)

        layout.addStretch()
        return editor

    # ── Load car ───────────────────────────────────────────────────────────
    def load_car(self, car_id: str) -> None:
        if self._parser is None:
            return

        self._current_car_id = car_id
        self._data = self._parser.read_car(car_id)

        if self._data is None:
            self._offset_label.setText(
                f"⚠  {car_id} not found in GlobalB.lzc — block not mapped yet."
            )
            self._set_widgets_enabled(False)
            return

        self._offset_label.setText(
            f"Base offset: 0x{self._data.base_offset:08X}  ·  "
            f"GlobalB.lzc  ·  {len(self._params)} confirmed fields"
        )
        self._set_widgets_enabled(True)

        self._building = True
        for fname, pw in self._params.items():
            pw.set_value(self._data.values.get(fname, 0.0))
        self._building = False

    def _set_widgets_enabled(self, enabled: bool) -> None:
        for pw in self._params.values():
            pw.setEnabled(enabled)

    # ── Edit handler ───────────────────────────────────────────────────────
    def _on_field_changed(self, field_name: str, value: float) -> None:
        if self._building or self._data is None:
            return
        self._data.values[field_name] = value
        self._parser.write_car(self._data)
        if self._current_car_id:
            self.binary_changed.emit(self._current_car_id, self._data)
