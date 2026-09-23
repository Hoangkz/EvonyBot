"""
daily_activities_tab.py — 1:1 rebuild of tabPage4 ("Daily Activities")
from Form3_Designer.cs.
"""
from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "buttonDailyActivitiesApplyALL": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "checkBox2": {"loc": [534, 283], "size": [207, 28], "text": "Resource Garthering", "type": "CheckBox"},
    "checkBox21": {"loc": [534, 131], "size": [140, 28], "text": "Trap Buiding", "type": "CheckBox"},
    "checkBox22": {"loc": [36, 81], "size": [116, 28], "text": "Gold Levy", "type": "CheckBox"},
    "checkBox23": {"loc": [286, 183], "size": [113, 28], "text": "Research", "type": "CheckBox"},
    "checkBox24": {"loc": [286, 236], "size": [137, 28], "text": "Construction", "type": "CheckBox"},
    "checkBox25": {"loc": [36, 183], "size": [151, 28], "text": "Resource Tax", "type": "CheckBox"},
    "checkBox26": {"checked": True, "loc": [818, 31], "size": [160, 28], "text": "Troop Heading", "type": "CheckBox"},
    "checkBox27": {"loc": [534, 183], "size": [115, 28], "text": "PvP Battle", "type": "CheckBox"},
    "checkBox28": {"loc": [36, 329], "size": [171, 28], "text": "Buy x10 Stamina", "type": "CheckBox"},
    "checkBox29": {"loc": [286, 283], "size": [80, 28], "text": "Labor", "type": "CheckBox"},
    "checkBox3": {"loc": [534, 236], "size": [202, 28], "text": "Resource Collecting", "type": "CheckBox"},
    "checkBox30": {"loc": [534, 79], "size": [79, 28], "text": "Patrol", "type": "CheckBox"},
    "checkBox31": {"loc": [818, 131], "size": [199, 28], "text": "Material Composing", "type": "CheckBox"},
    "checkBox32": {"loc": [36, 31], "size": [178, 28], "text": "Wheel of Fortune", "type": "CheckBox"},
    "checkBox33": {"loc": [36, 131], "size": [138, 28], "text": "Black Market", "type": "CheckBox"},
    "checkBox34": {"loc": [286, 31], "size": [179, 28], "text": "Alliance Donation", "type": "CheckBox"},
    "checkBox35": {"loc": [36, 236], "size": [175, 28], "text": "Boss Monster Kill", "type": "CheckBox"},
    "checkBox36": {"loc": [818, 236], "size": [155, 28], "text": "Monster Killing", "type": "CheckBox"},
    "checkBox37": {"loc": [818, 183], "size": [138, 28], "text": "Troop Killing", "type": "CheckBox"},
    "checkBox38": {"loc": [534, 31], "size": [196, 28], "text": "General Enhancing", "type": "CheckBox"},
    "checkBox39": {"loc": [36, 283], "size": [174, 28], "text": "Relic Exploration", "type": "CheckBox"},
    "checkBox4": {"loc": [818, 79], "size": [157, 28], "text": "Troop Training", "type": "CheckBox"},
    "checkBox40": {"loc": [286, 329], "size": [160, 28], "text": "Valueble Event", "type": "CheckBox"},
    "checkBox5": {"loc": [286, 81], "size": [144, 28], "text": "Alliance Help", "type": "CheckBox"},
    "checkBox6": {"loc": [286, 131], "size": [98, 28], "text": "Offering", "type": "CheckBox"},
    "groupBox6": {"children": ["panelDailyActivites"], "loc": [20, 65], "size": [1045, 502],
                  "text": "Selection Activity", "type": "GroupBox"},
    "panelDailyActivites": {
        "children": ["checkBox40", "checkBox28", "checkBox39", "checkBox38", "checkBox37",
                      "checkBox36", "checkBox35", "checkBox34", "checkBox33", "checkBox32",
                      "checkBox31", "checkBox30", "checkBox29", "checkBox27", "checkBox26",
                      "checkBox25", "checkBox24", "checkBox23", "checkBox22", "checkBox21",
                      "checkBox6", "checkBox5", "checkBox4", "checkBox3", "checkBox2"],
        "loc": [3, 24], "size": [1039, 475], "type": "Panel",
    },
    "tabPage4": {"children": ["buttonDailyActivitiesApplyALL", "groupBox6"],
                 "loc": [4, 31], "size": [1088, 609], "text": "Daily Activities", "type": "TabPage"},
}
COMBO_ITEMS = {}
PAGE_SIZE = (1088, 609)

_CHECKBOX_NAMES = [n for n in DESIGNER_DATA if n.startswith("checkBox")]


class DailyActivitiesTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("tabPage4", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)

    def get_settings(self) -> dict:
        return {
            self.controls[name].text(): self.controls[name].isChecked()
            for name in _CHECKBOX_NAMES
        }

    def set_settings(self, data: dict):
        by_text = {self.controls[n].text(): n for n in _CHECKBOX_NAMES}
        for label, checked in data.items():
            if label in by_text:
                self.controls[by_text[label]].setChecked(bool(checked))
