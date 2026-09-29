"""Compact Join Monster War settings with responsive boss groups."""
import json
import textwrap
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QScrollArea, QVBoxLayout, QWidget,
)
from .tab_placeholder import BaseTab

TROOP_RADIOS = [f"troop_{i}" for i in range(1, 9)]
STAMINA_RADIOS = {"stamina_all": "ALL", "stamina_100": "100", "stamina_no": "No"}


class JoinMonsterWarTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title="Join Monster War", show_apply_all=False, parent=parent)
        self.controls = {}
        self.boss_choices = []
        self._boss_grids = []
        self._columns = None
        self._boss_style = "QCheckBox { spacing: 3px; padding: 0px; }"
        self.body_layout.setContentsMargins(20, 16, 21, 16)
        self.body_layout.setSpacing(7)
        apply_row = QWidget()
        apply_layout = QHBoxLayout(apply_row)
        apply_layout.setContentsMargins(0, 0, 0, 0)
        apply_layout.addStretch()
        self.apply_all_button = QPushButton("Apply ALL")
        self.apply_all_button.setFixedSize(132, 43)
        self.apply_all_button.clicked.connect(self.on_apply_all)
        apply_layout.addWidget(self.apply_all_button)
        self.add_row(apply_row)
        self.findChild(QScrollArea).setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Original designer geometry, relative to the header's (20, 66) origin.
        header = QWidget()
        header.setFixedHeight(150)
        troop = QGroupBox("Troop", header)
        troop.setGeometry(0, 0, 711, 150)
        self._troop_group = troop
        troop_panel = QWidget(troop)
        troop_panel.setGeometry(32, 39, 655, 94)
        for i, name in enumerate(TROOP_RADIOS):
            button = QRadioButton(f"Troop {i + 1}", troop_panel)
            button.setGeometry((33, 200, 358, 520)[i % 4], 12 if i < 4 else 61, 97, 28)
            button.setChecked(i == 0)
            self.controls[name] = button
        stamina = QGroupBox("Use Stamina", header)
        stamina.setGeometry(717, 0, 325, 150)
        self._stamina_group = stamina
        stamina_panel = QWidget(stamina)
        stamina_panel.setGeometry(33, 39, 273, 49)
        for (name, label), x, width in zip(STAMINA_RADIOS.items(), (16, 96, 176), (64, 61, 56)):
            button = QRadioButton(label, stamina_panel)
            button.setGeometry(x, 11, width, 28)
            button.setChecked(label == "100")
            self.controls[name] = button
        label = QLabel("Buy Stamina: ", stamina)
        label.setGeometry(29, 109, 124, 24)
        combo = QComboBox(stamina)
        combo.setGeometry(168, 103, 84, 30)
        combo.addItems(["10", "16", "20"])
        self.controls["comboBoxBuyStamina"] = combo
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
            standard = category["category_key"] == "standard_bosses"
            group = QGroupBox(category["label"])
            group.setStyleSheet(self._boss_style)
            grid = QGridLayout(group)
            grid.setContentsMargins(16, 8, 16, 6)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(4)
            grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            cards = []
            for boss in category["list"]:
                levels = boss.get("levels", [boss["level"]] if "level" in boss else [])
                card = QGroupBox(boss["name"]) if levels else QWidget()
                row = QVBoxLayout(card)
                row.setContentsMargins(8, 8, 8, 4) if levels else row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(2)
                if levels and len(boss["name"]) > 20:
                    card.setTitle("")
                    title = QLabel(boss["name"])
                    title.setWordWrap(True)
                    row.addWidget(title)
                enabled = None
                if not levels:
                    enabled = QCheckBox(textwrap.fill(boss["name"], width=8 if standard else 22))
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
                    level_grid.addWidget(box, (i + 1) // 4, (i + 1) % 4)
                if levels:
                    select_all = QCheckBox("All")
                    select_all.clicked.connect(
                        lambda checked, boxes=level_boxes: self._select_levels(boxes, checked)
                    )
                    for box in level_boxes.values():
                        box.toggled.connect(
                            lambda _checked, boxes=level_boxes, all_box=select_all:
                            all_box.setChecked(all(level.isChecked() for level in boxes.values()))
                        )
                    level_grid.addWidget(select_all, 0, 0)
                    row.addLayout(level_grid)
                cards.append(card)
                grid.addWidget(card, len(cards) - 1, 0, Qt.AlignTop)
                self.boss_choices.append((category["category_key"], boss["name"], enabled, level_boxes))
            self._boss_grids.append((grid, cards, standard))
            self.add_row(group)

    @staticmethod
    def _select_levels(boxes, checked):
        for box in boxes.values():
            box.setChecked(checked)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        available = max(1, self.width() - 64)
        card_width = max((card.sizeHint().width() for _, cards, _ in self._boss_grids
                          for card in cards), default=240)
        columns = max(1, (available - 128) // (card_width + 12))
        if columns == self._columns:
            return
        self._columns = columns
        for grid, cards, standard in self._boss_grids:
            for card in cards:
                grid.removeWidget(card)
            for i, card in enumerate(cards):
                if standard:
                    rows = max(1, (len(cards) + 5) // 6)
                    grid.addWidget(card, i % rows, i // rows, Qt.AlignTop)
                else:
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
