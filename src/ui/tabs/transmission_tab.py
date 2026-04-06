"""Transmission parameters tab."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QHBoxLayout, QPushButton, QLabel
)
from PySide6.QtCore import Signal, Qt

from src.models.car_data import CarPhysics
from src.ui.widgets.param_widget import ParamWidget


class TransmissionTab(QWidget):
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

        # ── Gear ratios table ─────────────────────────────────────────────
        gear_group = QGroupBox("Gear Ratios")
        gear_layout = QVBoxLayout(gear_group)

        self._gear_table = QTableWidget(0, 2)
        self._gear_table.setHorizontalHeaderLabels(["Gear", "Ratio"])
        self._gear_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self._gear_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._gear_table.setColumnWidth(0, 80)
        self._gear_table.setFixedHeight(200)
        self._gear_table.setObjectName("gearTable")
        self._gear_table.itemChanged.connect(self._on_gear_changed)
        gear_layout.addWidget(self._gear_table)

        layout.addWidget(gear_group)

        # ── Drive parameters ──────────────────────────────────────────────
        drive_group = QGroupBox("Drive Parameters")
        drive_layout = QVBoxLayout(drive_group)
        drive_layout.setSpacing(4)

        self._params: dict[str, ParamWidget] = {}

        def add(attr, label, mn, mx, dec, step, unit, tip):
            pw = ParamWidget(label, mn, mx, 0.0, dec, step, unit, tip)
            pw.value_changed.connect(lambda v, a=attr: self._on_change(a, v))
            drive_layout.addWidget(pw)
            self._params[attr] = pw

        add("final_drive", "Final Drive Ratio", 2.0, 6.0, 3, 0.01, "",
            "Final drive (differential) ratio — higher = more acceleration, lower = higher top speed.")
        add("reverse_ratio", "Reverse Ratio", 2.0, 5.0, 3, 0.01, "",
            "Gear ratio for reverse gear.")
        add("shift_time", "Shift Time", 0.05, 0.60, 3, 0.01, "s",
            "Time taken to complete a gear change.")

        layout.addWidget(drive_group)
        layout.addStretch()

    def load_car(self, physics: CarPhysics) -> None:
        self._building = True
        self._physics = physics
        t = physics.transmission

        # Populate gear table
        self._gear_table.blockSignals(True)
        self._gear_table.setRowCount(0)
        gear_names = ["1st", "2nd", "3rd", "4th", "5th", "6th"]
        for i, ratio in enumerate(t.gear_ratios):
            row = self._gear_table.rowCount()
            self._gear_table.insertRow(row)
            name_item = QTableWidgetItem(gear_names[i] if i < len(gear_names) else f"{i+1}st")
            name_item.setFlags(Qt.ItemIsEnabled)  # read-only
            self._gear_table.setItem(row, 0, name_item)
            ratio_item = QTableWidgetItem(f"{ratio:.4f}")
            self._gear_table.setItem(row, 1, ratio_item)
        self._gear_table.blockSignals(False)

        self._params["final_drive"].set_value(t.final_drive)
        self._params["reverse_ratio"].set_value(t.reverse_ratio)
        self._params["shift_time"].set_value(t.shift_time)

        self._building = False

    def _on_gear_changed(self, item: QTableWidgetItem) -> None:
        if self._building or self._physics is None or item.column() != 1:
            return
        row = item.row()
        try:
            value = float(item.text())
        except ValueError:
            return
        if row < len(self._physics.transmission.gear_ratios):
            self._physics.transmission.gear_ratios[row] = value
            self.physics_changed.emit(self._physics)

    def _on_change(self, attr: str, value: float) -> None:
        if self._building or self._physics is None:
            return
        setattr(self._physics.transmission, attr, value)
        self.physics_changed.emit(self._physics)
