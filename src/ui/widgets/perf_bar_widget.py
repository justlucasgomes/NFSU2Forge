"""
PerfBarWidget — animated gradient performance bar.

  [Label]  [████████████░░░░░░░░]  8 / 10
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRect
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QPen


class _BarFill(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fill = 0.0
        self.setFixedHeight(16)
        self.setMinimumWidth(120)

    def get_fill(self) -> float:
        return self._fill

    def set_fill(self, v: float) -> None:
        self._fill = max(0.0, min(1.0, v))
        self.update()

    fill = Property(float, get_fill, set_fill)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = 4  # corner radius

        # Background track
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1e1e2e"))
        p.drawRoundedRect(0, 0, w, h, r, r)

        # Filled portion
        fill_w = int(w * self._fill)
        if fill_w > 0:
            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0.0, QColor("#e05a00"))
            grad.setColorAt(0.6, QColor("#ff8c00"))
            grad.setColorAt(1.0, QColor("#ffb347"))
            p.setBrush(grad)
            p.drawRoundedRect(0, 0, fill_w, h, r, r)

        # Border
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#333344"), 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, r, r)


class PerfBarWidget(QWidget):
    def __init__(self, label: str, max_value: int = 10, parent=None):
        super().__init__(parent)
        self._max = max_value
        self._current = 0
        self._anim: QPropertyAnimation | None = None
        self._build_ui(label)

    def _build_ui(self, label: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(100)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setObjectName("perfBarLabel")
        layout.addWidget(lbl)

        self._bar = _BarFill()
        layout.addWidget(self._bar)

        self._value_lbl = QLabel("—")
        self._value_lbl.setFixedWidth(40)
        self._value_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._value_lbl.setObjectName("perfBarValue")
        layout.addWidget(self._value_lbl)

    def set_value(self, value: float) -> None:
        target_fill = value / self._max
        self._value_lbl.setText(f"{value:.0f}")

        if self._anim:
            self._anim.stop()

        self._anim = QPropertyAnimation(self._bar, b"fill", self)
        self._anim.setDuration(400)
        self._anim.setStartValue(self._bar.fill)
        self._anim.setEndValue(target_fill)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()
