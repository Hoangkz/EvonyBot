"""
_designer.py — shared engine that rebuilds a tab's control tree exactly
as it was laid out in the original C# WinForms designer (Form3_Designer.cs):
same parent/child nesting, same X/Y/W/H coordinates, same control types,
same text. Each concrete tab module only supplies its own slice of the
parsed designer data (DESIGNER_DATA / COMBO_ITEMS) and this module does
the actual QWidget construction with setGeometry(), just like WinForms'
Location/Size.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QLabel,
    QPushButton,
    QRadioButton,
    QWidget,
)

_FACTORY = {
    "Panel": lambda: QWidget(),
    "GroupBox": lambda: QGroupBox(),
    "Button": lambda: QPushButton(),
    "Label": lambda: QLabel(),
    "CheckBox": lambda: QCheckBox(),
    "RadioButton": lambda: QRadioButton(),
    "ComboBox": lambda: QComboBox(),
}


def build(name, data, combo_items, registry, parent):
    """Recursively (re)create `name` and its children under `parent`,
    positioned exactly as in the original designer, and register every
    widget in `registry[name]` for later lookup by the tab class."""
    node = data[name]
    factory = _FACTORY.get(node["type"], QWidget)
    widget = factory()
    widget.setParent(parent)

    loc = node.get("loc")
    size = node.get("size")
    if loc and size:
        widget.setGeometry(loc[0], loc[1], size[0], size[1])
    elif size:
        widget.resize(*size)

    text = node.get("text")
    if text:
        if isinstance(widget, QGroupBox):
            widget.setTitle(text)
        elif isinstance(widget, (QLabel, QPushButton, QCheckBox, QRadioButton)):
            widget.setText(text)

    if isinstance(widget, QComboBox) and name in combo_items:
        widget.addItems(combo_items[name])

    if node.get("checked") and isinstance(widget, (QCheckBox, QRadioButton)):
        widget.setChecked(True)

    widget.show()
    registry[name] = widget

    for child_name in node.get("children", []):
        if child_name in data:
            build(child_name, data, combo_items, registry, parent=widget)

    return widget


def build_tab(root_name, data, combo_items, size):
    """Build a whole tab page: a fixed-size white QWidget (matching the
    original tabPage's Size) containing every descendant control from
    the designer tree. Returns (page_widget, registry) where registry
    maps every original C# control name -> its QWidget instance."""
    page = QWidget()
    page.setFixedSize(*size)
    page.setStyleSheet("background: white;")
    registry = {}
    for child_name in data[root_name].get("children", []):
        if child_name in data:
            build(child_name, data, combo_items, registry, parent=page)
    return page, registry
