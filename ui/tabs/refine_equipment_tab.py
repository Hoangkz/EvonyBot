"""
refine_equipment_tab.py — tab "Refine Equipment": group "General" (ô tích tướng yêu thích + loại tướng) và 6 group trang bị. Mỗi group có ô
"Max refines (per equipment)" và nút "+ Add line": mỗi lần bấm thêm một dòng cần có (tối đa 4, vì trang bị chỉ có 4 dòng tinh luyện). Mỗi dòng chọn
một thuộc tính trong danh mục của trang bị đó, màu tối thiểu (Orange / Gold), ô "Lock" (khoá dòng lại khi đã ra đúng) và nút xoá. Hai dòng có thể
cùng thuộc tính (game có thể ra trùng).

Settings (cột `refine_equipment` của DB):
{"favorite": false, "general_type": "all",
 "slots": {"weapon": {"lines": [{"attribute": "Ground Troop Attack", "color": "gold", "lock": true}, {"attribute": "Ranged Troop Attack", "color": "gold", "lock": false}],
                      "max_refines": 100}, ...}}
"""
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
)

from bot.activities.refine_equipment.constants import (
    ATTRIBUTE_KEY,
    COLOR_KEY,
    COLORS,
    DEFAULT_COLOR,
    DEFAULT_GENERAL_TYPE,
    FAVORITE_KEY,
    GENERAL_TYPE_KEY,
    GENERAL_TYPES,
    DEFAULT_MAX_REFINES,
    LINES_KEY,
    LOCK_KEY,
    MAX_LINES,
    MAX_REFINES_KEY,
    MAX_REFINES_OPTIONS,
    SLOTS,
    SLOTS_KEY,
)

from .constants import PROFILE_BUTTON_HEIGHT
from .initialization_tab import _trash_icon
from .tab_placeholder import BaseTab

COLOR_WIDTH = 70
GENERAL_TYPE_WIDTH = 170   # đủ chữ dài nhất ("Hammer (Development)")
ATTRIBUTE_CHARS = 24       # bề rộng tối thiểu của ô thuộc tính, tính theo số ký tự
ATTRIBUTE_POPUP_WIDTH = 340   # danh sách xổ ra rộng đủ tên dài nhất
BORDER = "#c7ccd4"
ROW_STYLE = "QFrame#RefineRow {{ border: 1px solid {color}; border-radius: 6px; }}"


class _LineRow(QFrame):
    """Một dòng cần có (một hàng có viền): ô chọn thuộc tính, màu tối thiểu, Lock, nút xoá."""

    def __init__(self, catalog: tuple, on_change, on_remove, parent=None):
        super().__init__(parent)
        self.setObjectName("RefineRow")
        self.setStyleSheet(ROW_STYLE.format(color=BORDER))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.attribute = QComboBox()
        for name in catalog:
            self.attribute.addItem(name, name)
        self.attribute.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.attribute.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)   # không giãn theo tên dài nhất; danh sách xổ ra vẫn hiện đủ tên
        self.attribute.setMinimumContentsLength(ATTRIBUTE_CHARS)
        self.attribute.view().setMinimumWidth(ATTRIBUTE_POPUP_WIDTH)
        self.color = QComboBox()
        for color_id, text in COLORS:
            self.color.addItem(text, color_id)
        self.color.setCurrentIndex(max(0, self.color.findData(DEFAULT_COLOR)))
        self.color.setFixedWidth(COLOR_WIDTH)
        self.lock = QCheckBox("Lock")
        self.lock.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)   # rộng đúng bằng ô tích + chữ "Lock" theo font thật, không cắt chữ
        self.lock.setToolTip("Khoá dòng này lại khi đã ra đúng thuộc tính và màu")
        remove = QPushButton()      # nút thùng rác giống nút xoá hồ sơ ở tab Initialization
        remove.setFixedSize(PROFILE_BUTTON_HEIGHT + 12, PROFILE_BUTTON_HEIGHT)
        remove.setStyleSheet("padding: 0px;")
        remove.setIcon(_trash_icon())
        remove.setIconSize(QSize(14, 14))
        remove.setToolTip("Delete this line")
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 4, 6, 4)
        row.setSpacing(8)
        row.addWidget(self.attribute, 1)
        row.addWidget(self.color)
        row.addWidget(self.lock)
        row.addWidget(remove)
        self.attribute.currentIndexChanged.connect(lambda _=0: on_change())
        self.color.currentIndexChanged.connect(lambda _=0: on_change())
        self.lock.toggled.connect(lambda _=False: on_change())
        remove.clicked.connect(lambda _=False: on_remove(self))

    def value(self) -> dict:
        return {ATTRIBUTE_KEY: self.attribute.currentData(), COLOR_KEY: self.color.currentData(), LOCK_KEY: self.lock.isChecked()}

    def set_value(self, data: dict):
        self.attribute.setCurrentIndex(max(0, self.attribute.findData(data.get(ATTRIBUTE_KEY))))
        self.color.setCurrentIndex(max(0, self.color.findData(data.get(COLOR_KEY, DEFAULT_COLOR))))
        self.lock.setChecked(bool(data.get(LOCK_KEY)))


