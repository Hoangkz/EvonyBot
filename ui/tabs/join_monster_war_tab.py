"""Compact Join Monster War settings with responsive boss groups."""
import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)
from .tab_placeholder import BaseTab

TROOP_RADIOS = [f"troop_{i}" for i in range(1, 9)]
STAMINA_OPTIONS = ["ALL", "100", "No"]
HAMMER_OPTIONS = ["No", "10", "9", "8", "7", "6","5","4","3","2","1"]
BOSS_CATALOG_VERSION = 2
# Boss active mới của từng phiên bản. Cấu hình cũ chưa biết boss này sẽ được
# bật một lần; sau khi lưu version mới, người dùng vẫn có thể tắt bình thường.
NEW_DEFAULT_BOSSES = {"Elite Temple Guard": 2}


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
        troop.setGeometry(0, 0, 470, 150)
        self._troop_group = troop
        troop_panel = QWidget(troop)
        troop_panel.setGeometry(32, 43, 410, 94)
        for i, name in enumerate(TROOP_RADIOS):
            button = QCheckBox(f"Troop {i + 1}", troop_panel)
            button.setGeometry((10, 110, 210, 310)[i % 4], 0 if i < 4 else 50, 97, 28)
            button.setChecked(i == 0)
            self.controls[name] = button
        stamina = QGroupBox("Setting", header)
        stamina.setGeometry(476, 0, 566, 150)
        self._stamina_group = stamina
        # Chọn tướng khi hành quân; tướng phụ chỉ đi cùng khi có chọn tướng.
        general = QCheckBox("Select General", stamina)
        general.setGeometry(290, 39, 250, 28)
        assistant = QCheckBox("With Assistant General", stamina)
        assistant.setGeometry(290, 75, 250, 28)
        assistant.setEnabled(False)
        general.toggled.connect(assistant.setEnabled)
        # Khi chọn tướng: bấm tab Development, chỉ chọn tướng phát triển.
        development = QCheckBox("Development General", stamina)
        development.setGeometry(290, 111, 250, 28)
        development.setEnabled(False)
        general.toggled.connect(development.setEnabled)
        self.controls["checkBoxSelectGeneral"] = general
        self.controls["checkBoxAssistantGeneral"] = assistant
        self.controls["checkBoxDevelopmentGeneral"] = development
        for y, (name, text, items, current) in zip((36, 72, 108), (
            ("comboBoxUseStamina", "Use Stamina: ", STAMINA_OPTIONS, "100"),
            ("comboBoxBuyStamina", "Buy Stamina: ", ["10", "16", "20"], "10"),
            ("comboBoxBuyHammer", "Buy Hammer: ", HAMMER_OPTIONS, "No"),
        )):
            label = QLabel(text, stamina)
            label.setGeometry(29, y + 3, 124, 24)
            combo = QComboBox(stamina)
            combo.setGeometry(168, y, 84, 30)
            combo.addItems(items)
            combo.setCurrentText(current)
            self.controls[name] = combo
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
        actives = []   # (checkbox, "active" in boss.json): ticked by default
        for category in catalog["boss_categories"]:
            standard = category["category_key"] == "standard_bosses"
            group = QGroupBox(category["label"])
            group.setStyleSheet(self._boss_style)
            grid = QGridLayout(group)
            grid.setContentsMargins(16, 8, 16, 6)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(4)
            grid.setAlignment(Qt.AlignTop | Qt.AlignLeft if standard else Qt.AlignTop)
            cards = []
            for boss in category["list"]:
                # "levels": [{"level", "tier"?, "power"}] (or plain level numbers). A
                # standard boss's own "level" is its rank, not something to tick.
                infos = {(info["level"] if isinstance(info, dict) else info):
                         (info if isinstance(info, dict) else {}) for info in boss.get("levels", [])}
                levels = list(infos)
                boxed = bool(levels) or not standard
                card = QGroupBox(boss["name"]) if boxed else QWidget()
                row = QVBoxLayout(card)
                row.setContentsMargins(8, 8, 8, 4) if boxed else row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(2)
                enabled = None
                if not levels:
                    enabled = QCheckBox(boss["name"] if standard else "Join")
                    if boxed and boss["name"] == "Viking":
                        options = QHBoxLayout()
                        options.setContentsMargins(0, 0, 0, 0)
                        options.setSpacing(12)
                        options.addWidget(enabled)
                        summon = QCheckBox("Summon")
                        self.controls["viking_summon"] = summon
                        options.addWidget(summon)
                        options.addStretch()
                        row.addLayout(options)
                    else:
                        row.addWidget(enabled)
                    actives.append((enabled, bool(boss.get("active"))))
                level_boxes = {}
                level_grid = QGridLayout()
                level_grid.setContentsMargins(0, 0, 0, 0)
                level_grid.setHorizontalSpacing(5)
                level_grid.setVerticalSpacing(2)
                level_grid.setAlignment(Qt.AlignLeft)
                offset = 1 if len(levels) > 1 else 0
                for i, level in enumerate(levels, offset):
                    box = QCheckBox(str(level))
                    detail = ", ".join(str(infos[level][k]) for k in ("tier", "power") if infos[level].get(k))
                    box.setToolTip(f"{boss['name']} - Level {level}" + (f" ({detail})" if detail else ""))
                    level_boxes[level] = box
                    actives.append((box, bool(infos[level].get("active"))))
                    level_grid.addWidget(box, i // 4, i % 4)
                if levels:
                    row.addLayout(level_grid)
                if len(levels) > 1:
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
                cards.append(card)
                grid.addWidget(card, len(cards) - 1, 0, Qt.AlignTop)
                self.boss_choices.append((category["category_key"], boss["name"], enabled, level_boxes))
            if standard:
                boss_boxes = {name: box for key, name, box, _ in self.boss_choices
                              if key == category["category_key"] and box is not None}
                select_all = QCheckBox("All")
                select_all.clicked.connect(
                    lambda checked, boxes=boss_boxes: self._select_levels(boxes, checked)
                )
                for box in boss_boxes.values():
                    box.toggled.connect(
                        lambda _checked, boxes=boss_boxes, all_box=select_all:
                        all_box.setChecked(all(boss.isChecked() for boss in boxes.values()))
                    )
                cards.insert(0, select_all)
                grid.addWidget(select_all, len(cards) - 1, 0, Qt.AlignTop)
            self._boss_grids.append((grid, cards, standard))
            self.add_row(group)
        # "active" in boss.json (on a plain boss, or on each level) = ticked by
        # default. Set after the "All" boxes are wired so they follow.
        for box, active in actives:
            box.setChecked(active)

    @staticmethod
    def _select_levels(boxes, checked):
        for box in boxes.values():
            box.setChecked(checked)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        available = max(1, self.width() - 96)
        layout = []
        for _, cards, _ in self._boss_grids:
            width = max((card.sizeHint().width() for card in cards), default=120)
            columns = max(1, min(len(cards), available // (width + 12)))
            layout.append((width, columns))
        if layout == self._columns:
            return
        self._columns = layout
        for (grid, cards, standard), (width, columns) in zip(self._boss_grids, layout):
            for card in cards:
                grid.removeWidget(card)
            for col in range(grid.columnCount()):
                grid.setColumnMinimumWidth(col, 0)
                grid.setColumnStretch(col, 0)
            for i, card in enumerate(cards):
                if standard:
                    rows = max(1, -(-len(cards) // columns))
                    grid.addWidget(card, i % rows, i // rows, Qt.AlignTop | Qt.AlignLeft)
                    grid.setColumnMinimumWidth(i // rows, width)
                else:
                    grid.addWidget(card, i // columns, i % columns, Qt.AlignTop)
            if not standard:
                for col in range(columns):
                    grid.setColumnStretch(col, 1)

    def get_settings(self) -> dict:
        c = self.controls
        return {
            "troop": [c[n].text() for n in TROOP_RADIOS if c[n].isChecked()],
            "use_stamina": c["comboBoxUseStamina"].currentText(),
            "buy_stamina": c["comboBoxBuyStamina"].currentText(),
            "buy_hammer": c["comboBoxBuyHammer"].currentText(),
            "select_general": c["checkBoxSelectGeneral"].isChecked(),
            "select_assistant_general": c["checkBoxAssistantGeneral"].isChecked(),
            "development_general": c["checkBoxDevelopmentGeneral"].isChecked(),
            "viking_summon": c["viking_summon"].isChecked() if "viking_summon" in c else False,
            "boss_catalog_version": BOSS_CATALOG_VERSION,
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
            troops = data["troop"] if isinstance(data["troop"], list) else [data["troop"]]
            for n in TROOP_RADIOS:
                c[n].setChecked(c[n].text() in troops)
        if "use_stamina" in data:
            c["comboBoxUseStamina"].setCurrentText(str(data["use_stamina"]))
        if "buy_hammer" in data:
            c["comboBoxBuyHammer"].setCurrentText(str(data["buy_hammer"]))
        c["checkBoxSelectGeneral"].setChecked(bool(data.get("select_general", False)))
        c["checkBoxAssistantGeneral"].setChecked(bool(data.get("select_assistant_general", False)))
        c["checkBoxDevelopmentGeneral"].setChecked(bool(data.get("development_general", False)))
        if "viking_summon" in c:
            c["viking_summon"].setChecked(bool(data.get("viking_summon", False)))
        if "selected_bosses" in data:
            selected = {(boss["category_key"], boss["name"]): boss.get("levels", [])
                        for boss in data["selected_bosses"]}
            saved_catalog_version = int(data.get("boss_catalog_version", 0) or 0)
            for category, name, enabled, levels in self.boss_choices:
                key = (category, name)
                if enabled is not None:
                    introduced = NEW_DEFAULT_BOSSES.get(name, 0)
                    enable_new_default = introduced > saved_catalog_version
                    enabled.setChecked(key in selected or enable_new_default)
                for level, box in levels.items():
                    box.setChecked(level in selected.get(key, []))
        else:
            # Older device settings only had a Viking checkbox.
            for _, name, enabled, levels in self.boss_choices:
                if enabled is not None:
                    enabled.setChecked((name == "Viking" and bool(data.get("viking", False)))
                                       or name in NEW_DEFAULT_BOSSES)
                for box in levels.values():
                    box.setChecked(False)

