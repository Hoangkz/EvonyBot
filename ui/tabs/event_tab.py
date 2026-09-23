"""
event_tab.py — 1:1 rebuild of the "Event" TabPage from Form3_Designer.cs.
"""
from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "Event": {"children": ["groupBoxEvent3Day", "groupBoxOtherEvent", "groupBoxEvent7Day",
                            "buttonEventApplyALL"],
              "loc": [4, 31], "size": [1088, 609], "text": "Event", "type": "TabPage"},
    "buttonEventApplyALL": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "checkBoxEvent3DayChampion": {"loc": [10, 17], "size": [119, 28], "text": "Champion", "type": "CheckBox"},
    "checkBoxEvent7DayCultivateGenerals": {"loc": [10, 16], "size": [183, 28],
                                            "text": "Cultivate Generals", "type": "CheckBox"},
    "comboBoxEvent3DayDonateAlliance": {"loc": [161, 7], "size": [121, 30], "type": "ComboBox"},
    "comboBoxEvent3DayHealTroops": {"loc": [432, 7], "size": [121, 30], "type": "ComboBox"},
    "groupBoxEvent3Day": {"children": ["panel6"], "loc": [20, 204], "size": [1047, 171],
                          "text": "Event  3 Day", "type": "GroupBox"},
    "groupBoxEvent7Day": {"children": ["panelEvent7Day"], "loc": [20, 65], "size": [1047, 130],
                          "text": "Event 7 Day", "type": "GroupBox"},
    "groupBoxOtherEvent": {"children": ["panel5"], "loc": [20, 383], "size": [1047, 167],
                           "text": "Other Event", "type": "GroupBox"},
    "label5": {"loc": [8, 13], "size": [147, 24], "text": "Donate Alliance:", "type": "Label"},
    "label9": {"loc": [307, 13], "size": [119, 24], "text": "Heal Troops:", "type": "Label"},
    "panel5": {"children": ["checkBoxEvent3DayChampion"], "loc": [21, 35], "size": [1010, 82], "type": "Panel"},
    "panel6": {"children": ["label9", "comboBoxEvent3DayHealTroops", "label5",
                             "comboBoxEvent3DayDonateAlliance"],
               "loc": [21, 35], "size": [1010, 82], "type": "Panel"},
    "panelEvent7Day": {"children": ["checkBoxEvent7DayCultivateGenerals"],
                       "loc": [21, 35], "size": [1010, 82], "type": "Panel"},
}
COMBO_ITEMS = {
    "comboBoxEvent3DayDonateAlliance": ["5", "3", "1"],
    "comboBoxEvent3DayHealTroops": ["30000", "10000", "5000"],
}
PAGE_SIZE = (1088, 609)


class EventTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("Event", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)

    def get_settings(self) -> dict:
        c = self.controls
        return {
            "cultivate_generals": c["checkBoxEvent7DayCultivateGenerals"].isChecked(),
            "heal_troops": c["comboBoxEvent3DayHealTroops"].currentText(),
            "donate_alliance": c["comboBoxEvent3DayDonateAlliance"].currentText(),
            "champion": c["checkBoxEvent3DayChampion"].isChecked(),
        }

    def set_settings(self, data: dict):
        c = self.controls
        if "cultivate_generals" in data:
            c["checkBoxEvent7DayCultivateGenerals"].setChecked(bool(data["cultivate_generals"]))
        if "heal_troops" in data:
            c["comboBoxEvent3DayHealTroops"].setCurrentText(str(data["heal_troops"]))
        if "donate_alliance" in data:
            c["comboBoxEvent3DayDonateAlliance"].setCurrentText(str(data["donate_alliance"]))
        if "champion" in data:
            c["checkBoxEvent3DayChampion"].setChecked(bool(data["champion"]))
