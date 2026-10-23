"""
craft_tab.py — tab "Craft": group "Equipment" (như group chọn tướng của Recruit General) gom mọi trang bị (bot/activities/craft/constants.py) trong
một lưới cuộn có ô search theo tên và ô lọc theo loại; mỗi trang bị một ô tích kèm icon và số lượng cần chế tạo (mặc định 1, chỉ nhập được khi
đã tích).

Group "Overview" ở đầu tab (bố cục như group Setting của Recruit General): trái là ô tích "Claim event gifts", phải là các hộp quà đổi xếp 4 cột theo độ ưu tiên
("1. Resource", "2. Stamina"...), mỗi hộp có nút lên / xuống để đổi thứ tự.

Settings (cột `craft` của DB): {"items": {"ring/05": 1, "helmet/03": 2}, "claim_event_gifts": false, "gift_order": ["resource", "stamina"]}
— "items" chỉ có các trang bị đã tích, giá trị là số lượng.
"""
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)

from bot.activities.craft.constants import (
    CLAIM_KEY, DEFAULT_QTY, GIFT_ORDER_KEY, GIFTS, ITEMS_KEY, MAX_QTY, SET_BASIC, SETS, catalog, item_set,
)
from bot.context.templates import TEMPLATE_DIR

from .recruit_general_tab import GROUP_TIGHT
from .tab_placeholder import BaseTab

COLUMNS = 4      # số trang bị mỗi hàng trong một group
ICON_SIZE = 28   # icon thu nhỏ từ 44x43
BORDER, BORDER_ON = "#c7ccd4", "#2563eb"     # viền ô trang bị: thường / đã tích
CELL_STYLE = "QFrame#CraftCell {{ border: 1px solid {color}; border-radius: 6px; }}"
NAME_WIDTH = 90  # bề rộng cố định của tên trang bị (xuống dòng khi dài)
NAME_HEIGHT = 48  # cao đủ 3 dòng để các ô cùng hàng thẳng nhau
PICKER_HEIGHT = 200   # chiều cao tối thiểu (px) lưới chọn trang bị; nhiều hơn thì cuộn dọc
TYPE_ALL = "All"       # mục "không lọc" của ô chọn loại / bộ
SEARCH_PLACEHOLDER = "Search equipment name..."


def _icon(path: str) -> QIcon:
    pixmap = QPixmap()
    try:
        pixmap.loadFromData((TEMPLATE_DIR / path).read_bytes())
    except OSError:
        pass
    return QIcon(pixmap)


class CraftTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title="Craft", parent=parent)
        self.boxes: dict[str, tuple[QCheckBox, QSpinBox]] = {}     # id trang bị -> (ô tích, số lượng)
        self._cells: dict[str, QFrame] = {}                        # id trang bị -> ô (xếp vào lưới theo bộ lọc)
        self._names: dict[str, str] = {}                           # id trang bị -> tên
        self._types: dict[str, str] = {}                           # id trang bị -> loại (tiêu đề nhóm: Ring, Bow...)
        self._sets: dict[str, str] = {}                            # id trang bị -> bộ (King, Dragon, Achaemenidae, Officer, Consul, Basic)
        self.add_row(self._overview())
        self.add_row(self._picker())

    def _overview(self) -> QGroupBox:
        """Group Overview (bố cục như group Setting của Recruit General): trái là ô nhận quà event, phải là các hộp quà xếp 4 cột theo độ ưu
        tiên ("1. Resource", "2. Stamina", ...), mỗi hộp có nút lên / xuống để đổi thứ tự."""
        group = QGroupBox("Overview")
        group.setObjectName("CraftOverview")
        group.setStyleSheet(GROUP_TIGHT.format(name="CraftOverview"))
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 10, 0, 0)     # chừa chỗ cho tiêu đề group (không có TightGroupBox bao nội dung)
        layout.setSpacing(8)
        self.claim_gifts = QCheckBox("Claim event gifts")
        self.claim_gifts.toggled.connect(lambda _checked: self.settings_changed.emit())
        layout.addWidget(self.claim_gifts, 0, Qt.AlignmentFlag.AlignTop)

        self._gift_order = [gift_id for gift_id, _ in GIFTS]       # thứ tự ưu tiên hiện tại (trên xuống dưới)
        self._gift_cells: dict[str, tuple[QFrame, QLabel]] = {}
        holder = QWidget()
        self._gift_grid = QGridLayout(holder)
        self._gift_grid.setContentsMargins(0, 0, 0, 0)
        self._gift_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for column in range(COLUMNS):
            self._gift_grid.setColumnStretch(column, 1)
        for gift_id, label in GIFTS:
            self._gift_cells[gift_id] = self._gift_cell(gift_id, label)
        layout.addWidget(holder, 1)
        self._render_gifts()
        return group

    def _gift_cell(self, gift_id: str, label: str) -> tuple[QFrame, QLabel]:
        """Hộp một quà: viền, nhãn "số. tên", nút ▲ ▼."""
        cell = QFrame()
        cell.setObjectName("CraftCell")
        cell.setStyleSheet(CELL_STYLE.format(color=BORDER))
        row = QHBoxLayout(cell)
        row.setContentsMargins(6, 4, 6, 4)
        text = QLabel(label)
        row.addWidget(text, 1)
        for symbol, step in (("▲", -1), ("▼", 1)):
            button = QPushButton(symbol)
            button.setFixedSize(26, 26)
            button.setToolTip("Up" if step < 0 else "Down")
            button.clicked.connect(lambda _=False, g=gift_id, d=step: self._move_gift(g, d))
            row.addWidget(button)
        return cell, text

    def _render_gifts(self):
        """Xếp lại các hộp quà theo _gift_order (4 cột, trái sang phải, trên xuống dưới) và đánh số lại."""
        labels = dict(GIFTS)
        for cell, _ in self._gift_cells.values():
            self._gift_grid.removeWidget(cell)
        for i, gift_id in enumerate(self._gift_order):
            cell, text = self._gift_cells[gift_id]
            text.setText(f"{i + 1}. {labels[gift_id]}")
            self._gift_grid.addWidget(cell, i // COLUMNS, i % COLUMNS)

    def _move_gift(self, gift_id: str, step: int):
        index = self._gift_order.index(gift_id)
        target = index + step
        if not 0 <= target < len(self._gift_order):
            return
        self._gift_order.insert(target, self._gift_order.pop(index))
        self._render_gifts()
        self.settings_changed.emit()

    def _picker(self) -> QGroupBox:
        """Group Equipment: ô search + ô lọc loại + ô lọc bộ (King, Dragon...) ở trên, lưới 4 cột (cuộn dọc) các trang bị ở dưới."""
        group = QGroupBox("Equipment")
        group.setObjectName("CraftEquipment")
        group.setStyleSheet(GROUP_TIGHT.format(name="CraftEquipment"))
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.search = QLineEdit()
        self.search.setPlaceholderText(SEARCH_PLACEHOLDER)
        self.search.setClearButtonEnabled(True)
        self.type = QComboBox()
        self.type.addItem(TYPE_ALL, TYPE_ALL)
        self.set = QComboBox()      # lọc theo bộ trang bị (King, Dragon, ...)
        self.set.addItem(TYPE_ALL, TYPE_ALL)
        for label in [SET_BASIC] + [label for label, _ in SETS]:
            self.set.addItem(label, label)
        top = QHBoxLayout()
        top.addWidget(self.search, 1)
        top.addWidget(self.type)
        top.addWidget(self.set)
        layout.addLayout(top)

        holder = QWidget()
        self._grid = QGridLayout(holder)
        self._grid.setAlignment(Qt.AlignTop)
        for column in range(COLUMNS):
            self._grid.setColumnStretch(column, 1)
        for key, title, items in catalog():
            self.type.addItem(title, title)
            for item_id, path, name in items:
                self._cells[item_id] = self._cell(item_id, path, name)
                self._names[item_id] = name
                self._types[item_id] = title
                self._sets[item_id] = item_set(name)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(holder)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                             "QScrollArea > QWidget > QWidget { background: transparent; }")
        scroll.setMinimumHeight(PICKER_HEIGHT)
        layout.addWidget(scroll)
        self.search.textChanged.connect(self._filter)
        self.type.currentTextChanged.connect(self._filter)
        self.set.currentTextChanged.connect(self._filter)
        self._filter()
        return group

    def _cell(self, item_id: str, path: str, name: str) -> QFrame:
        """Một trang bị: viền (xanh khi đã tích), ô tích kèm icon, tên nhiều dòng, số lượng."""
        cell = QFrame()
        cell.setObjectName("CraftCell")
        cell.setStyleSheet(CELL_STYLE.format(color=BORDER))
        row = QHBoxLayout(cell)
        row.setContentsMargins(6, 4, 6, 4)
        box = QCheckBox()
        box.setIcon(_icon(path))
        box.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        box.setToolTip(name)
        label = QLabel(name)             # tên nhiều dòng, bề rộng cố định; bấm vào tên cũng tích / bỏ tích
        label.setWordWrap(True)
        label.setFixedSize(NAME_WIDTH, NAME_HEIGHT)
        label.setToolTip(name)
        label.mousePressEvent = lambda event, b=box: b.click()
        spin = QSpinBox()
        spin.setRange(1, MAX_QTY)
        spin.setValue(DEFAULT_QTY)
        spin.setFixedWidth(52)
        spin.setEnabled(False)
        box.toggled.connect(spin.setEnabled)
        box.toggled.connect(lambda on, c=cell: c.setStyleSheet(CELL_STYLE.format(color=BORDER_ON if on else BORDER)))
        row.addWidget(box)
        row.addWidget(label)
        row.addWidget(spin)
        self.boxes[item_id] = (box, spin)
        return cell

    def _filter(self, *_):
        """Hiện các trang bị khớp ô search (theo tên), ô loại và ô bộ; xếp lại lưới từ trên xuống, trái sang phải."""
        text = self.search.text().strip().lower()
        kind = self.type.currentData()
        bundle = self.set.currentData()
        for cell in self._cells.values():
            self._grid.removeWidget(cell)
            cell.hide()
        shown = [item_id for item_id in self._cells
                 if text in self._names[item_id].lower() and (kind == TYPE_ALL or self._types[item_id] == kind)
                 and (bundle == TYPE_ALL or self._sets[item_id] == bundle)]
        for i, item_id in enumerate(shown):
            self._grid.addWidget(self._cells[item_id], i // COLUMNS, i % COLUMNS)
            self._cells[item_id].show()

    def craft_done(self, item_id: str):
        """Bot vừa chế tạo xong một cái: số lượng giảm 1; về 0 thì bỏ tích (không lưu: người gọi lưu DB)."""
        if item_id not in self.boxes:
            return
        box, spin = self.boxes[item_id]
        if box.isChecked() and spin.value() > 1:
            spin.setValue(spin.value() - 1)
        else:
            box.setChecked(False)
            spin.setValue(DEFAULT_QTY)

    def get_settings(self) -> dict:
        return {ITEMS_KEY: {item_id: spin.value() for item_id, (box, spin) in self.boxes.items() if box.isChecked()},
                CLAIM_KEY: self.claim_gifts.isChecked(),
                GIFT_ORDER_KEY: list(self._gift_order)}

    def set_settings(self, data: dict):
        self.claim_gifts.setChecked(bool(data.get(CLAIM_KEY)))
        labels = dict(GIFTS)
        wanted = [g for g in data.get(GIFT_ORDER_KEY) or [] if g in labels]
        self._gift_order = wanted + [gift_id for gift_id, _ in GIFTS if gift_id not in wanted]      # quà mới (chưa lưu) xuống cuối
        self._render_gifts()
        chosen = data.get(ITEMS_KEY) or {}
        for item_id, (box, spin) in self.boxes.items():
            box.setChecked(item_id in chosen)
            try:
                spin.setValue(max(1, min(MAX_QTY, int(chosen.get(item_id, DEFAULT_QTY)))))
            except (TypeError, ValueError):
                spin.setValue(DEFAULT_QTY)
