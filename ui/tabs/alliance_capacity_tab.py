"""
alliance_capacity_tab.py — 1:1 rebuild of tabPage3 ("Alliance Capacity")
from Form3_Designer.cs.
"""
from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "ChoiceGemsAllianceCapacity": {"children": ["label3", "comboBoxTimesAllianceCapacity"],
                                    "loc": [33, 39], "size": [984, 158], "type": "Panel"},
    "buttonAllicanceCapaCtityApplyAll": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "comboBoxTimesAllianceCapacity": {"loc": [166, 24], "size": [121, 30], "type": "ComboBox"},
    "groupBox5": {"children": ["ChoiceGemsAllianceCapacity"], "loc": [22, 67], "size": [1045, 234],
                  "text": "Gems", "type": "GroupBox"},
    "label3": {"loc": [83, 30], "size": [72, 24], "text": "Times: ", "type": "Label"},
    "tabPage3": {"children": ["buttonAllicanceCapaCtityApplyAll", "groupBox5"],
                 "loc": [4, 31], "size": [1088, 609], "text": "Alliance Capacity", "type": "TabPage"},
}
COMBO_ITEMS = {"comboBoxTimesAllianceCapacity": ["No", "10", "20", "50", "100", "ALL"]}
PAGE_SIZE = (1088, 609)


class AllianceCapacityTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("tabPage3", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)

    def get_settings(self) -> dict:
        return {"times": self.controls["comboBoxTimesAllianceCapacity"].currentText()}

    def set_settings(self, data: dict):
        if "times" in data:
            self.controls["comboBoxTimesAllianceCapacity"].setCurrentText(str(data["times"]))
