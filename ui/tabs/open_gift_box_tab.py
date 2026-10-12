"""
open_gift_box_tab.py — 1:1 rebuild of tabPage5 ("Open Gift Box")
from Form3_Designer.cs.
"""
from PyQt5.QtCore import pyqtSignal

from bot.activities.open_gift_box.constants import BOX_TYPES

from .tab_placeholder import DesignerTab

# One checkbox per BOX_TYPES entry (label, image folder, ticked by default), shown in that order
# after "All". To add a type, add one line to BOX_TYPES in bot/activities/open_gift_box/constants.py.
BOX_LABELS = [label for label, _, _ in BOX_TYPES]
ALL_CHECKBOX = "checkBoxAll"
BOX_CHECKBOXES = [f"checkBox{i}" for i in range(len(BOX_TYPES))]
BOX_DEFAULTS = [default for _, _, default in BOX_TYPES]
SELECTION_CHECKBOXES = [ALL_CHECKBOX, *BOX_CHECKBOXES]

COLUMNS, CELL_W, ROW_H = 8, 120, 60


def _checkbox(index: int, text: str) -> dict:
    return {"loc": [20 + CELL_W * (index % COLUMNS), 26 + ROW_H * (index // COLUMNS)],
            "size": [112, 28], "text": text, "type": "CheckBox"}


DESIGNER_DATA = {
    "buttonOpenBoxApplyALL": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    ALL_CHECKBOX: _checkbox(0, "All"),
    **{name: _checkbox(i + 1, text) for i, (name, text) in enumerate(zip(BOX_CHECKBOXES, BOX_LABELS))},
    "groupBox7": {"children": ["panelBox"], "loc": [20, 65], "size": [1042, 249],
                  "text": "Selection Gift Box", "type": "GroupBox"},
    "panelBox": {"children": SELECTION_CHECKBOXES,
                 "loc": [21, 35], "size": [994, 192], "type": "Panel"},
    "panelOpen": {"children": ["groupBox7", "buttonOpenBoxApplyALL"],
                  "loc": [3, 3], "size": [1082, 587], "type": "Panel"},
    "tabPage5": {"children": ["panelOpen"], "loc": [4, 31], "size": [1088, 609],
                 "text": "Open Gift Box", "type": "TabPage"},
}
COMBO_ITEMS = {}
PAGE_SIZE = (1088, 609)


class OpenGiftBoxTab(DesignerTab):
    settings_changed = pyqtSignal()     # user ticked/unticked a box -> saved to the DB

    def __init__(self, parent=None):
        super().__init__("tabPage5", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)
        c = self.controls
        for n, default in zip(BOX_CHECKBOXES, BOX_DEFAULTS):
            c[n].setChecked(default)
        self._sync_all()
        c[ALL_CHECKBOX].clicked.connect(self._toggle_all)
        for n in BOX_CHECKBOXES:
            c[n].clicked.connect(self._sync_all)
        for n in SELECTION_CHECKBOXES:      # connected last: runs after the sync above
            c[n].clicked.connect(self.settings_changed)

    def _toggle_all(self, checked: bool):
        for n in BOX_CHECKBOXES:
            self.controls[n].setChecked(checked)

    def _sync_all(self):
        """"All" is ticked only while every box type is."""
        c = self.controls
        c[ALL_CHECKBOX].setChecked(all(c[n].isChecked() for n in BOX_CHECKBOXES))

    def get_settings(self) -> dict:
        c = self.controls
        return {
            "selection_gift_box": {c[n].text(): c[n].isChecked() for n in SELECTION_CHECKBOXES},
        }

    def set_settings(self, data: dict):
        c = self.controls
        values = data.get("selection_gift_box", {})
        for n in SELECTION_CHECKBOXES:
            if c[n].text() in values:
                c[n].setChecked(bool(values[c[n].text()]))
        self._sync_all()
