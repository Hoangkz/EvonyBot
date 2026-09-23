"""
initialization_tab.py — 1:1 rebuild of tabPage1 ("Initialization") from
Form3_Designer.cs: same controls, same nesting, same X/Y/W/H.
"""
from PyQt5.QtCore import pyqtSignal

from ..theme import COLORS
from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "ButtonJoinMonsterWar": {"loc": [85, 53], "size": [230, 40], "text": "Join Monster War", "type": "Button"},
    "ButtonOpenGiftBox": {"loc": [85, 117], "size": [230, 40], "text": "Open Gift Box", "type": "Button"},
    "button10": {"loc": [85, 180], "size": [230, 40], "text": "Event", "type": "Button"},
    "button7": {"loc": [740, 117], "size": [230, 40], "text": "Battlefield Shop", "type": "Button"},
    "button9": {"loc": [935, 372], "size": [140, 50], "text": "Start All", "type": "Button"},
    "buttonAllianceCapacity": {"loc": [409, 53], "size": [230, 40], "text": "Alliance Capacity", "type": "Button"},
    "buttonBlackMarket": {"loc": [409, 117], "size": [230, 40], "text": "Black Market", "type": "Button"},
    "buttonDailyActivities": {"loc": [740, 53], "size": [230, 40], "text": "Daily Activities", "type": "Button"},
    "buttonInitializationApplyAll": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "buttonStart": {"loc": [449, 447], "size": [217, 51], "text": "Start", "type": "Button"},
    "groupBox2": {
        "children": ["button10", "button7", "buttonBlackMarket", "ButtonOpenGiftBox",
                      "ButtonJoinMonsterWar", "buttonDailyActivities", "buttonAllianceCapacity"],
        "loc": [13, 106], "size": [1062, 253], "text": "Select Activity", "type": "GroupBox",
    },
    "labelID": {"loc": [506, 18], "size": [200, 32], "text": "labelID", "type": "Label"},
    "tabPage1": {
        "children": ["button9", "buttonInitializationApplyAll", "buttonStart", "labelID", "groupBox2"],
        "loc": [4, 31], "size": [1088, 609], "text": "Initialization", "type": "TabPage",
    },
}
COMBO_ITEMS = {}
PAGE_SIZE = (1088, 609)

# Original button.Tag values in the C# form matched the activity's
# display text, which in turn matches this app's tab titles.
ACTIVITY_BUTTON_TARGETS = {
    "ButtonJoinMonsterWar": "Join Monster War",
    "buttonAllianceCapacity": "Alliance Capacity",
    "buttonDailyActivities": "Daily Activities",
    "ButtonOpenGiftBox": "Open Gift Box",
    "buttonBlackMarket": "Black Market",
    "button7": "Battlefield Shop",
    "button10": "Event",
}


# Set on each button directly: the designer page's own "background: white"
# stylesheet would otherwise win over the app-level theme.
ACTIVITY_BUTTON_STYLE = f"""
QPushButton:checked {{
    background: {COLORS['success']};
    border-color: {COLORS['success']};
    color: white;
    font-weight: 600;
}}
QPushButton:checked:hover {{
    background: #28985f;
    color: white;
}}
"""


class InitializationTab(DesignerTab):
    start_clicked = pyqtSignal()
    start_all_clicked = pyqtSignal()

    def __init__(self, device_id="", parent=None):
        super().__init__("tabPage1", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)
        c = self.controls

        c["labelID"].setStyleSheet("font-size: 16.2pt;")
        if device_id:
            c["labelID"].setText(device_id)

        c["buttonStart"].setStyleSheet("font-size: 13.8pt;")
        c["buttonStart"].clicked.connect(self.start_clicked.emit)
        c["button9"].clicked.connect(self.start_all_clicked.emit)

        # Activity buttons are toggles: they pick which activities the bot
        # runs (shown green when selected) instead of jumping to the tab.
        for name in ACTIVITY_BUTTON_TARGETS:
            c[name].setCheckable(True)
            c[name].setStyleSheet(ACTIVITY_BUTTON_STYLE)

    def set_running(self, running: bool):
        """While the bot runs, Start becomes Stop (same button, same signal)."""
        self.controls["buttonStart"].setText("Stop" if running else "Start")

    def set_all_running(self, running: bool):
        button = self.controls["button9"]
        button.setText("Stop All" if running else "Start All")
        button.setStyleSheet("background-color: #d9534f; color: white;" if running else "")

    def set_device_id(self, device_id: str):
        self.controls["labelID"].setText(device_id)

    def selected_activities(self) -> list[str]:
        return [target for name, target in ACTIVITY_BUTTON_TARGETS.items()
                if self.controls[name].isChecked()]

    def get_settings(self) -> dict:
        return {
            "device_id": self.controls["labelID"].text(),
            "activities": self.selected_activities(),
        }

    def set_settings(self, data: dict):
        if "device_id" in data:
            self.set_device_id(data["device_id"])
        if "activities" in data:
            selected = set(data["activities"])
            for name, target in ACTIVITY_BUTTON_TARGETS.items():
                self.controls[name].setChecked(target in selected)
