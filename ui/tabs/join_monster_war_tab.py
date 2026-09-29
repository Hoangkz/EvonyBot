"""
Join Monster War settings with a compact boss selection grid.
"""
import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTabWidget, QVBoxLayout, QWidget,
)

from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "ChoiceSatamina": {"children": ["radioButton9", "radioButton12", "radioButton10"],
                        "loc": [33, 39], "size": [273, 49], "type": "Panel"},
    "ChoiceTroop": {"children": ["radioButton5", "radioButton6", "radioButton2", "radioButton7",
                                  "radioButton3", "radioButton8", "radioButton1", "radioButton4"],
                     "loc": [32, 39], "size": [655, 94], "type": "Panel"},
    "buttonJoinBossApplyAll": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "comboBoxBuyStamina": {"loc": [168, 103], "size": [84, 30], "type": "ComboBox"},
    "groupBox1": {"children": ["ChoiceTroop"], "loc": [20, 66], "size": [711, 150],
                  "text": "Troop", "type": "GroupBox"},
    "groupBox4": {"children": ["label7", "comboBoxBuyStamina", "ChoiceSatamina"], "loc": [737, 66],
                  "size": [325, 150], "text": "Use Stamina", "type": "GroupBox"},
    "label7": {"loc": [29, 109], "size": [124, 24], "text": "Buy Stamina: ", "type": "Label"},
    "radioButton1": {"checked": True, "loc": [33, 12], "size": [97, 28], "text": "Troop 1", "type": "RadioButton"},
    "radioButton10": {"checked": True, "loc": [96, 11], "size": [61, 28], "text": "100", "type": "RadioButton"},
    "radioButton12": {"loc": [176, 11], "size": [56, 28], "text": "No", "type": "RadioButton"},
    "radioButton2": {"loc": [200, 12], "size": [97, 28], "text": "Troop 2", "type": "RadioButton"},
    "radioButton3": {"loc": [33, 61], "size": [97, 28], "text": "Troop 5", "type": "RadioButton"},
    "radioButton4": {"loc": [200, 61], "size": [97, 28], "text": "Troop 6", "type": "RadioButton"},
    "radioButton5": {"loc": [520, 61], "size": [97, 28], "text": "Troop 8", "type": "RadioButton"},
    "radioButton6": {"loc": [358, 12], "size": [97, 28], "text": "Troop 3", "type": "RadioButton"},
    "radioButton7": {"loc": [358, 61], "size": [97, 28], "text": "Troop 7", "type": "RadioButton"},
    "radioButton8": {"loc": [520, 12], "size": [97, 28], "text": "Troop 4", "type": "RadioButton"},
    "radioButton9": {"loc": [16, 11], "size": [64, 28], "text": "ALL", "type": "RadioButton"},
    "tabPage2": {"children": ["buttonJoinBossApplyAll", "groupBox4", "groupBox1"],
                 "loc": [4, 31], "size": [1088, 609], "text": "Join Monster War", "type": "TabPage"},
}
COMBO_ITEMS = {"comboBoxBuyStamina": ["10", "16", "20"]}
PAGE_SIZE = (1088, 700)

TROOP_RADIOS = ["radioButton1", "radioButton2", "radioButton6", "radioButton8",
                "radioButton3", "radioButton7", "radioButton5", "radioButton4"]
STAMINA_RADIOS = {"radioButton9": "ALL", "radioButton10": "100", "radioButton12": "No"}


class JoinMonsterWarTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("tabPage2", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)
        self.boss_choices = []
        self._build_boss_selector()

    def _build_boss_selector(self):
        group = QGroupBox("Choose Boss", self.page)
        group.setGeometry(20, 230, 1042, 450)
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
            rows = QGridLayout(content)
            rows.setAlignment(Qt.AlignTop)
            rows.setSpacing(8)
            for column in range(3):
                rows.setColumnStretch(column, 1)
            for index, boss in enumerate(category["list"]):
                card = QGroupBox()
                row = QVBoxLayout(card)
                row.setContentsMargins(10, 8, 10, 8)
                enabled = QCheckBox()
                enabled.setAccessibleName(boss["name"])
                enabled.setToolTip(boss["name"])
                title = QLabel(boss["name"])
                title.setWordWrap(True)
                title.setBuddy(enabled)
                heading = QHBoxLayout()
                heading.addWidget(enabled)
                heading.addWidget(title, 1)
                row.addLayout(heading)
                level_boxes = {}
                levels = boss.get("levels", [boss["level"]] if "level" in boss else [])
                level_grid = QGridLayout()
                for level_index, level in enumerate(levels):
                    box = QCheckBox(f"Lv {level}")
                    box.setChecked(True)
                    box.setEnabled(False)
                    enabled.toggled.connect(box.setEnabled)
                    level_boxes[level] = box
                    level_grid.addWidget(box, level_index // 3, level_index % 3)
                if levels:
                    row.addLayout(level_grid)
                rows.addWidget(card, index // 3, index % 3)
                self.boss_choices.append((category["category_key"], boss["name"], enabled, level_boxes))
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
        return {
            "troop": troop,
            "use_stamina": stamina,
            "buy_stamina": c["comboBoxBuyStamina"].currentText(),
            "selected_bosses": [
                {"category_key": category, "name": name,
                 "levels": [level for level, box in levels.items() if box.isChecked()]}
                for category, name, enabled, levels in self.boss_choices
                if enabled.isChecked()
            ],
        }

    def set_settings(self, data: dict):
        c = self.controls
        if "buy_stamina" in data:
            c["comboBoxBuyStamina"].setCurrentText(str(data["buy_stamina"]))
        if "troop" in data:
            _set_radio(c, {n: c[n].text() for n in TROOP_RADIOS}, data["troop"])
        if "use_stamina" in data:
            _set_radio(c, STAMINA_RADIOS, data["use_stamina"])
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
