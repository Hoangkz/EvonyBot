"""
open_gift_box_tab.py — 1:1 rebuild of tabPage5 ("Open Gift Box")
from Form3_Designer.cs.
"""
from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "buttonOpenBoxApplyALL": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "checkBox1": {"loc": [496, 86], "size": [114, 28], "text": "Resource", "type": "CheckBox"},
    "checkBox10": {"loc": [273, 86], "size": [72, 28], "text": "Gold", "type": "CheckBox"},
    "checkBox11": {"loc": [59, 86], "size": [82, 28], "text": "Gems", "type": "CheckBox"},
    "checkBox12": {"loc": [740, 26], "size": [183, 28], "text": "Gift Box Resource", "type": "CheckBox"},
    "checkBox13": {"loc": [740, 86], "size": [59, 28], "text": "Etc", "type": "CheckBox"},
    "checkBox14": {"loc": [273, 86], "size": [72, 28], "text": "Gold", "type": "CheckBox"},
    "checkBox15": {"loc": [273, 26], "size": [142, 28], "text": "Gift Box Boss", "type": "CheckBox"},
    "checkBox17": {"loc": [740, 86], "size": [59, 28], "text": "Etc", "type": "CheckBox"},
    "checkBox19": {"loc": [59, 26], "size": [122, 28], "text": "All Gift Box", "type": "CheckBox"},
    "checkBox41": {"loc": [740, 26], "size": [183, 28], "text": "Gift Box Resource", "type": "CheckBox"},
    "checkBox42": {"loc": [496, 26], "size": [168, 28], "text": "Gift Box Alliance", "type": "CheckBox"},
    "checkBox43": {"loc": [59, 86], "size": [82, 28], "text": "Gems", "type": "CheckBox"},
    "checkBox7": {"loc": [496, 86], "size": [114, 28], "text": "Resource", "type": "CheckBox"},
    "checkBox8": {"loc": [496, 26], "size": [168, 28], "text": "Gift Box Alliance", "type": "CheckBox"},
    "checkBox9": {"loc": [273, 26], "size": [142, 28], "text": "Gift Box Boss", "type": "CheckBox"},
    "checkBoxAll": {"loc": [59, 26], "size": [122, 28], "text": "All Gift Box", "type": "CheckBox"},
    "groupBox15": {"children": ["panel4"], "loc": [20, 334], "size": [1042, 249],
                   "text": "Event", "type": "GroupBox"},
    "groupBox7": {"children": ["panelBox"], "loc": [20, 65], "size": [1042, 249],
                  "text": "Selection Gift Box", "type": "GroupBox"},
    "panel4": {"children": ["checkBox1", "checkBox10", "checkBox15", "checkBox17", "checkBox19",
                             "checkBox41", "checkBox42", "checkBox43"],
               "loc": [21, 35], "size": [994, 192], "type": "Panel"},
    "panelBox": {"children": ["checkBox7", "checkBox14", "checkBox9", "checkBox13", "checkBoxAll",
                               "checkBox12", "checkBox8", "checkBox11"],
                 "loc": [21, 35], "size": [994, 192], "type": "Panel"},
    "panelOpen": {"children": ["groupBox15", "groupBox7", "buttonOpenBoxApplyALL"],
                  "loc": [3, 3], "size": [1082, 587], "type": "Panel"},
    "tabPage5": {"children": ["panelOpen"], "loc": [4, 31], "size": [1088, 609],
                 "text": "Open Gift Box", "type": "TabPage"},
}
COMBO_ITEMS = {}
PAGE_SIZE = (1088, 609)

SELECTION_CHECKBOXES = ["checkBoxAll", "checkBox9", "checkBox14", "checkBox8", "checkBox12",
                         "checkBox13", "checkBox11"]
EVENT_CHECKBOXES = ["checkBox19", "checkBox15", "checkBox10", "checkBox42", "checkBox41",
                     "checkBox17", "checkBox43"]


class OpenGiftBoxTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("tabPage5", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)

    def get_settings(self) -> dict:
        c = self.controls
        return {
            "selection_gift_box": {c[n].text(): c[n].isChecked() for n in SELECTION_CHECKBOXES},
            "event": {c[n].text(): c[n].isChecked() for n in EVENT_CHECKBOXES},
        }

    def set_settings(self, data: dict):
        c = self.controls
        for key, names in (("selection_gift_box", SELECTION_CHECKBOXES), ("event", EVENT_CHECKBOXES)):
            values = data.get(key, {})
            for n in names:
                if c[n].text() in values:
                    c[n].setChecked(bool(values[c[n].text()]))
