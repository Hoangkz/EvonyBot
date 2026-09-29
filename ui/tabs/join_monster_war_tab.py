"""
join_monster_war_tab.py — 1:1 rebuild of tabPage2 ("Join Monster War")
from Form3_Designer.cs.
"""
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QCheckBox, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTabWidget, QVBoxLayout, QWidget,
)

from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "BuyHammer": {"loc": [37, 110], "size": [142, 28], "text": "Buy Hammer", "type": "CheckBox"},
    "ChoiceSatamina": {"children": ["radioButton9", "radioButton12", "radioButton10"],
                        "loc": [33, 39], "size": [273, 49], "type": "Panel"},
    "ChoiceTroop": {"children": ["radioButton5", "radioButton6", "radioButton2", "radioButton7",
                                  "radioButton3", "radioButton8", "radioButton1", "radioButton4"],
                     "loc": [32, 39], "size": [655, 94], "type": "Panel"},
    "buttonJoinBossApplyAll": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "checkBoxViking": {"loc": [59, 61], "size": [84, 28], "text": "Viking", "type": "CheckBox"},
    "comboBoxBuyStamina": {"loc": [168, 103], "size": [84, 30], "type": "ComboBox"},
    "comboBoxCrazyEggs": {"loc": [161, 48], "size": [53, 30], "type": "ComboBox"},
    "groupBoss": {"children": ["checkBoxViking"], "loc": [20, 235], "size": [437, 228],
                  "text": "Setting", "type": "GroupBox"},
    "groupBox1": {"children": ["ChoiceTroop"], "loc": [20, 66], "size": [711, 150],
                  "text": "Troop", "type": "GroupBox"},
    "groupBox14": {"children": ["BuyHammer", "comboBoxCrazyEggs", "label6"], "loc": [463, 235],
                   "size": [268, 228], "text": "Crazy Eggs", "type": "GroupBox"},
    "groupBox3": {"children": ["panelSpeedMarching"], "loc": [737, 235], "size": [325, 228],
                  "text": "Speed Marching", "type": "GroupBox"},
    "groupBox4": {"children": ["label7", "comboBoxBuyStamina", "ChoiceSatamina"], "loc": [737, 66],
                  "size": [325, 150], "text": "Use Stamina", "type": "GroupBox"},
    "label6": {"loc": [33, 54], "size": [122, 24], "text": "Time Check: ", "type": "Label"},
    "label7": {"loc": [29, 109], "size": [124, 24], "text": "Buy Stamina: ", "type": "Label"},
    "panelSpeedMarching": {"children": ["radioButton19", "radioButton21", "radioButton16",
                                         "radioButton17", "radioButton18", "radioButton15",
                                         "radioButton11", "radioButton13", "radioButton14"],
                            "loc": [33, 60], "size": [273, 151], "type": "Panel"},
    "radioButton1": {"checked": True, "loc": [33, 12], "size": [97, 28], "text": "Troop 1", "type": "RadioButton"},
    "radioButton10": {"checked": True, "loc": [96, 11], "size": [61, 28], "text": "100", "type": "RadioButton"},
    "radioButton11": {"loc": [30, 11], "size": [50, 28], "text": "1s", "type": "RadioButton"},
    "radioButton12": {"loc": [176, 11], "size": [56, 28], "text": "No", "type": "RadioButton"},
    "radioButton13": {"checked": True, "loc": [182, 107], "size": [56, 28], "text": "No", "type": "RadioButton"},
    "radioButton14": {"loc": [107, 11], "size": [50, 28], "text": "5s", "type": "RadioButton"},
    "radioButton15": {"loc": [182, 11], "size": [60, 28], "text": "10s", "type": "RadioButton"},
    "radioButton16": {"loc": [182, 61], "size": [60, 28], "text": "30s", "type": "RadioButton"},
    "radioButton17": {"loc": [30, 61], "size": [60, 28], "text": "15s", "type": "RadioButton"},
    "radioButton18": {"loc": [107, 61], "size": [60, 28], "text": "20s", "type": "RadioButton"},
    "radioButton19": {"loc": [30, 107], "size": [60, 28], "text": "45s", "type": "RadioButton"},
    "radioButton2": {"loc": [200, 12], "size": [97, 28], "text": "Troop 2", "type": "RadioButton"},
    "radioButton21": {"loc": [107, 107], "size": [60, 28], "text": "60s", "type": "RadioButton"},
    "radioButton3": {"loc": [33, 61], "size": [97, 28], "text": "Troop 5", "type": "RadioButton"},
    "radioButton4": {"loc": [200, 61], "size": [97, 28], "text": "Troop 6", "type": "RadioButton"},
    "radioButton5": {"loc": [520, 61], "size": [97, 28], "text": "Troop 8", "type": "RadioButton"},
    "radioButton6": {"loc": [358, 12], "size": [97, 28], "text": "Troop 3", "type": "RadioButton"},
    "radioButton7": {"loc": [358, 61], "size": [97, 28], "text": "Troop 7", "type": "RadioButton"},
    "radioButton8": {"loc": [520, 12], "size": [97, 28], "text": "Troop 4", "type": "RadioButton"},
    "radioButton9": {"loc": [16, 11], "size": [64, 28], "text": "ALL", "type": "RadioButton"},
    "tabPage2": {"children": ["groupBox14", "groupBox3", "buttonJoinBossApplyAll", "groupBox4",
                               "groupBoss", "groupBox1"],
                 "loc": [4, 31], "size": [1088, 609], "text": "Join Monster War", "type": "TabPage"},
}
COMBO_ITEMS = {"comboBoxBuyStamina": ["10", "16", "20"], "comboBoxCrazyEggs": ["0", "1H", "2H", "3H", "4H"]}
PAGE_SIZE = (1088, 950)

