"""
gather_resources_tab.py — tab "Gather Resources": nút "+ Add troop" thêm một dòng (tối đa MAX_TROOP); mỗi dòng là một đội, nhãn
"Troop n" theo thứ tự dòng, ô chọn loại tài nguyên (Food, Wood, Stone, Iron, Gems), ô chọn cấp mỏ (MAX_LEVEL..1, mặc định
DEFAULT_LEVEL) và nút xoá dòng. Không chọn preset: ở màn March bot bấm March luôn.

Settings (cột `gather_resources` của DB): {"squads": [{"resource": "food", "level": 10}, ...]}
"""
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from bot.activities.gather_resources.constants import DEFAULT_LEVEL, DEFAULT_RESOURCE, MAX_LEVEL, MAX_TROOP, RESOURCES, SQUADS_KEY

from .constants import PROFILE_BUTTON_HEIGHT
from .initialization_tab import _trash_icon
from .tab_placeholder import BaseTab


class _SquadRow(QWidget):
    """Một dòng: Troop n: Gather [loại tài nguyên] [cấp] [xoá]."""

    def __init__(self, on_change, on_remove, resource: str = DEFAULT_RESOURCE, level: int = DEFAULT_LEVEL, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self.resource = QComboBox()
        for resource_id, label in RESOURCES:
            self.resource.addItem(label, resource_id)
        self.number = QLabel()
        self.level = QComboBox()
        for number in range(MAX_LEVEL, 0, -1):
            self.level.addItem(f"Lv {number}", number)
        remove = QPushButton()      # nút thùng rác giống nút xoá hồ sơ ở tab Initialization
        remove.setFixedSize(PROFILE_BUTTON_HEIGHT + 12, PROFILE_BUTTON_HEIGHT)
        remove.setStyleSheet("padding: 0px;")
        remove.setIcon(_trash_icon())
        remove.setIconSize(QSize(14, 14))
        remove.setToolTip("Delete this troop")
        row.addWidget(self.number)
        row.addWidget(QLabel("Gather"))
        row.addWidget(self.resource)
        row.addWidget(self.level)
        row.addWidget(remove)
        row.addStretch(1)
        self.set_value(resource, level)
        self.resource.currentIndexChanged.connect(lambda _=0: on_change())
        self.level.currentIndexChanged.connect(lambda _=0: on_change())
        remove.clicked.connect(lambda _=False: on_remove(self))

    def set_value(self, resource: str, level: int):
        self.resource.setCurrentIndex(max(0, self.resource.findData(resource)))
        self.level.setCurrentIndex(max(0, self.level.findData(level)))

    def value(self) -> dict:
        return {"resource": self.resource.currentData(), "level": self.level.currentData()}


class GatherResourcesTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title="Gather Resources", parent=parent)
        self.rows: list[_SquadRow] = []
        group = QGroupBox("Troops")
        outer = QVBoxLayout(group)
        self._rows_layout = QVBoxLayout()
        outer.addLayout(self._rows_layout)
        self.add_button = QPushButton("+ Add troop")
        self.add_button.clicked.connect(lambda _=False: self._add_row())
        buttons = QHBoxLayout()
        buttons.addWidget(self.add_button)
        buttons.addStretch(1)
        outer.addLayout(buttons)
        self.add_row(group)

    def _add_row(self, resource: str = DEFAULT_RESOURCE, level: int = DEFAULT_LEVEL, notify: bool = True):
        if len(self.rows) >= MAX_TROOP:      # tối đa MAX_TROOP dòng (mỗi đội một dòng)
            return
        row = _SquadRow(self.settings_changed.emit, self._remove_row, resource, level)
        self.rows.append(row)
        self._rows_layout.addWidget(row)
        self._refresh()
        if notify:
            self.settings_changed.emit()

    def _refresh(self):
        """Đánh số lại "Troop n" theo thứ tự dòng; đủ MAX_TROOP dòng thì khoá nút thêm."""
        for n, row in enumerate(self.rows, 1):
            row.number.setText(f"Troop {n}:")
        self.add_button.setEnabled(len(self.rows) < MAX_TROOP)

    def _remove_row(self, row: _SquadRow):
        self.rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()
        self._refresh()
        self.settings_changed.emit()

    def get_settings(self) -> dict:
        return {SQUADS_KEY: [row.value() for row in self.rows]}

    def set_settings(self, data: dict):
        for row in list(self.rows):
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self.rows.clear()
        for squad in data.get(SQUADS_KEY) or []:
            self._add_row(squad.get("resource", DEFAULT_RESOURCE), squad.get("level", DEFAULT_LEVEL), notify=False)
        self._refresh()
