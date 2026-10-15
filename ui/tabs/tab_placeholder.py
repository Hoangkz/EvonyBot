"""
tab_placeholder.py

- BaseTab: common scaffolding every settings tab is built on
  (scroll area, "Apply ALL" button, get_settings()/set_settings()).
- Small reusable helpers (LabeledCombo, CheckGroup, RadioGroup) that
  turn the repetitive C# designer blocks (rows of CheckBoxes /
  RadioButtons inside a Panel inside a GroupBox) into a couple of
  data-driven lines each.
- PlaceholderTab: a plain BaseTab with a "coming soon" message, used
  for any tab that hasn't been fleshed out yet.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QMessageBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import _designer


class DesignerTab(QWidget):
    """
    Base class for tabs that are rebuilt 1:1 from the original C#
    designer layout (Form3_Designer.cs): same control tree, same
    parent/child nesting, same pixel X/Y/W/H, same text — via
    `_designer.build_tab()`. The page keeps its original fixed size
    and sits inside a QScrollArea so it still works in a smaller window.

    Subclasses pass their own DESIGNER_DATA / COMBO_ITEMS / PAGE_SIZE
    (parsed straight out of the .cs file) and then use
    `self.controls["originalControlName"]` to wire up behaviour.

    The tab's "Apply ALL" button (any control whose name contains
    "ApplyAll") emits `apply_all_clicked`; DeviceView turns that into a
    request to copy this device's config to every other device.
    """

    apply_all_clicked = pyqtSignal()

    def __init__(self, root_name, designer_data, combo_items, page_size, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.page, self.controls = _designer.build_tab(
            root_name, designer_data, combo_items, page_size
        )
        scroll.setWidget(self.page)
        outer.addWidget(scroll)

        for name, widget in self.controls.items():
            if "applyall" in name.lower():
                # Cùng màu / cỡ với nút Apply ALL của BaseTab (Daily Activities): theme ApplyAllButton, cỡ tự nhiên, giữ mép phải.
                widget.setObjectName("ApplyAllButton")
                widget.style().unpolish(widget)       # nút đã polish lúc show() chưa có tên: áp lại theme để đo đúng cỡ chữ đậm
                widget.style().polish(widget)
                right, top = widget.x() + widget.width(), widget.y()
                hint = widget.sizeHint()
                widget.setGeometry(right - hint.width(), top, hint.width(), hint.height())
                widget.clicked.connect(self.apply_all_clicked.emit)

    def get_settings(self) -> dict:
        return {}

    def set_settings(self, data: dict):
        pass


def confirm_reset(parent, title: str, text: str) -> bool:
    """Hộp hỏi lại trước khi reset (tránh bấm nhầm); mặc định chọn No."""
    return QMessageBox.question(parent, title, text, QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) == QMessageBox.Yes


class LabeledCombo(QWidget):
    """A "Label: [combo box]" row, mirrors label+comboBox pairs in the C# form."""

    currentTextChanged = pyqtSignal(str)

    def __init__(self, label_text, items=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(label_text))
        self.combo = QComboBox()
        if items:
            self.combo.addItems([str(i) for i in items])
        self.combo.currentTextChanged.connect(self.currentTextChanged.emit)
        layout.addWidget(self.combo)
        layout.addStretch(1)

    def value(self):
        return self.combo.currentText()

    def set_value(self, text):
        index = self.combo.findText(str(text))
        if index >= 0:
            self.combo.setCurrentIndex(index)


class CheckGroup(QGroupBox):
    """A GroupBox full of CheckBoxes laid out in a grid (N columns)."""

    def __init__(self, title, options, columns=2, parent=None):
        super().__init__(title, parent)
        grid = QGridLayout(self)
        self.checkboxes = {}
        for i, name in enumerate(options):
            box = QCheckBox(name)
            self.checkboxes[name] = box
            grid.addWidget(box, i // columns, i % columns)

    def checked(self):
        return [name for name, box in self.checkboxes.items() if box.isChecked()]

    def set_all(self, checked=True):
        for box in self.checkboxes.values():
            box.setChecked(checked)

    def set_checked(self, names):
        names = set(names)
        for name, box in self.checkboxes.items():
            box.setChecked(name in names)


class RadioGroup(QGroupBox):
    """A GroupBox of mutually-exclusive RadioButtons (mirrors the C#
    Panel-of-RadioButtons pattern, e.g. Speed Marching 1s/5s/10s/.../No)."""

    valueChanged = pyqtSignal(str)

    def __init__(self, title, options, default=None, columns=3, parent=None):
        super().__init__(title, parent)
        grid = QGridLayout(self)
        self.buttons = {}
        for i, name in enumerate(options):
            btn = QRadioButton(name)
            self.buttons[name] = btn
            btn.toggled.connect(self._on_toggled)
            grid.addWidget(btn, i // columns, i % columns)
        if default and default in self.buttons:
            self.buttons[default].setChecked(True)
        elif options:
            self.buttons[options[0]].setChecked(True)

    def _on_toggled(self, checked):
        if checked:
            self.valueChanged.emit(self.value())

    def value(self):
        for name, btn in self.buttons.items():
            if btn.isChecked():
                return name
        return None

    def set_value(self, name):
        if name in self.buttons:
            self.buttons[name].setChecked(True)


class BaseTab(QWidget):
    """
    Common scaffold for every tab in the bot's tab widget.

    Subclasses call `self.body_layout` to add their controls, and can
    override `get_settings()` / `set_settings()` to persist/restore state.
    An "Apply ALL" button (present on almost every C# tab) is wired to
    `on_apply_all`, which subclasses can override; by default it just
    emits `apply_all_clicked`.
    """

    apply_all_clicked = pyqtSignal()
    settings_changed = pyqtSignal()

    def __init__(self, title="", show_apply_all=True, parent=None):
        super().__init__(parent)
        self.title = title

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        for page in (self, content):
            page.setProperty("tabPage", True)       # nền trắng chung của mọi tab (theme.py)
        self.setAttribute(Qt.WA_StyledBackground, True)
        content.setAttribute(Qt.WA_StyledBackground, True)
        self.body_layout = QVBoxLayout(content)
        self.body_layout.setContentsMargins(20, 16, 21, 16)     # như Join Monster War
        self.body_layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        if show_apply_all:
            # Nút Apply ALL nằm trong vùng cuộn, hàng đầu, sát phải: cuộn thì trôi theo nội dung (giống Join Monster War).
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addStretch(1)
            self.apply_all_row = row_layout
            self.apply_all_button = QPushButton("Apply ALL")
            self.apply_all_button.setObjectName("ApplyAllButton")
            self.apply_all_button.clicked.connect(self.on_apply_all)
            row_layout.addWidget(self.apply_all_button)
            self.add_row(row)

    def add_row(self, widget):
        """Insert a widget above the trailing stretch."""
        self.body_layout.insertWidget(self.body_layout.count() - 1, widget)

    def on_apply_all(self):
        self.apply_all_clicked.emit()

    def get_settings(self) -> dict:
        """Subclasses override to return their current config as a dict."""
        return {}

    def set_settings(self, data: dict):
        """Subclasses override to restore config from a dict."""
        pass


class PlaceholderTab(BaseTab):
    """Generic filler tab: used for any activity not yet implemented."""

    def __init__(self, title, note="Chức năng đang được phát triển.", parent=None):
        super().__init__(title=title, show_apply_all=False, parent=parent)
        label = QLabel(note)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #6b7280; padding: 40px;")
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.add_row(label)