TROOP_RADIOS = ["radioButton1", "radioButton2", "radioButton6", "radioButton8",
                "radioButton3", "radioButton7", "radioButton5", "radioButton4"]
STAMINA_RADIOS = {"radioButton9": "ALL", "radioButton10": "100", "radioButton12": "No"}
SPEED_MARCH_RADIOS = {
    "radioButton13": "No", "radioButton11": "1s", "radioButton14": "5s", "radioButton15": "10s",
    "radioButton17": "15s", "radioButton18": "20s", "radioButton16": "30s",
    "radioButton19": "45s", "radioButton21": "60s",
}


class JoinMonsterWarTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("tabPage2", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)
        self.boss_choices = []
        self._build_boss_selector()

    def _build_boss_selector(self):
        group = QGroupBox("Choose Boss", self.page)
        group.setGeometry(20, 480, 1042, 450)
        layout = QVBoxLayout(group)
        try:
            catalog = json.loads(Path(__file__).with_name("boss.json").read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            error = QLabel(f"Cannot load boss.json: {exc}")
            error.setWordWrap(True)
            layout.addWidget(error)
            return

        toolbar = QHBoxLayout()
        for title, checked in (("Select All", True), ("Clear All", False)):
            button = QPushButton(title)
            button.clicked.connect(lambda _=False, value=checked: self._select_all_bosses(value))
            toolbar.addWidget(button)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        for category in catalog["boss_categories"]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            rows = QVBoxLayout(content)
            for boss in category["list"]:
                row = QHBoxLayout()
                enabled = QCheckBox(boss["name"])
                enabled.setMinimumWidth(280)
                row.addWidget(enabled)
                level_boxes = {}
                levels = boss.get("levels", [boss["level"]] if "level" in boss else [])
                for level in levels:
                    box = QCheckBox(f"Lv {level}")
                    box.setChecked(True)
                    box.setEnabled(False)
                    enabled.toggled.connect(box.setEnabled)
                    level_boxes[level] = box
                    row.addWidget(box)
                row.addStretch()
                rows.addLayout(row)
                self.boss_choices.append((category["category_key"], boss["name"], enabled, level_boxes))
                if boss["name"] == "Viking":
                    legacy = self.controls["checkBoxViking"]
                    enabled.setChecked(legacy.isChecked())
                    enabled.toggled.connect(legacy.setChecked)
                    legacy.toggled.connect(enabled.setChecked)
            rows.addStretch()
            scroll.setWidget(content)
            tabs.addTab(scroll, category["label"])

    def _select_all_bosses(self, checked):
        for _, _, enabled, levels in self.boss_choices:
            if checked:
                for box in levels.values():
                    box.setChecked(True)
            enabled.setChecked(checked)

    def get_settings(self) -> dict:
        c = self.controls
        troop = next((c[n].text() for n in TROOP_RADIOS if c[n].isChecked()), None)
        stamina = next((v for n, v in STAMINA_RADIOS.items() if c[n].isChecked()), None)
        speed = next((v for n, v in SPEED_MARCH_RADIOS.items() if c[n].isChecked()), None)
        return {
            "troop": troop,
            "viking": c["checkBoxViking"].isChecked(),
            "use_stamina": stamina,
            "buy_stamina": c["comboBoxBuyStamina"].currentText(),
            "crazy_eggs_time_check": c["comboBoxCrazyEggs"].currentText(),
            "buy_hammer": c["BuyHammer"].isChecked(),
            "speed_marching": speed,
            "selected_bosses": [
                {"category_key": category, "name": name,
                 "levels": [level for level, box in levels.items() if box.isChecked()]}
                for category, name, enabled, levels in self.boss_choices
                if enabled.isChecked()
            ],
        }

    def set_settings(self, data: dict):
        c = self.controls
        if "viking" in data:
            c["checkBoxViking"].setChecked(bool(data["viking"]))
        if "buy_stamina" in data:
            c["comboBoxBuyStamina"].setCurrentText(str(data["buy_stamina"]))
        if "crazy_eggs_time_check" in data:
            c["comboBoxCrazyEggs"].setCurrentText(str(data["crazy_eggs_time_check"]))
        if "buy_hammer" in data:
            c["BuyHammer"].setChecked(bool(data["buy_hammer"]))
        if "troop" in data:
            _set_radio(c, {n: c[n].text() for n in TROOP_RADIOS}, data["troop"])
        if "use_stamina" in data:
            _set_radio(c, STAMINA_RADIOS, data["use_stamina"])
        if "speed_marching" in data:
            _set_radio(c, SPEED_MARCH_RADIOS, data["speed_marching"])
        if "selected_bosses" in data:
            selected = {(boss["category_key"], boss["name"]): boss.get("levels", [])
                        for boss in data["selected_bosses"]}
            for category, name, enabled, levels in self.boss_choices:
                key = (category, name)
                enabled.setChecked(key in selected)
                for level, box in levels.items():
                    box.setChecked(level in selected[key] if key in selected else True)
        else:
            # Older device settings only had a Viking checkbox.
            for _, name, enabled, levels in self.boss_choices:
                enabled.setChecked(name == "Viking" and bool(data.get("viking", False)))
                for box in levels.values():
                    box.setChecked(True)


def _set_radio(controls, values_by_name: dict, value):
    """Check the radio whose value matches; with no match (e.g. None) leave
    them all unchecked, so an applied config fully replaces the old one."""
    for n, v in values_by_name.items():
        btn = controls[n]
        # Auto-exclusive radios refuse to be unchecked directly.
        btn.setAutoExclusive(False)
        btn.setChecked(v == value)
        btn.setAutoExclusive(True)