class _SlotGroup(QGroupBox):
    """Một trang bị: ô số lần Refine tối đa, các dòng cần có (thêm bằng nút +, tối đa MAX_LINES) và nút "+ Add line"."""

    def __init__(self, label: str, catalog: tuple, on_change, parent=None):
        super().__init__(label, parent)
        self._catalog = catalog
        self._on_change = on_change
        self.rows: list[_LineRow] = []
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        # Số lần Refine tối đa của TRANG BỊ NÀY mỗi lượt (100 .. 1000 hoặc ALL = tới khi đạt); mỗi trang bị một ô riêng.
        self.max_refines = QComboBox()
        for option in MAX_REFINES_OPTIONS:
            self.max_refines.addItem(str(option), option)
        self.max_refines.setCurrentIndex(self.max_refines.findData(DEFAULT_MAX_REFINES))
        self.max_refines.currentIndexChanged.connect(lambda _=0: on_change())
        header = QHBoxLayout()
        header.addWidget(QLabel(f"Max refines (per equipment: {label})"))
        header.addWidget(self.max_refines)
        header.addStretch(1)
        layout.addLayout(header)
        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(6)
        layout.addLayout(self._rows_layout)
        self.add_button = QPushButton("+ Add line")
        self.add_button.clicked.connect(lambda _=False: self._add_row(notify=True))
        buttons = QHBoxLayout()
        buttons.addWidget(self.add_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    def _add_row(self, data: dict | None = None, notify: bool = False):
        if len(self.rows) >= MAX_LINES:      # trang bị chỉ có MAX_LINES dòng tinh luyện
            return
        row = _LineRow(self._catalog, self._on_change, self._remove_row)
        if data:
            row.set_value(data)
        self.rows.append(row)
        self._rows_layout.addWidget(row)
        self._refresh()
        if notify:
            self._on_change()

    def _remove_row(self, row: _LineRow):
        self.rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()
        self._refresh()
        self._on_change()

    def _refresh(self):
        self.add_button.setEnabled(len(self.rows) < MAX_LINES)

    def chosen(self) -> list[dict]:
        return [row.value() for row in self.rows]

    def value(self) -> dict:
        return {LINES_KEY: self.chosen(), MAX_REFINES_KEY: self.max_refines.currentData()}

    def set_value(self, data: dict):
        for row in list(self.rows):
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self.rows.clear()
        for line in (data.get(LINES_KEY) or [])[:MAX_LINES]:
            self._add_row(line)
        self._refresh()
        self.max_refines.setCurrentIndex(max(0, self.max_refines.findData(data.get(MAX_REFINES_KEY, DEFAULT_MAX_REFINES))))


class RefineEquipmentTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title="Refine Equipment", parent=parent)
        self.findChild(QScrollArea).setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)   # bảng giãn theo bề ngang, không cuộn ngang
        general = QGroupBox("General")
        row = QHBoxLayout(general)
        self.favorite = QCheckBox("Favorite generals")
        self.favorite.toggled.connect(lambda _=False: self.settings_changed.emit())
        self.general_type = QComboBox()
        self.general_type.setFixedWidth(GENERAL_TYPE_WIDTH)
        for type_id, label, _x in GENERAL_TYPES:
            self.general_type.addItem(label, type_id)
        self.general_type.currentIndexChanged.connect(lambda _=0: self.settings_changed.emit())
        row.addWidget(self.favorite)
        row.addWidget(QLabel("General type"))
        row.addWidget(self.general_type)
        row.addStretch(1)
        self.add_row(general)
        self.slots: dict[str, _SlotGroup] = {}
        for slot_id, label, _pos, catalog in SLOTS:
            self.slots[slot_id] = _SlotGroup(label, catalog, self.settings_changed.emit)
            self.add_row(self.slots[slot_id])

    def get_settings(self) -> dict:
        return {
            FAVORITE_KEY: self.favorite.isChecked(),
            GENERAL_TYPE_KEY: self.general_type.currentData(),
            SLOTS_KEY: {slot_id: group.value() for slot_id, group in self.slots.items() if group.chosen()},
        }

    def set_settings(self, data: dict):
        self.favorite.setChecked(bool(data.get(FAVORITE_KEY)))
        self.general_type.setCurrentIndex(max(0, self.general_type.findData(data.get(GENERAL_TYPE_KEY, DEFAULT_GENERAL_TYPE))))
        saved = data.get(SLOTS_KEY) or {}
        for slot_id, group in self.slots.items():
            group.set_value(saved.get(slot_id) or {})
