"""Engine parameters tab."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QFrame, QLabel
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QPainter, QPen, QFont

from src.models.car_data import CarPhysics
from src.ui.widgets.param_widget import ParamWidget


class TorqueChart(QFrame):
    """Simple torque curve chart using QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setObjectName("torqueChart")
        self._curve: list[tuple[float, float]] = []

    def set_curve(self, curve: list[tuple[float, float]]) -> None:
        self._curve = curve
        self.update()

    def paintEvent(self, _event) -> None:
        if not self._curve:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width() - 16, self.height() - 24
        ox, oy = 8, 8

        # Background
        p.fillRect(self.rect(), QColor("#111122"))

        # Grid lines
        p.setPen(QPen(QColor("#2a2a3a"), 1))
        for i in range(1, 5):
            y = oy + h * i // 5
            p.drawLine(ox, y, ox + w, y)

        # Curve
        max_rpm = max(pt[0] for pt in self._curve)
        max_torque = max(pt[1] for pt in self._curve)
        if max_rpm == 0 or max_torque == 0:
            return

        points = [
            (ox + int(rpm / max_rpm * w),
             oy + h - int(torque / max_torque * h))
            for rpm, torque in self._curve
        ]

        pen = QPen(QColor("#ff8c00"), 2)
        p.setPen(pen)
        for i in range(len(points) - 1):
            p.drawLine(*points[i], *points[i + 1])

        # Dots
        p.setBrush(QColor("#ffb347"))
        p.setPen(QPen(QColor("#ffb347"), 1))
        for x, y in points:
            p.drawEllipse(x - 3, y - 3, 6, 6)

        # Axis labels
        p.setPen(QColor("#666677"))
        p.setFont(QFont("Segoe UI", 7))
        p.drawText(ox, oy + h + 14, f"0")
        p.drawText(ox + w - 20, oy + h + 14, f"{int(max_rpm)} RPM")


class EngineTab(QWidget):
    physics_changed = Signal(object)  # emits updated CarPhysics

    def __init__(self, parent=None):
        super().__init__(parent)
        self._physics: CarPhysics | None = None
        self._building = False
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Torque curve chart ────────────────────────────────────────────
        chart_group = QGroupBox("Torque Curve")
        chart_layout = QVBoxLayout(chart_group)
        self._chart = TorqueChart()
        chart_layout.addWidget(self._chart)
        layout.addWidget(chart_group)

        # ── Engine parameters ─────────────────────────────────────────────
        eng_group = QGroupBox("Engine Parameters")
        eng_layout = QVBoxLayout(eng_group)
        eng_layout.setSpacing(4)

        self._params: dict[str, ParamWidget] = {}

        def add(attr, label, mn, mx, dec, step, unit, tip):
            pw = ParamWidget(label, mn, mx, 0.0, dec, step, unit, tip)
            pw.value_changed.connect(lambda v, a=attr: self._on_change(a, v))
            eng_layout.addWidget(pw)
            self._params[attr] = pw

        add("max_torque", "Max Torque", 50, 800, 1, 1.0, "Nm",
            "Peak torque output of the engine in Newton-metres.")
        add("max_power", "Max Power", 30, 600, 1, 1.0, "kW",
            "Maximum power output (1 kW approx 1.34 hp).")
        add("max_rpm", "Max RPM", 4000, 12000, 0, 100.0, "RPM",
            "Engine rev limiter — the absolute ceiling before fuel cut.")
        add("redline_rpm", "Redline RPM", 3000, 11000, 0, 100.0, "RPM",
            "Optimal shift point — the RPM where peak power is delivered.")
        add("idle_rpm", "Idle RPM", 300, 2000, 0, 50.0, "RPM",
            "Engine idle speed when stationary.")

        layout.addWidget(eng_group)
        layout.addStretch()

    def load_car(self, physics: CarPhysics) -> None:
        self._building = True
        self._physics = physics
        e = physics.engine
        self._params["max_torque"].set_value(e.max_torque)
        self._params["max_power"].set_value(e.max_power)
        self._params["max_rpm"].set_value(e.max_rpm)
        self._params["redline_rpm"].set_value(e.redline_rpm)
        self._params["idle_rpm"].set_value(e.idle_rpm)

        # Update torque curve chart with RPM-scaled points
        curve = [(rpm * e.max_rpm / 1.0, torque_norm * e.max_torque)
                 for rpm, torque_norm in e.torque_curve]
        self._chart.set_curve(curve)

        self._building = False

    def _on_change(self, attr: str, value: float) -> None:
        if self._building or self._physics is None:
            return
        setattr(self._physics.engine, attr, value)

        # Refresh chart when relevant fields change
        if attr in ("max_torque", "max_rpm"):
            e = self._physics.engine
            curve = [(rpm * e.max_rpm, torque_norm * e.max_torque)
                     for rpm, torque_norm in e.torque_curve]
            self._chart.set_curve(curve)

        self.physics_changed.emit(self._physics)
