"""
recruit_general_tab.py — tab "Recruit General" (activity bot/activities/recruit_general/).

- Group "Setting": ô tích "Open Gold" + nhóm hai nút radio "Recruit General" / "Buy General Token" (hai nút ở màn chi tiết
  tướng), chỉ một nút được tích (mặc định Recruit General).

- Group "Generals": danh sách tướng (ui/tabs/generals.py), ô search theo tên + lọc theo civ và type, tích chọn tướng.
  Tướng đã tích vẫn giữ khi đổi search / civ; mặc định tích sẵn các tướng có `default` (generals.py).

Settings (cột `recruit_general` của DB): {"buy_with": "Recruit General" | "Buy General Token", "generals": [tên, ...], "open_gold": bool}
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from .constants import (
    GENERAL_COLUMNS,
    RECRUIT_CIV_ALL,
    RECRUIT_DESELECT_ALL_TEXT,
    RECRUIT_OPEN_GOLD_KEY,
    RECRUIT_OPEN_GOLD_TEXT,
    RECRUIT_GENERALS_GROUP,
    RECRUIT_GENERALS_KEY,
    RECRUIT_RESET_TEXT,
    RECRUIT_SEARCH_PLACEHOLDER,
    RECRUIT_SELECT_ALL_TEXT,
    RECRUIT_TYPE_ALL,
    RECRUIT_TYPE_ORDER,
    RECRUIT_BUY_DEFAULT,
    RECRUIT_BUY_KEY,
    RECRUIT_BUY_OPTIONS,
    RECRUIT_SETTING_GROUP,
    RECRUIT_TAB_TITLE,
)
from .generals import GENERALS
from .tab_placeholder import BaseTab, RadioGroup


class GeneralPicker(QGroupBox):
    """Lưới ô tích tướng (theo hàng, cột) có ô search theo tên và ô lọc civ."""

    changed = pyqtSignal()

    def __init__(self, title, generals, columns=GENERAL_COLUMNS, parent=None):
        super().__init__(title, parent)
        self._columns = columns
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText(RECRUIT_SEARCH_PLACEHOLDER)
        self.search.setClearButtonEnabled(True)
        self.civ = QComboBox()
        self.civ.addItem(RECRUIT_CIV_ALL, RECRUIT_CIV_ALL)
        for civ in sorted({g["civ"] for g in generals}):
            self.civ.addItem(civ.capitalize(), civ)   # hiện hoa chữ đầu, lọc theo giá trị gốc
        self.type = QComboBox()
        self.type.addItem(RECRUIT_TYPE_ALL, RECRUIT_TYPE_ALL)
        types = {g.get("type1", "") for g in generals} - {""}
        for type1 in [t for t in RECRUIT_TYPE_ORDER if t in types] + sorted(types - set(RECRUIT_TYPE_ORDER)):
            self.type.addItem(type1, type1)
        self._boxes = {}
        self._civs = {}
        self._types = {}
        self._defaults = {}
        holder = QWidget()
        self._grid = QGridLayout(holder)
        self._grid.setAlignment(Qt.AlignTop)
        for g in generals:
            box = QCheckBox(g["name"])
            box.setChecked(bool(g.get("default")))
            self._defaults[g["name"]] = bool(g.get("default"))
            box.toggled.connect(lambda _checked: self.changed.emit())
            self._boxes[g["name"]] = box
            self._civs[g["name"]] = g["civ"]
            self._types[g["name"]] = g.get("type1", "")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)
        scroll.setMinimumHeight(300)
        top = QHBoxLayout()
        top.addWidget(self.search, 1)
        top.addWidget(self.civ)
        top.addWidget(self.type)
        select_all = QPushButton(RECRUIT_SELECT_ALL_TEXT)
        deselect_all = QPushButton(RECRUIT_DESELECT_ALL_TEXT)
        select_all.clicked.connect(lambda: self._set_shown(True))
        deselect_all.clicked.connect(lambda: self._set_shown(False))
        top.addWidget(select_all)
        top.addWidget(deselect_all)
        reset = QPushButton(RECRUIT_RESET_TEXT)
        reset.clicked.connect(self._reset)
        top.addWidget(reset)
        layout.addLayout(top)
        layout.addWidget(scroll)
        self.search.textChanged.connect(self._filter)
        self.civ.currentTextChanged.connect(self._filter)
        self.type.currentTextChanged.connect(self._filter)
        self._filter()

    def _filter(self, *_):
        text = self.search.text().strip().lower()
        civ = self.civ.currentData()
        type1 = self.type.currentData()
        for box in self._boxes.values():
            self._grid.removeWidget(box)
            box.hide()
        shown = [name for name, box in self._boxes.items()
                 if text in name.lower() and (civ == RECRUIT_CIV_ALL or self._civs[name] == civ)
                 and (type1 == RECRUIT_TYPE_ALL or self._types[name] == type1)]
        self._shown = shown
        for i, name in enumerate(shown):
            self._grid.addWidget(self._boxes[name], i // self._columns, i % self._columns)
            self._boxes[name].show()

    def _set_shown(self, checked):
        """Tích / bỏ tích tất cả tướng đang hiện (đã qua search, civ, type); tướng bị lọc ẩn không đổi."""
        for name in self._shown:
            self._boxes[name].setChecked(checked)

    def _reset(self):
        """Về mặc định: chỉ tích các tướng `default` (toàn danh sách, không phụ thuộc bộ lọc đang chọn)."""
        for name, box in self._boxes.items():
            box.setChecked(self._defaults[name])

    def checked(self):
        return [name for name, box in self._boxes.items() if box.isChecked()]

    def set_checked(self, names):
        names = set(names)
        for name, box in self._boxes.items():
            box.blockSignals(True)
            box.setChecked(name in names)
            box.blockSignals(False)


class RecruitGeneralTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title=RECRUIT_TAB_TITLE, show_apply_all=True, parent=parent)
        # Group "Setting": ô tích "Open Gold" ở trên, dưới là nhóm hai nút radio (mỗi nhóm radio loại trừ riêng).
        self.open_gold = QCheckBox(RECRUIT_OPEN_GOLD_TEXT)
        self.open_gold.toggled.connect(lambda _checked: self.settings_changed.emit())
        self.setting = RadioGroup("", list(RECRUIT_BUY_OPTIONS), default=RECRUIT_BUY_DEFAULT,
                                  columns=len(RECRUIT_BUY_OPTIONS))
        self.setting.setFlat(True)
        self.setting.valueChanged.connect(lambda _value: self.settings_changed.emit())
        setting_box = QGroupBox(RECRUIT_SETTING_GROUP)
        box_layout = QVBoxLayout(setting_box)
        box_layout.addWidget(self.open_gold)
        box_layout.addWidget(self.setting, 0, Qt.AlignLeft)   # chỉ rộng vừa hai nút, căn trái
        self.add_row(setting_box)
        self.generals = GeneralPicker(RECRUIT_GENERALS_GROUP, GENERALS)
        self.generals.changed.connect(self.settings_changed.emit)
        self.add_row(self.generals)

    def get_settings(self) -> dict:
        return {RECRUIT_OPEN_GOLD_KEY: self.open_gold.isChecked(),
                RECRUIT_BUY_KEY: self.setting.value() or RECRUIT_BUY_DEFAULT,
                RECRUIT_GENERALS_KEY: self.generals.checked()}

    def set_settings(self, data: dict):
        self.open_gold.setChecked(bool(data.get(RECRUIT_OPEN_GOLD_KEY, False)))
        value = data.get(RECRUIT_BUY_KEY)
        if value in RECRUIT_BUY_OPTIONS:
            self.setting.set_value(value)
        names = data.get(RECRUIT_GENERALS_KEY)
        if isinstance(names, list):
            self.generals.set_checked(names)
