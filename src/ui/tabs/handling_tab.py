"""Handling, suspension, and tyre parameters tab."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QFrame
)
from PySide6.QtCore import Signal

from src.models.car_data import CarPhysics
from src.ui.widgets.param_widget import ParamWidget


class HandlingTab(QWidget):
    physics_changed = Signal(object)

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

        self._params: dict[str, ParamWidget] = {}

        def add(group_layout, attr, label, mn, mx, dec, step, unit, tip):
            pw = ParamWidget(label, mn, mx, 0.0, dec, step, unit, tip)
            pw.value_changed.connect(lambda v, a=attr: self._on_change(a, v))
            group_layout.addWidget(pw)
            self._params[attr] = pw

        # ── Steering ──────────────────────────────────────────────────────
        steer_group = QGroupBox("Steering")
        sl = QVBoxLayout(steer_group)
        sl.setSpacing(4)
        add(sl, "steering_lock", "Steering Lock", 15, 55, 1, 0.5, "deg",
            "Maximum steering angle in degrees. Higher = more responsive but harder to control.")
        add(sl, "steering_ratio", "Steering Ratio", 10, 22, 2, 0.1, "",
            "Steering wheel to road wheel ratio. Lower = more direct steering.")
        layout.addWidget(steer_group)

        # ── Suspension ────────────────────────────────────────────────────
        susp_group = QGroupBox("Suspension")
        susp_l = QVBoxLayout(susp_group)
        susp_l.setSpacing(4)
        add(susp_l, "suspension_stiffness_f", "Front Stiffness", 5, 60, 1, 0.5, "N/mm",
            "Front spring stiffness. Higher = less body roll but rougher ride.")
        add(susp_l, "suspension_stiffness_r", "Rear Stiffness", 5, 60, 1, 0.5, "N/mm",
            "Rear spring stiffness. Higher rear stiffness increases oversteer tendency.")
        add(susp_l, "damping_front", "Front Damping", 500, 8000, 0, 50.0, "N*s/m",
            "Front shock absorber damping. Higher = less oscillation after bumps.")
        add(susp_l, "damping_rear", "Rear Damping", 500, 8000, 0, 50.0, "N*s/m",
            "Rear shock absorber damping.")
        add(susp_l, "roll_stiffness", "Anti-Roll Stiffness", 0.2, 3.0, 2, 0.05, "",
            "Anti-roll bar stiffness multiplier. Higher = less body roll in corners.")
        layout.addWidget(susp_group)

        # ── Tyres ─────────────────────────────────────────────────────────
        tyre_group = QGroupBox("Tyres")
        tyre_l = QVBoxLayout(tyre_group)
        tyre_l.setSpacing(4)
        add(tyre_l, "front_grip", "Front Grip", 0.5, 2.0, 3, 0.01, "",
            "Front tyre grip coefficient. Higher = more front traction.")
        add(tyre_l, "rear_grip", "Rear Grip", 0.5, 2.0, 3, 0.01, "",
            "Rear tyre grip coefficient. Lower = easier to drift.")
        add(tyre_l, "lateral_grip", "Lateral Grip", 0.5, 2.0, 3, 0.01, "",
            "Lateral (sideways) tyre grip. Affects cornering speed.")
        add(tyre_l, "front_slip_angle", "Front Slip Angle", 2, 20, 1, 0.5, "deg",
            "Angle at which front tyres lose grip. Higher = more progressive.")
        add(tyre_l, "rear_slip_angle", "Rear Slip Angle", 2, 20, 1, 0.5, "deg",
            "Angle at which rear tyres lose grip. Lower = easier oversteer/drift.")
        layout.addWidget(tyre_group)

        # ── Brakes ────────────────────────────────────────────────────────
        brake_group = QGroupBox("Brakes")
        brake_l = QVBoxLayout(brake_group)
        brake_l.setSpacing(4)
        add(brake_l, "front_bias", "Front Brake Bias", 0.3, 0.9, 2, 0.01, "",
            "Proportion of braking force on front wheels. Higher = more stable under braking.")
        add(brake_l, "brake_power", "Brake Power", 500, 8000, 0, 50.0, "N",
            "Total braking force available.")
        layout.addWidget(brake_group)

        layout.addStretch()

    def load_car(self, physics: CarPhysics) -> None:
        self._building = True
        self._physics = physics
        h = physics.handling
        t = physics.tyres
        b = physics.brakes

        self._params["steering_lock"].set_value(h.steering_lock)
        self._params["steering_ratio"].set_value(h.steering_ratio)
        self._params["suspension_stiffness_f"].set_value(h.suspension_stiffness_f)
        self._params["suspension_stiffness_r"].set_value(h.suspension_stiffness_r)
        self._params["damping_front"].set_value(h.damping_front)
        self._params["damping_rear"].set_value(h.damping_rear)
        self._params["roll_stiffness"].set_value(h.roll_stiffness)
        self._params["front_grip"].set_value(t.front_grip)
        self._params["rear_grip"].set_value(t.rear_grip)
        self._params["lateral_grip"].set_value(t.lateral_grip)
        self._params["front_slip_angle"].set_value(t.front_slip_angle)
        self._params["rear_slip_angle"].set_value(t.rear_slip_angle)
        self._params["front_bias"].set_value(b.front_bias)
        self._params["brake_power"].set_value(b.power)

        self._building = False

    def _on_change(self, attr: str, value: float) -> None:
        if self._building or self._physics is None:
            return
        if hasattr(self._physics.handling, attr):
            setattr(self._physics.handling, attr, value)
        elif hasattr(self._physics.tyres, attr):
            setattr(self._physics.tyres, attr, value)
        elif attr in ("front_bias", "brake_power"):
            target = "front_bias" if attr == "front_bias" else "power"
            setattr(self._physics.brakes, target, value)
        self.physics_changed.emit(self._physics)
