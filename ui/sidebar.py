"""
sidebar.py — left navigation panel.

Python/PyQt5 counterpart of the C# `panelistbutton` (an AutoScroll Panel
docked left that hosted one button per running bot instance). Here it
becomes a proper widget: a title and a scrollable list of device buttons.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    device_selected = pyqtSignal(str)      # device_id
    home_selected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("EvonyBot")
        title.setObjectName("SidebarTitle")
        outer.addWidget(title)

        self.home_button = QPushButton("🏠  Home")
        self.home_button.setCheckable(True)
        self.home_button.setChecked(True)
        self.home_button.clicked.connect(self.home_selected.emit)
        self._group.addButton(self.home_button)
        outer.addWidget(self.home_button)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch(1)
        scroll.setWidget(self._list_container)
        outer.addWidget(scroll, 1)

    def add_device(self, device_id: str, label: str | None = None) -> QPushButton:
        """Add a device entry to the list; returns the created button."""
        if device_id in self._buttons:
            return self._buttons[device_id]

        btn = QPushButton(label or device_id)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.device_selected.emit(device_id))
        self._group.addButton(btn)
        self._list_layout.insertWidget(self._list_layout.count() - 1, btn)
        self._buttons[device_id] = btn
        return btn

    def remove_device(self, device_id: str):
        btn = self._buttons.pop(device_id, None)
        if btn is not None:
            self._group.removeButton(btn)
            btn.deleteLater()

    def select_device(self, device_id: str):
        btn = self._buttons.get(device_id)
        if btn is not None:
            btn.setChecked(True)

    def select_home(self):
        self.home_button.setChecked(True)

    def device_ids(self):
        return list(self._buttons.keys())
