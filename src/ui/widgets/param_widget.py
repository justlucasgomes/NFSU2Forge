"""
ParamWidget — a horizontal row containing:
  [Label]  [═══════════○═══] slider  [  12.50 ] spinbox  [unit]
with tooltip support and dirty-state indicator.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSlider, QDoubleSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ParamWidget(QWidget):
    """A single parameter row with synced slider + spinbox."""

    value_changed = Signal(float)

    def __init__(
        self,
        label: str,
        min_val: float,
        max_val: float,
        default: float,
        decimals: int = 2,
        step: float = 0.01,
        unit: str = "",
        tooltip: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._min = min_val
        self._max = max_val
        self._decimals = decimals
        self._step = step
        self._blocking = False

        self._build_ui(label, default, unit, tooltip)
        self.set_value(default)

    # ──────────────────────────────────────────────────────────────────────
    def _build_ui(self, label: str, default: float, unit: str, tooltip: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Label
        lbl = QLabel(label)
        lbl.setFixedWidth(160)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setObjectName("paramLabel")
        if tooltip:
            lbl.setToolTip(tooltip)
        layout.addWidget(lbl)

        # Slider
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, 10000)
        self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._slider.setObjectName("paramSlider")
        if tooltip:
            self._slider.setToolTip(tooltip)
        layout.addWidget(self._slider)

        # Spinbox
        self._spin = QDoubleSpinBox()
        self._spin.setRange(self._min, self._max)
        self._spin.setDecimals(self._decimals)
        self._spin.setSingleStep(self._step)
        self._spin.setFixedWidth(90)
        self._spin.setObjectName("paramSpinbox")
        if tooltip:
            self._spin.setToolTip(tooltip)
        layout.addWidget(self._spin)

        # Unit
        if unit:
            unit_lbl = QLabel(unit)
            unit_lbl.setFixedWidth(40)
            unit_lbl.setObjectName("paramUnit")
            layout.addWidget(unit_lbl)

        # Connect
        self._slider.valueChanged.connect(self._on_slider_changed)
        self._spin.valueChanged.connect(self._on_spin_changed)

    # ──────────────────────────────────────────────────────────────────────
    def _to_slider(self, value: float) -> int:
        span = self._max - self._min
        if span == 0:
            return 0
        return int((value - self._min) / span * 10000)

    def _from_slider(self, tick: int) -> float:
        span = self._max - self._min
        return self._min + tick / 10000.0 * span

    def _on_slider_changed(self, tick: int) -> None:
        if self._blocking:
            return
        self._blocking = True
        value = self._from_slider(tick)
        self._spin.setValue(value)
        self._blocking = False
        self.value_changed.emit(value)

    def _on_spin_changed(self, value: float) -> None:
        if self._blocking:
            return
        self._blocking = True
        self._slider.setValue(self._to_slider(value))
        self._blocking = False
        self.value_changed.emit(value)

    # ──────────────────────────────────────────────────────────────────────
    def value(self) -> float:
        return self._spin.value()

    def set_value(self, value: float) -> None:
        self._blocking = True
        clamped = max(self._min, min(self._max, value))
        self._spin.setValue(clamped)
        self._slider.setValue(self._to_slider(clamped))
        self._blocking = False
