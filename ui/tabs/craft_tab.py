"""
craft_tab.py — tab "Craft": mỗi nhóm trang bị (bot/activities/craft/constants.py) một group, mỗi trang bị một ô tích kèm icon và số lượng
cần chế tạo (mặc định 1, chỉ nhập được khi đã tích).

Settings (cột `craft` của DB): {"items": {"ring/05": 1, "helmet/03": 2}} — chỉ các trang bị đã tích, giá trị là số lượng.
"""
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QCheckBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from bot.activities.craft.constants import DEFAULT_QTY, ITEMS_KEY, MAX_QTY, catalog
from bot.context.templates import TEMPLATE_DIR

from .tab_placeholder import BaseTab

COLUMNS = 4      # số trang bị mỗi hàng trong một group
ICON_SIZE = 28   # icon thu nhỏ từ 44x43
BORDER, BORDER_ON = "#c7ccd4", "#2563eb"     # viền ô trang bị: thường / đã tích
CELL_STYLE = "QFrame#CraftCell {{ border: 1px solid {color}; border-radius: 6px; }}"
NAME_WIDTH = 100  # bề rộng cố định của tên trang bị (xuống dòng khi dài)
NAME_HEIGHT = 48  # cao đủ 3 dòng để các ô cùng hàng thẳng nhau


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
        for key, title, items in catalog():
            self.add_row(self._group(title, items))

    def _group(self, title: str, items) -> QGroupBox:
        group = QGroupBox(title)
        outer = QVBoxLayout(group)
        grid = QGridLayout()
        outer.addLayout(grid)
        for i, (item_id, path, name) in enumerate(items):
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
            grid.addWidget(cell, i // COLUMNS, i % COLUMNS)
            self.boxes[item_id] = (box, spin)
        return group

    def get_settings(self) -> dict:
        return {ITEMS_KEY: {item_id: spin.value() for item_id, (box, spin) in self.boxes.items() if box.isChecked()}}

    def set_settings(self, data: dict):
        chosen = data.get(ITEMS_KEY) or {}
        for item_id, (box, spin) in self.boxes.items():
            box.setChecked(item_id in chosen)
            try:
                spin.setValue(max(1, min(MAX_QTY, int(chosen.get(item_id, DEFAULT_QTY)))))
            except (TypeError, ValueError):
                spin.setValue(DEFAULT_QTY)
