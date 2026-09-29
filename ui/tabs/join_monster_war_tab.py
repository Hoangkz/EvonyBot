"""Compact Join Monster War settings with responsive boss groups."""
import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QLabel,
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
        self._boss_style = """
            QCheckBox, QRadioButton, QLabel, QComboBox, QPushButton { font-size: 12px; }
            QCheckBox, QRadioButton { spacing: 3px; padding: 0px; }
            QCheckBox::indicator, QRadioButton::indicator { width: 13px; height: 13px; }
            QGroupBox { font-size: 12px; margin-top: 9px; padding-top: 5px; }
            QPushButton { padding: 3px 8px; }
        """
        self.body_layout.setContentsMargins(8, 4, 8, 8)
        self.body_layout.setSpacing(6)
        self.findChild(QScrollArea).setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header = QWidget()
        self._header_grid = QGridLayout(header)
        self._header_grid.setContentsMargins(12, 0, 12, 0)
        self._header_grid.setSpacing(6)
        troop = QGroupBox("Troop")
        self._troop_group = troop
        troop.setMinimumHeight(150)
        self._troop_grid = QGridLayout(troop)
        self._troop_grid.setContentsMargins(32, 32, 32, 16)
        self._troop_grid.setHorizontalSpacing(20)
        self._troop_grid.setVerticalSpacing(16)
        self._troop_grid.setAlignment(Qt.AlignLeft)
        for i, name in enumerate(TROOP_RADIOS):
            button = QRadioButton(f"Troop {i + 1}")
            button.setChecked(i == 0)
            self.controls[name] = button
            self._troop_grid.addWidget(button, i // 2, i % 2)
        self._header_grid.addWidget(troop, 0, 0)
        stamina = QGroupBox("Use Stamina")
        self._stamina_group = stamina
        stamina.setMinimumHeight(150)
        row = QGridLayout(stamina)
        self._stamina_grid = row
        row.setContentsMargins(29, 32, 18, 16)
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
        self._header_grid.addWidget(stamina, 0, 1)
        self._header_grid.setColumnStretch(0, 711)
        self._header_grid.setColumnStretch(1, 325)
        self.add_row(header)
        self._build_boss_selector()

    def _build_boss_selector(self):
        try:
            catalog = json.loads(Path(__file__).with_name("boss.json").read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            error = QLabel(f"Cannot load boss.json: {exc}")
            error.setWordWrap(True)
            self.add_row(error)
            return
        for category in catalog["boss_categories"]:
            group = QGroupBox(category["label"])
            group.setStyleSheet(self._boss_style)
            grid = QGridLayout(group)
            grid.setContentsMargins(8, 8, 8, 6)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(5)
            grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            cards = []
            for boss in category["list"]:
                levels = boss.get("levels", [boss["level"]] if "level" in boss else [])
                card = QGroupBox(boss["name"]) if levels else QWidget()
                row = QVBoxLayout(card)
                row.setContentsMargins(6, 8, 6, 5) if levels else row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(2)
                enabled = None
                if not levels:
                    enabled = QCheckBox(boss["name"].replace(" / ", " /\n"))
                    row.addWidget(enabled)
                level_boxes = {}
                level_grid = QGridLayout()
                level_grid.setContentsMargins(0, 0, 0, 0)
                level_grid.setHorizontalSpacing(5)
                level_grid.setVerticalSpacing(2)
                level_grid.setAlignment(Qt.AlignLeft)
                for i, level in enumerate(levels):
                    box = QCheckBox(str(level))
                    box.setToolTip(f"{boss['name']} - Level {level}")
                    level_boxes[level] = box
                    level_grid.addWidget(box, i // 4, i % 4)
                if levels:
                    select_all = QPushButton("All")
                    select_all.clicked.connect(
                        lambda _=False, boxes=level_boxes: self._select_levels(boxes)
                    )
                    row.addWidget(select_all, alignment=Qt.AlignLeft)
                    row.addLayout(level_grid)
                cards.append(card)
                grid.addWidget(card, len(cards) - 1, 0, Qt.AlignTop)
                self.boss_choices.append((category["category_key"], boss["name"], enabled, level_boxes))
            self._boss_grids.append((grid, cards))
            self.add_row(group)

    @staticmethod
    def _select_levels(boxes):
        for box in boxes.values():
            box.setChecked(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        available = max(1, self.width() - 64)
        narrow = available < 400
        self._header_grid.setContentsMargins(0 if narrow else 12, 0, 0 if narrow else 12, 0)
        self._troop_grid.setContentsMargins(8 if narrow else 32, 32, 8 if narrow else 32, 16)
        self._stamina_grid.setContentsMargins(8 if narrow else 29, 32, 8 if narrow else 18, 16)
        wide = available >= 1000
        self._header_grid.removeWidget(self._stamina_group)
        self._header_grid.addWidget(self._stamina_group, 0 if wide else 1, 1 if wide else 0)
        self._header_grid.setColumnStretch(1, 325 if wide else 0)
        troop_columns = 4 if available >= 650 else 2
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
                if (enabled.isChecked() if enabled is not None else any(box.isChecked() for box in levels.values()))
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
                if enabled is not None:
                    enabled.setChecked(key in selected)
                for level, box in levels.items():
                    box.setChecked(level in selected.get(key, []))
        else:
            # Older device settings only had a Viking checkbox.
            for _, name, enabled, levels in self.boss_choices:
                if enabled is not None:
                    enabled.setChecked(name == "Viking" and bool(data.get("viking", False)))
                for box in levels.values():
                    box.setChecked(False)



def _set_radio(controls, values_by_name: dict, value):
    """Check the radio whose value matches; with no match (e.g. None) leave
    them all unchecked, so an applied config fully replaces the old one."""
    for n, v in values_by_name.items():
        btn = controls[n]
        # Auto-exclusive radios refuse to be unchecked directly.
        btn.setAutoExclusive(False)
        btn.setChecked(v == value)
        btn.setAutoExclusive(True)
