"""Compact, responsive Join Monster War settings."""
import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QScrollArea, QVBoxLayout, QWidget,
)

from .tab_placeholder import BaseTab

TROOP_RADIOS = [f"troop_{i}" for i in range(1, 9)]
STAMINA_RADIOS = {"stamina_all": "ALL", "stamina_100": "100", "stamina_no": "No"}


class JoinMonsterWarTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title="Join Monster War", parent=parent)
        self.controls = {}
        self.boss_choices = []
        self._boss_grids = []
        self._columns = None
        self.setStyleSheet("""
            QCheckBox, QRadioButton, QLabel, QComboBox, QPushButton {
                font-size: 12px;
            }
            QCheckBox, QRadioButton { spacing: 3px; padding: 0px; }
            QCheckBox::indicator, QRadioButton::indicator { width: 13px; height: 13px; }
            QGroupBox { font-size: 12px; margin-top: 9px; padding-top: 5px; }
            QPushButton { padding: 3px 8px; }
        """)
        self.body_layout.setContentsMargins(8, 4, 8, 8)
        self.body_layout.setSpacing(6)
        scroll = self.findChild(QScrollArea)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        troop = QGroupBox("Troop")
        grid = QGridLayout(troop)
        self._troop_grid = grid
        grid.setContentsMargins(8, 8, 8, 6)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)
        grid.setAlignment(Qt.AlignLeft)
        for i, name in enumerate(TROOP_RADIOS):
            button = QRadioButton(f"Troop {i + 1}")
            button.setChecked(i == 0)
            self.controls[name] = button
            grid.addWidget(button, i // 4, i % 4)
        self.add_row(troop)
        stamina = QGroupBox("Use Stamina")
        row = QGridLayout(stamina)
        row.setContentsMargins(8, 8, 8, 6)
        row.setSpacing(4)
        row.setAlignment(Qt.AlignLeft)
        for i, (name, label) in enumerate(STAMINA_RADIOS.items()):
            button = QRadioButton(label)
            button.setChecked(label == "100")
            self.controls[name] = button
            row.addWidget(button, 0, i)
        row.addWidget(QLabel("Buy Stamina:"), 1, 0, 1, 2)
        combo = QComboBox()
        combo.addItems(["10", "16", "20"])
        self.controls["comboBoxBuyStamina"] = combo
        row.addWidget(combo, 1, 2)
        self.add_row(stamina)
        self._build_boss_selector()

    def _build_boss_selector(self):
        try:
            catalog = json.loads(Path(__file__).with_name("boss.json").read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            error = QLabel(f"Cannot load boss.json: {exc}")
            error.setWordWrap(True)
            self.add_row(error)
            return
        toolbar = QWidget()
        buttons = QHBoxLayout(toolbar)
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(4)
        for title, checked in (("Select All", True), ("Clear All", False)):
            button = QPushButton(title)
            button.clicked.connect(lambda _=False, value=checked: self._select_all_bosses(value))
            buttons.addWidget(button)
        buttons.addStretch()
        self.add_row(toolbar)
        for category in catalog["boss_categories"]:
            group = QGroupBox(category["label"])
            grid = QGridLayout(group)
            grid.setContentsMargins(8, 8, 8, 6)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(5)
            grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            cards = []
            for boss in category["list"]:
                card = QWidget()
                row = QVBoxLayout(card)
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(2)
                enabled = QCheckBox(boss["name"].replace(" / ", " /\n"))
                row.addWidget(enabled)
                levels = boss.get("levels", [boss["level"]] if "level" in boss else [])
                level_boxes = {}
                level_grid = QGridLayout()
                level_grid.setContentsMargins(16, 0, 0, 0)
                level_grid.setHorizontalSpacing(5)
                level_grid.setVerticalSpacing(2)
                level_grid.setAlignment(Qt.AlignLeft)
                for i, level in enumerate(levels):
                    box = QCheckBox(str(level))
                    box.setToolTip(f"{boss['name']} - Level {level}")
                    box.setChecked(True)
                    box.setEnabled(False)
                    enabled.toggled.connect(box.setEnabled)
                    level_boxes[level] = box
                    level_grid.addWidget(box, i // 4, i % 4)
                if levels:
                    row.addLayout(level_grid)
                cards.append(card)
                grid.addWidget(card, len(cards) - 1, 0, Qt.AlignTop)
                self.boss_choices.append((category["category_key"], boss["name"], enabled, level_boxes))
            self._boss_grids.append((grid, cards))
            self.add_row(group)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reflow the groups instead of retaining a fixed-width designer page.
        available = max(1, self.width() - 64)
        troop_columns = 4 if available >= 450 else 2
        for i, name in enumerate(TROOP_RADIOS):
            button = self.controls[name]
            self._troop_grid.removeWidget(button)
            self._troop_grid.addWidget(button, i // troop_columns, i % troop_columns)
        card_width = max((card.sizeHint().width() for _, cards in self._boss_grids
                          for card in cards), default=240)
        columns = max(1, available // (card_width + 12))
        if columns == self._columns:
            return
        self._columns = columns
        for grid, cards in self._boss_grids:
            for card in cards:
                grid.removeWidget(card)
            for i, card in enumerate(cards):
                grid.addWidget(card, i // columns, i % columns, Qt.AlignTop)

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
