"""Advanced / chassis parameters tab."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QFrame, QLabel
)
from PySide6.QtCore import Signal

from src.models.car_data import CarPhysics
from src.ui.widgets.param_widget import ParamWidget


class AdvancedTab(QWidget):
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

        # ── Vehicle mass & inertia ─────────────────────────────────────────
        mass_group = QGroupBox("Mass & Inertia")
        ml = QVBoxLayout(mass_group)
        ml.setSpacing(4)
        add(ml, "mass", "Vehicle Mass", 800, 5000, 1, 10.0, "kg",
            "Total vehicle mass including fluids but excluding driver.")
        add(ml, "inertia_x", "Inertia X (Roll)", 200, 8000, 0, 10.0, "kg*m2",
            "Rotational inertia around the longitudinal (roll) axis.")
        add(ml, "inertia_y", "Inertia Y (Pitch)", 500, 12000, 0, 10.0, "kg*m2",
            "Rotational inertia around the lateral (pitch) axis.")
        add(ml, "inertia_z", "Inertia Z (Yaw)", 200, 8000, 0, 10.0, "kg*m2",
            "Rotational inertia around the vertical (yaw) axis. Affects turn-in response.")
        layout.addWidget(mass_group)

        # ── Centre of mass ────────────────────────────────────────────────
        com_group = QGroupBox("Centre of Mass")
        cl = QVBoxLayout(com_group)
        cl.setSpacing(4)
        add(cl, "center_of_mass_x", "CoM X (Left/Right)", -0.5, 0.5, 3, 0.005, "m",
            "Lateral CoM offset. 0 = centred. Positive = right.")
        add(cl, "center_of_mass_y", "CoM Y (Height)", -0.5, 0.2, 3, 0.005, "m",
            "Vertical CoM. Negative = lower. Lower CoM = better handling.")
        add(cl, "center_of_mass_z", "CoM Z (Front/Rear)", -0.5, 0.5, 3, 0.005, "m",
            "Longitudinal CoM. Positive = toward front. Affects balance.")
        layout.addWidget(com_group)

        # ── Aerodynamics ──────────────────────────────────────────────────
        aero_group = QGroupBox("Aerodynamics")
        al = QVBoxLayout(aero_group)
        al.setSpacing(4)
        add(al, "drag_coefficient", "Drag Coefficient (Cd)", 0.15, 0.80, 3, 0.01, "",
            "Aerodynamic drag (Cd). Lower = higher top speed. Typical: 0.28-0.40.")
        add(al, "lift_front", "Front Lift", -0.5, 0.2, 3, 0.01, "",
            "Front downforce (negative = down). Affects high-speed front grip.")
        add(al, "lift_rear", "Rear Lift", -0.5, 0.2, 3, 0.01, "",
            "Rear downforce. More negative = more rear stability at high speed.")
        add(al, "top_speed", "Top Speed", 80, 400, 1, 1.0, "km/h",
            "Theoretical top speed. Limited by drag and power.")
        layout.addWidget(aero_group)

        # ── Warning notice ────────────────────────────────────────────────
        note = QLabel(
            "Warning: Advanced parameters affect simulation accuracy.\n"
            "   Extreme values may cause instability or crashes in-game.\n"
            "   A backup is always created before any changes are written."
        )
        note.setObjectName("warningLabel")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def load_car(self, physics: CarPhysics) -> None:
        self._building = True
        self._physics = physics
        c = physics.chassis
        a = physics.aero

        self._params["mass"].set_value(c.mass)
        self._params["inertia_x"].set_value(c.inertia_x)
        self._params["inertia_y"].set_value(c.inertia_y)
        self._params["inertia_z"].set_value(c.inertia_z)
        self._params["center_of_mass_x"].set_value(c.center_of_mass_x)
        self._params["center_of_mass_y"].set_value(c.center_of_mass_y)
        self._params["center_of_mass_z"].set_value(c.center_of_mass_z)
        self._params["drag_coefficient"].set_value(a.drag_coefficient)
        self._params["lift_front"].set_value(a.lift_front)
        self._params["lift_rear"].set_value(a.lift_rear)
        self._params["top_speed"].set_value(a.top_speed)

        self._building = False

    def _on_change(self, attr: str, value: float) -> None:
        if self._building or self._physics is None:
            return
        if hasattr(self._physics.chassis, attr):
            setattr(self._physics.chassis, attr, value)
        elif hasattr(self._physics.aero, attr):
            setattr(self._physics.aero, attr, value)
        self.physics_changed.emit(self._physics)
