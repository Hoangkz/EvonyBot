"""
refine_equipment_tab.py — tab "Refine Equipment": group "General" (ô tích tướng yêu thích + loại tướng) và 6 group trang bị. Mỗi trang bị có 4 dòng tinh luyện,
mỗi dòng ra ngẫu nhiên một trong nhiều loại thuộc tính, nên group liệt kê MỌI thuộc tính của trang bị đó thành lưới ô có viền 2 cột để tích nhiều
thuộc tính cần: mỗi ô gồm ô tích, tên, màu tối thiểu (Orange / Gold) và ô "Lock" (khoá dòng lại khi đã ra đúng). Đầu group có hai ô cho RIÊNG trang bị đó:
"Max refines" (số lần Refine tối đa) và "Stop when" (khi nào dừng: số dòng vàng / cam trong 4 dòng New).

Settings (cột `refine_equipment` của DB):
{"favorite": false, "general_type": "all",
 "slots": {"weapon": {"lines": [{"attribute": "Ground Troop Attack", "color": "gold", "kind": "percent", "lock": true}], "max_refines": 100, "stop": {"gold": 1, "orange": 0}}, ...}}
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
    DEFAULT_MAX_REFINES,
    DEFAULT_KIND,
    DEFAULT_STOP,
    FAVORITE_KEY,
    GENERAL_TYPE_KEY,
    GENERAL_TYPES,
    KIND_KEY,
    KINDS,
    LINES_KEY,
    LOCK_KEY,
    MAX_REFINES_KEY,
    MAX_REFINES_OPTIONS,
    SLOTS,
    SLOTS_KEY,
    STOP_KEY,
    STOP_OPTIONS,
    stop_label,
)

from .tab_placeholder import BaseTab

COLUMNS = 2          # số cột thuộc tính trong một group trang bị
NAME_WIDTH = 92      # bề rộng tối thiểu của tên thuộc tính (ô rộng hơn thì tên giãn thêm, xuống dòng khi dài)
NAME_PADDING = 6     # chừa thêm cho dòng cuối (heightForWidth tính sát chữ)
NAME_HEIGHT = 36     # chiều cao tối thiểu của tên (2 dòng); tên dài hơn tự cao thêm
COLOR_WIDTH = 66
KIND_WIDTH = 60
MAX_REFINES_WIDTH = 80
STOP_WIDTH = 170           # đủ chữ dài nhất ("1 gold + 3 orange")
GENERAL_TYPE_WIDTH = 170   # đủ chữ dài nhất ("Hammer (Development)")
BORDER, BORDER_ON = "#c7ccd4", "#2563eb"     # viền ô: thường / đã tích
CELL_STYLE = "QFrame#RefineCell {{ border: 1px solid {color}; border-radius: 6px; }}"


class _LineRow:
    """Một thuộc tính = một ô có viền (xanh khi đã tích): ô tích, tên, màu tối thiểu, Lock. Màu và Lock chỉ chỉnh được khi đã tích."""

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
        self.kind = QComboBox()        # tăng % hay tăng chỉ số (hay cả hai) của dòng
        for kind_id, text in KINDS:
            self.kind.addItem(text, kind_id)
        self.kind.setCurrentIndex(max(0, self.kind.findData(DEFAULT_KIND)))
        self.kind.setFixedWidth(KIND_WIDTH)
        self.kind.setToolTip("All: cả tăng % lẫn tăng chỉ số | %: chỉ dòng tăng % (+3.9%) | Flat: chỉ dòng tăng chỉ số (+128)")
        self.lock = QCheckBox("Lock")
        self.lock.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)   # rộng đúng bằng ô tích + chữ "Lock" theo font thật, không cắt chữ
        self.lock.setToolTip("Khoá dòng này lại khi đã ra đúng thuộc tính và màu")
        for widget in (self.color, self.kind, self.lock):
            widget.setEnabled(False)
        row = QHBoxLayout(self.cell)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(4)
        self.cell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)   # ô giãn đều theo cột; cao theo tên
        row.addWidget(self.box)
        row.addWidget(label, 1)            # tên giãn hết phần dư của ô; màu / Lock luôn sát mép phải
        row.addWidget(self.color)
        row.addWidget(self.kind)
        row.addWidget(self.lock)
        self.box.toggled.connect(lambda on: on_toggle(self, on))
        self.color.currentIndexChanged.connect(lambda _=0: on_change())
        self.kind.currentIndexChanged.connect(lambda _=0: on_change())
        self.lock.toggled.connect(lambda _=False: on_change())

    def set_ticked(self, on: bool):
        self.color.setEnabled(on)
        self.kind.setEnabled(on)
        self.lock.setEnabled(on)
        self.cell.setStyleSheet(CELL_STYLE.format(color=BORDER_ON if on else BORDER))

    def value(self) -> dict:
        return {ATTRIBUTE_KEY: self.name, COLOR_KEY: self.color.currentData(), KIND_KEY: self.kind.currentData(), LOCK_KEY: self.lock.isChecked()}

    def set_value(self, data: dict | None):
        self.box.setChecked(data is not None)
        data = data or {}
        self.color.setCurrentIndex(max(0, self.color.findData(data.get(COLOR_KEY, DEFAULT_COLOR))))
        self.kind.setCurrentIndex(max(0, self.kind.findData(data.get(KIND_KEY, DEFAULT_KIND))))
        self.lock.setChecked(bool(data.get(LOCK_KEY)))


class _SlotGroup(QGroupBox):
    """Một trang bị: hàng đầu là ô Max refines + ô Stop when, dưới là bảng COLUMNS cột các thuộc tính (tích bao nhiêu cũng được)."""

    def __init__(self, label: str, catalog: tuple, on_change, parent=None):
        super().__init__(label, parent)
        self._on_change = on_change
        grid = QGridLayout(self)
        grid.setSpacing(6)
        # Số lần Refine tối đa của TRANG BỊ NÀY mỗi lượt (100 .. 1000 hoặc ALL = tới khi đạt); mỗi trang bị một ô riêng.
        self.max_refines = QComboBox()
        for option in MAX_REFINES_OPTIONS:
            self.max_refines.addItem(str(option), option)
        self.max_refines.setFixedWidth(MAX_REFINES_WIDTH)
        self.max_refines.setCurrentIndex(self.max_refines.findData(DEFAULT_MAX_REFINES))
        self.max_refines.currentIndexChanged.connect(lambda _=0: on_change())
        # Khi nào dừng (Confirm) của TRANG BỊ NÀY: số dòng vàng / cam tối thiểu trong 4 dòng New. Dữ liệu của mục là chỉ số trong STOP_OPTIONS
        # (Qt không tìm lại được dữ liệu dạng tuple bằng findData).
        self.stop = QComboBox()
        for index, (gold, orange) in enumerate(STOP_OPTIONS):
            self.stop.addItem(stop_label(gold, orange), index)
        self.stop.setFixedWidth(STOP_WIDTH)
        self.stop.setCurrentIndex(STOP_OPTIONS.index(DEFAULT_STOP))
        self.stop.currentIndexChanged.connect(lambda _=0: on_change())
        header = QHBoxLayout()      # Max refines và Stop when cùng một hàng
        header.addWidget(QLabel("Max refines (per equipment)"))
        header.addWidget(self.max_refines)
        header.addSpacing(16)
        header.addWidget(QLabel("Stop when (per equipment)"))
        header.addWidget(self.stop)
        header.addStretch(1)
        grid.addLayout(header, 0, 0, 1, COLUMNS)
        grid.setAlignment(Qt.AlignTop)
        for column in range(COLUMNS):
            grid.setColumnStretch(column, 1)       # 2 cột chia đều bề ngang
        self.rows: dict[str, _LineRow] = {}
        for i, name in enumerate(catalog):
            row = _LineRow(name, self._toggled, on_change)
            self.rows[name] = row
            grid.addWidget(row.cell, 1 + i // COLUMNS, i % COLUMNS)

    def _toggled(self, row: _LineRow, on: bool):
        row.set_ticked(on)
        self._on_change()

    def chosen(self) -> list[dict]:
        return [row.value() for row in self.rows.values() if row.box.isChecked()]

    def value(self) -> dict:
        gold, orange = STOP_OPTIONS[self.stop.currentData()]
        return {LINES_KEY: self.chosen(), MAX_REFINES_KEY: self.max_refines.currentData(), STOP_KEY: {"gold": gold, "orange": orange}}

    def set_value(self, data: dict):
        saved = {line.get(ATTRIBUTE_KEY): line for line in data.get(LINES_KEY) or []}
        for name, row in self.rows.items():
            row.set_value(saved.get(name))
        self.max_refines.setCurrentIndex(max(0, self.max_refines.findData(data.get(MAX_REFINES_KEY, DEFAULT_MAX_REFINES))))
        stop = data.get(STOP_KEY) or {}
        pair = (stop.get("gold"), stop.get("orange"))
        self.stop.setCurrentIndex(STOP_OPTIONS.index(pair) if pair in STOP_OPTIONS else STOP_OPTIONS.index(DEFAULT_STOP))


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
