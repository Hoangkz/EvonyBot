"""
recruit_general_tab.py — tab "Recruit General" (activity bot/activities/recruit_general/).

- Group "Setting": ô tích "Open Gold", hai ô chọn số lần Refresh / số lần mua (ALL = không giới hạn) + nhóm hai nút radio "Recruit General" / "Buy General Token" (hai nút ở màn chi tiết
  tướng), chỉ một nút được tích (mặc định Recruit General).

- Group "Generals": danh sách tướng (ui/tabs/generals.py), ô search theo tên + lọc theo civ và type, tích chọn tướng.
  Tướng đã tích vẫn giữ khi đổi search / civ; mặc định tích sẵn các tướng có `default` (generals.py).

Settings (cột `recruit_general` của DB): {"buy_with": "Recruit General" | "Buy General Token", "generals": [tên, ...], "open_gold": bool,
"refresh_count": "ALL" | 100..1000,
"general_counts": {tên tướng: 1 | 2 | 3 | 10 | 15 | 20 | "ALL"}} (số lượng cần mua của từng tướng đã tích, mặc định 1)
"""
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from .constants import (
    GENERAL_COLUMNS,
    GENERAL_COUNT_WIDTH,
    GENERAL_NAME_WIDTH,
    RECRUIT_GENERAL_COUNT_DEFAULT,
    RECRUIT_GENERAL_COUNT_OPTIONS,
    RECRUIT_GENERAL_COUNTS_KEY,
    RECRUIT_CIV_ALL,
    RECRUIT_PICKER_HEIGHT,
    RECRUIT_SELECTED_COLUMNS,
    RECRUIT_SELECTED_GROUP,
    RECRUIT_SELECTED_ROWS,
    RECRUIT_SELECTED_SPACING,
    RECRUIT_SELECTED_NAME_WIDTH,
    RECRUIT_DESELECT_ALL_TEXT,
    RECRUIT_OPEN_GOLD_KEY,
    RECRUIT_OPEN_GOLD_TEXT,
    RECRUIT_GENERALS_GROUP,
    RECRUIT_GENERALS_KEY,
    RECRUIT_REFRESH_DEFAULT,
    RECRUIT_REFRESH_KEY,
    RECRUIT_REFRESH_OPTIONS,
    RECRUIT_REFRESH_TEXT,
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


GROUP_TIGHT = "QGroupBox#{name} {{ padding: 6px 6px 6px 6px; }}"   # thay padding 14px 10px 10px của theme cho group có tên


class GeneralPicker(QGroupBox):
    """Lưới ô tích tướng (theo hàng, cột) có ô search theo tên và ô lọc civ."""

    changed = pyqtSignal()

    def __init__(self, title, generals, columns=GENERAL_COLUMNS, parent=None):
        super().__init__(title, parent)
        self._columns = columns
        self.setObjectName("RecruitGenerals")
        self.setStyleSheet(GROUP_TIGHT.format(name="RecruitGenerals"))   # theme có padding 14px 10px 10px: thu nhỏ
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
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
        self._cells = {}    # ô tích + ô số lượng của từng tướng (xếp vào lưới)
        self._counts = {}   # ô chọn số lượng cần mua của từng tướng
        self._civs = {}
        self._types = {}
        self._defaults = {}
        holder = QWidget()
        self._grid = QGridLayout(holder)
        self._grid.setAlignment(Qt.AlignTop)
        self._grid.setHorizontalSpacing(6)
        for column in range(columns):
            self._grid.setColumnStretch(column, 1)   # các cột chia đều bề ngang, cột cuối không bị hở bên phải
        for g in generals:
            box = QCheckBox()   # tên hiện ở nhãn bên cạnh (xuống dòng khi dài)
            box.setChecked(bool(g.get("default")))
            self._defaults[g["name"]] = bool(g.get("default"))
            box.toggled.connect(lambda _checked: self.changed.emit())
            count = QComboBox()
            for option in RECRUIT_GENERAL_COUNT_OPTIONS:
                count.addItem(str(option), option)
            count.setCurrentIndex(RECRUIT_GENERAL_COUNT_OPTIONS.index(RECRUIT_GENERAL_COUNT_DEFAULT))
            count.currentIndexChanged.connect(lambda _index: self.changed.emit())
            count.setFixedWidth(GENERAL_COUNT_WIDTH)
            count.setEnabled(box.isChecked())   # chỉ chọn được số lượng khi tướng đã tích
            box.toggled.connect(count.setEnabled)
            cell = QWidget()   # một hàng: ô số lượng nhỏ đứng ngay cạnh tên tướng
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(2)
            label = QLabel(g["name"])
            label.setWordWrap(True)
            label.setMinimumWidth(GENERAL_NAME_WIDTH)   # tối thiểu cố định, dài quá thì xuống dòng; thừa chỗ thì tên giãn ra cho cột lấp kín
            label.setToolTip(g["name"])
            label.mousePressEvent = lambda _event, box=box: box.toggle()   # bấm vào tên cũng tích
            cell_layout.addWidget(box)
            cell_layout.addWidget(label, 1)
            cell_layout.addWidget(count)
            self._boxes[g["name"]] = box
            self._counts[g["name"]] = count
            self._cells[g["name"]] = cell
            self._civs[g["name"]] = g["civ"]
            self._types[g["name"]] = g.get("type1", "")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)   # 4 cột vừa chiều ngang, không cuộn ngang
        scroll.setWidget(holder)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                             "QScrollArea > QWidget > QWidget { background: transparent; }")   # nền trắng của group, không xám của theme
        scroll.setMinimumHeight(RECRUIT_PICKER_HEIGHT)
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
        for cell in self._cells.values():
            self._grid.removeWidget(cell)
            cell.hide()
        shown = [name for name, box in self._boxes.items()
                 if text in name.lower() and (civ == RECRUIT_CIV_ALL or self._civs[name] == civ)
                 and (type1 == RECRUIT_TYPE_ALL or self._types[name] == type1)]
        self._shown = shown
        for i, name in enumerate(shown):
            self._grid.addWidget(self._cells[name], i // self._columns, i % self._columns)
            self._cells[name].show()

    def _set_shown(self, checked):
        """Tích / bỏ tích tất cả tướng đang hiện (đã qua search, civ, type); tướng bị lọc ẩn không đổi."""
        for name in self._shown:
            self._boxes[name].setChecked(checked)

    def _reset(self):
        """Về mặc định: chỉ tích các tướng `default` (toàn danh sách, không phụ thuộc bộ lọc đang chọn)."""
        for name, box in self._boxes.items():
            box.setChecked(self._defaults[name])
            self._counts[name].setCurrentIndex(RECRUIT_GENERAL_COUNT_OPTIONS.index(RECRUIT_GENERAL_COUNT_DEFAULT))

    def checked(self):
        return [name for name, box in self._boxes.items() if box.isChecked()]

    def counts(self) -> dict:
        """Số lượng cần mua của các tướng đang tích: {tên: 1|2|3|10|15|20|"ALL"}."""
        return {name: self._counts[name].currentData() for name, box in self._boxes.items() if box.isChecked()}

    def set_counts(self, counts: dict):
        """Đặt số lượng từng tướng; thiếu / không hợp lệ (settings cũ) thì về mặc định."""
        for name, combo in self._counts.items():
            value = counts.get(name)
            combo.blockSignals(True)
            combo.setCurrentIndex(RECRUIT_GENERAL_COUNT_OPTIONS.index(
                value if value in RECRUIT_GENERAL_COUNT_OPTIONS else RECRUIT_GENERAL_COUNT_DEFAULT))
            combo.blockSignals(False)

    def set_checked(self, names):
        names = set(names)
        for name, box in self._boxes.items():
            box.blockSignals(True)
            box.setChecked(name in names)
            box.blockSignals(False)
            self._counts[name].setEnabled(box.isChecked())


class TightGroupBox(QGroupBox):
    """QGroupBox mà nội dung (một widget con) lấp kín toàn bộ phần trong khung, sát mép: không dùng layout vì Qt tự chừa chỗ cho tiêu đề
    trong layout (~23px) nên bị hở phía trên. Chiều cao tối thiểu = chiều cao tối thiểu của widget con + khung."""

    FRAME_TOP = 15    # margin-top 14px của theme + viền 1px (tiêu đề nằm đè lên đây)
    FRAME_SIDE = 1
    MARGIN = 4        # chừa sát viền 2px mọi phía

    def __init__(self, title, content: QWidget, parent=None):
        super().__init__(title, parent)
        self._content = content
        content.setParent(self)
        self.setMinimumHeight(self.FRAME_TOP + content.minimumHeight() + self.FRAME_SIDE + 2 * self.MARGIN)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        side, margin = self.FRAME_SIDE + self.MARGIN, self.MARGIN
        self._content.setGeometry(self.rect().adjusted(side, self.FRAME_TOP + margin, -side, -(self.FRAME_SIDE + margin)))


class SelectedGenerals(QWidget):
    """Danh sách các tướng đã tích, mỗi tướng một nhãn "tên xN". Tự vẽ lại khi picker đổi."""

    def __init__(self, picker: GeneralPicker, parent=None):
        super().__init__(parent)
        self._picker = picker
        self._timer = QTimer(self)   # gộp nhiều thay đổi liên tiếp (Select All, Reset...) thành một lần vẽ lại
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.refresh)
        self._grid = QGridLayout(self)   # RECRUIT_SELECTED_COLUMNS cột, điền từng hàng từ trái sang phải; nằm trong QScrollArea của tab
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setAlignment(Qt.AlignTop)
        self._grid.setVerticalSpacing(RECRUIT_SELECTED_SPACING)
        for column in range(RECRUIT_SELECTED_COLUMNS):
            self._grid.setColumnStretch(column, 1)   # các cột chia đều bề ngang, cột cuối không bị hở bên phải
        picker.changed.connect(self.schedule)
        self.refresh()

    def schedule(self):
        self._timer.start(0)

    def refresh(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        counts = self._picker.counts()
        for i, name in enumerate(self._picker.checked()):
            text = QLabel(f"{name}  x{counts.get(name, RECRUIT_GENERAL_COUNT_DEFAULT)}")
            text.setWordWrap(True)
            text.setMinimumWidth(RECRUIT_SELECTED_NAME_WIDTH)   # rộng tối thiểu cố định, dài quá thì xuống dòng; thừa chỗ thì giãn cho cột lấp kín
            self._grid.addWidget(text, i // RECRUIT_SELECTED_COLUMNS, i % RECRUIT_SELECTED_COLUMNS)


class RecruitGeneralTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title=RECRUIT_TAB_TITLE, show_apply_all=True, parent=parent)
        # Group "Setting": ô tích "Open Gold" + ô số lần Refresh cùng hàng ở trên, dưới là nhóm hai nút radio (mỗi nhóm radio loại trừ riêng).
        self.open_gold = QCheckBox(RECRUIT_OPEN_GOLD_TEXT)
        self.open_gold.toggled.connect(lambda _checked: self.settings_changed.emit())
        self.setting = RadioGroup("", list(RECRUIT_BUY_OPTIONS), default=RECRUIT_BUY_DEFAULT,
                                  columns=len(RECRUIT_BUY_OPTIONS))
        self.setting.setFlat(True)
        self.setting.valueChanged.connect(lambda _value: self.settings_changed.emit())
        setting_box = QGroupBox(RECRUIT_SETTING_GROUP)
        setting_box.setObjectName("RecruitSetting")
        setting_box.setStyleSheet(GROUP_TIGHT.format(name="RecruitSetting"))
        self.setting.setStyleSheet("QGroupBox { padding: 4px 6px; margin-top: 0px; }")   # nhóm radio: bớt khoảng đệm / margin tiêu đề (không có tiêu đề)
        box_layout = QHBoxLayout(setting_box)   # trái: các setting, phải: danh sách tướng đã chọn
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(8)
        left = QVBoxLayout()
        left.setSpacing(4)
        self.refresh_count = self._count_combo(RECRUIT_REFRESH_OPTIONS, RECRUIT_REFRESH_DEFAULT)
        top = QHBoxLayout()   # "Open Gold" và ô số lần Refresh cùng một hàng
        top.addWidget(self.open_gold)
        top.addSpacing(16)
        top.addWidget(QLabel(RECRUIT_REFRESH_TEXT))
        top.addWidget(self.refresh_count)
        top.addStretch(1)
        left.addLayout(top)
        left.addWidget(self.setting, 0, Qt.AlignLeft)   # chỉ rộng vừa hai nút, căn trái
        left.addStretch(1)
        box_layout.addLayout(left)
        self.generals = GeneralPicker(RECRUIT_GENERALS_GROUP, GENERALS)
        self.generals.changed.connect(self.settings_changed.emit)
        self.selected = SelectedGenerals(self.generals)
        scroll = QScrollArea()   # cao cố định, cuộn dọc; nền trong suốt (không bị xám / nâu của theme)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        row_height = QLabel("X").sizeHint().height()   # chiều cao thật của một nhãn một dòng
        scroll.setMinimumHeight(RECRUIT_SELECTED_ROWS * row_height + (RECRUIT_SELECTED_ROWS - 1) * RECRUIT_SELECTED_SPACING)   # tối thiểu vừa số hàng; group cao thêm thì danh sách giãn theo
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                             "QScrollArea > QWidget > QWidget { background: transparent; }")
        scroll.setWidget(self.selected)
        selected_box = TightGroupBox(RECRUIT_SELECTED_GROUP, scroll)   # group bao danh sách tướng đã chọn
        box_layout.addWidget(selected_box, 1)
        self.add_row(setting_box)
        self.add_row(self.generals)

    def _count_combo(self, options, default) -> QComboBox:
        """Ô chọn số lần ("ALL" hoặc một số); phát settings_changed khi đổi."""
        combo = QComboBox()
        for option in options:
            combo.addItem(str(option), option)
        combo.setCurrentIndex(options.index(default))
        combo.currentIndexChanged.connect(lambda _index: self.settings_changed.emit())
        return combo

    @staticmethod
    def _set_count(combo: QComboBox, value, options, default):
        """Chọn `value` trong ô; không hợp lệ (settings cũ / hỏng) thì về `default`."""
        combo.blockSignals(True)
        combo.setCurrentIndex(options.index(value) if value in options else options.index(default))
        combo.blockSignals(False)

    def get_settings(self) -> dict:
        return {RECRUIT_OPEN_GOLD_KEY: self.open_gold.isChecked(),
                RECRUIT_BUY_KEY: self.setting.value() or RECRUIT_BUY_DEFAULT,
                RECRUIT_REFRESH_KEY: self.refresh_count.currentData(),
                RECRUIT_GENERALS_KEY: self.generals.checked(),
                RECRUIT_GENERAL_COUNTS_KEY: self.generals.counts()}

    def set_settings(self, data: dict):
        self.open_gold.setChecked(bool(data.get(RECRUIT_OPEN_GOLD_KEY, False)))
        value = data.get(RECRUIT_BUY_KEY)
        if value in RECRUIT_BUY_OPTIONS:
            self.setting.set_value(value)
        self._set_count(self.refresh_count, data.get(RECRUIT_REFRESH_KEY), RECRUIT_REFRESH_OPTIONS, RECRUIT_REFRESH_DEFAULT)
        names = data.get(RECRUIT_GENERALS_KEY)
        if isinstance(names, list):
            self.generals.set_checked(names)
        counts = data.get(RECRUIT_GENERAL_COUNTS_KEY)
        self.generals.set_counts(counts if isinstance(counts, dict) else {})
        self.selected.refresh()   # set_checked / set_counts chặn tín hiệu nên tự vẽ lại
