"""Car selection sidebar with search/filter."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt


_CLASS_ICONS = {
    "Tuner": "[T]",
    "Sport": "[S]",
    "Exotic": "[E]",
    "Muscle": "[M]",
    "SUV": "[4x4]",
}


class Sidebar(QWidget):
    car_selected = Signal(str)  # emits car_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_cars: list[dict] = []
        self._build_ui()
        self.setFixedWidth(230)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("sidebarHeader")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(12, 12, 12, 8)
        title = QLabel("VEHICLES")
        title.setObjectName("sidebarTitle")
        hl.addWidget(title)
        layout.addWidget(header)

        # Search box
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        sl = QVBoxLayout(search_container)
        sl.setContentsMargins(8, 6, 8, 6)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search cars...")
        self._search.setObjectName("searchBox")
        self._search.textChanged.connect(self._filter)
        sl.addWidget(self._search)
        layout.addWidget(search_container)

        # Car list
        self._list = QListWidget()
        self._list.setObjectName("carList")
        self._list.currentItemChanged.connect(self._on_selection)
        layout.addWidget(self._list)

        # Car count
        self._count_label = QLabel("0 cars")
        self._count_label.setObjectName("countLabel")
        self._count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._count_label)

    def populate(self, cars: list[dict]) -> None:
        """Load the full car list."""
        self._all_cars = cars
        self._render(cars)

    def _render(self, cars: list[dict]) -> None:
        self._list.clear()
        for car in cars:
            icon = _CLASS_ICONS.get(car.get("class", ""), "[?]")
            label = f"{icon}  {car['name']}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, car["id"])
            item.setToolTip(
                f"{car['name']}\n"
                f"Class: {car.get('class', '—')}\n"
                f"Drive: {car.get('drive', '—')}"
            )
            self._list.addItem(item)
        self._count_label.setText(f"{len(cars)} car{'s' if len(cars) != 1 else ''}")

    def _filter(self, text: str) -> None:
        q = text.lower()
        filtered = [c for c in self._all_cars
                    if q in c["name"].lower() or q in c.get("class", "").lower()]
        self._render(filtered)

    def _on_selection(self, current: QListWidgetItem, _prev) -> None:
        if current is not None:
            car_id = current.data(Qt.UserRole)
            if car_id:
                self.car_selected.emit(car_id)

    def select_first(self) -> None:
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def current_car_id(self) -> str | None:
        item = self._list.currentItem()
        return item.data(Qt.UserRole) if item else None
