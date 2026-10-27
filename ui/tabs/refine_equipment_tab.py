"""
refine_equipment_tab.py — tab "Refine Equipment": group "General" (ô tích tướng yêu thích + loại tướng) và 6 group trang bị; mỗi group
liệt kê các thuộc tính tinh luyện của trang bị đó, mỗi thuộc tính một hàng: ô tích (tối đa MAX_LINES = 4 dòng cần có), màu tối thiểu
(Orange / Gold) và ô "Lock" (khoá dòng lại khi đã ra đúng).

Settings (cột `refine_equipment` của DB):
{"favorite": false, "general_type": "all",
 "slots": {"weapon": {"lines": [{"attribute": "Ground Troop Attack", "color": "gold", "lock": true}]}, ...}}
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
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
    LINES_KEY,
    LOCK_KEY,
    MAX_LINES,
    SLOTS,
    SLOTS_KEY,
)

from .tab_placeholder import BaseTab

COLUMNS = 3          # số cột thuộc tính trong một group trang bị
NAME_WIDTH = 92      # bề rộng tối thiểu của tên thuộc tính (ô rộng hơn thì tên giãn thêm, xuống dòng khi dài)
NAME_PADDING = 6     # chừa thêm cho dòng cuối (heightForWidth tính sát chữ)
NAME_HEIGHT = 36     # chiều cao tối thiểu của tên (2 dòng); tên dài hơn tự cao thêm
COLOR_WIDTH = 66
GENERAL_TYPE_WIDTH = 170   # đủ chữ dài nhất ("Hammer (Development)")
BORDER, BORDER_ON = "#c7ccd4", "#2563eb"     # viền ô: thường / đã tích
CELL_STYLE = "QFrame#RefineCell {{ border: 1px solid {color}; border-radius: 6px; }}"


class _LineRow:
    """Một thuộc tính = một ô có viền (xanh khi đã tích): ô tích, tên (bề rộng cố định), màu tối thiểu, Lock. Màu và Lock chỉ chỉnh được khi đã tích."""

    def __init__(self, name: str, on_toggle, on_change):
        self.name = name
        self.cell = QFrame()
        self.cell.setObjectName("RefineCell")
        self.cell.setStyleSheet(CELL_STYLE.format(color=BORDER))
        self.box = QCheckBox()
        label = QLabel(name)              # bấm vào tên cũng tích / bỏ tích
        label.setWordWrap(True)
        label.setMinimumWidth(NAME_WIDTH)
        # Chiều cao tối thiểu = số dòng khi tên xuống dòng ở bề rộng hẹp nhất (NAME_WIDTH); ô rộng hơn chỉ ít dòng hơn nên không bị cắt, và không
        # phụ thuộc kích thước cửa sổ (đổi chiều cao theo bề rộng thật làm thanh cuộn dọc nhảy qua lại).
        label.setMinimumHeight(max(label.heightForWidth(NAME_WIDTH) + NAME_PADDING, NAME_HEIGHT))
        label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)   # tên chiếm hết phần dư của ô
        label.setToolTip(name)
        label.mousePressEvent = lambda event, b=self.box: b.click()
        self.color = QComboBox()
        for color_id, text in COLORS:
            self.color.addItem(text, color_id)
        self.color.setCurrentIndex(max(0, self.color.findData(DEFAULT_COLOR)))
        self.color.setFixedWidth(COLOR_WIDTH)
        self.lock = QCheckBox("Lock")
        self.lock.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)   # rộng đúng bằng ô tích + chữ "Lock" theo font thật, không cắt chữ
        self.lock.setToolTip("Khoá dòng này lại khi đã ra đúng thuộc tính và màu")
        for widget in (self.color, self.lock):
            widget.setEnabled(False)
        row = QHBoxLayout(self.cell)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(4)
        self.cell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)   # ô giãn đều theo cột; cao theo tên (Fixed làm ô cao theo sizeHint, cắt dòng cuối)
        row.addWidget(self.box)
        row.addWidget(label, 1)            # tên giãn hết phần dư của ô; màu / Lock luôn sát mép phải
        row.addWidget(self.color)
        row.addWidget(self.lock)
        self.box.toggled.connect(lambda on: on_toggle(self, on))
        self.color.currentIndexChanged.connect(lambda _=0: on_change())
        self.lock.toggled.connect(lambda _=False: on_change())

    def set_ticked(self, on: bool):
        self.color.setEnabled(on)
        self.lock.setEnabled(on)
        self.cell.setStyleSheet(CELL_STYLE.format(color=BORDER_ON if on else BORDER))

    def value(self) -> dict:
        return {ATTRIBUTE_KEY: self.name, COLOR_KEY: self.color.currentData(), LOCK_KEY: self.lock.isChecked()}

    def set_value(self, data: dict | None):
        self.box.setChecked(data is not None)
        data = data or {}
        self.color.setCurrentIndex(max(0, self.color.findData(data.get(COLOR_KEY, DEFAULT_COLOR))))
        self.lock.setChecked(bool(data.get(LOCK_KEY)))


class _SlotGroup(QGroupBox):
    """Một trang bị: bảng COLUMNS cột các thuộc tính, tối đa MAX_LINES dòng được tích."""

    def __init__(self, label: str, catalog: tuple, on_change, parent=None):
        super().__init__(label, parent)
        self._on_change = on_change
        grid = QGridLayout(self)
        grid.setSpacing(6)
        grid.setAlignment(Qt.AlignTop)
        for column in range(COLUMNS):
            grid.setColumnStretch(column, 1)       # 3 cột chia đều bề ngang
        self.rows: dict[str, _LineRow] = {}
        for i, name in enumerate(catalog):
            row = _LineRow(name, self._toggled, on_change)
            self.rows[name] = row
            grid.addWidget(row.cell, i // COLUMNS, i % COLUMNS)

    def _toggled(self, row: _LineRow, on: bool):
        if on and len(self.chosen()) > MAX_LINES:   # mỗi trang bị chỉ có MAX_LINES dòng tinh luyện
            row.box.setChecked(False)
            return
        row.set_ticked(on)
        self._on_change()

    def chosen(self) -> list[_LineRow]:
        return [row for row in self.rows.values() if row.box.isChecked()]

    def value(self) -> dict:
        return {LINES_KEY: [row.value() for row in self.chosen()]}

    def set_value(self, data: dict):
        saved = {line.get(ATTRIBUTE_KEY): line for line in (data.get(LINES_KEY) or [])[:MAX_LINES]}
        for name, row in self.rows.items():
            row.set_value(saved.get(name))


class RefineEquipmentTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title="Refine Equipment", parent=parent)
        self.findChild(QScrollArea).setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)   # 3 cột vừa chiều ngang, không cuộn ngang
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
