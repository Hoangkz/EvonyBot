"""Configuration UI for the Daily Activities automation.

Only tasks backed by an implementation in ``bot.activities.daily_activities``
are selectable. The remaining legacy entries stay visible at the bottom, but
cannot accidentally enable work that the bot cannot perform.
"""
from PyQt5.QtCore import QSignalBlocker
from PyQt5.QtWidgets import QCheckBox, QComboBox, QGridLayout, QGroupBox, QLabel

from bot.activities.daily_activities.offering.constants import (
    OFFER_GEMS_CHOICES,
    OFFER_GEMS_DEFAULT,
    OFFER_GEMS_KEY,
)

from .tab_placeholder import BaseTab


# The key stays compatible with the database and automation Task label; display
# text fixes spelling mistakes from the original WinForms form.
SUPPORTED_TASKS = (
    ("Monster Killing", "Monster Killing"),
    ("Resource Collecting", "Resource Collecting"),
    ("Offering", "Offering"),
    ("Resource Gathering", "Resource Gathering"),
    ("Resource Tax", "Resource Tax"),
    ("Gold Levy", "Gold Levy"),
    ("Troop Training", "Troop Training"),
    ("Troop Heading", "Troop Healing"),
    ("Trap Buiding", "Trap Building"),
    ("Alliance Donation", "Alliance Donation"),
    ("Black Market", "Black Market"),
    ("General Enhancing", "General Enhancing"),
    ("Wheel of Fortune", "Wheel of Fortune"),
    ("Patrol", "Patrol"),
    ("Material Composing", "Material Composing"),
)

UNSUPPORTED_TASKS = (
    ("Alliance Help", "Alliance Help"),
    ("Research", "Research"),
    ("Construction", "Construction"),
    ("PvP Battle", "PvP Battle"),
    ("Troop Killing", "Troop Killing"),
    ("Boss Monster Kill", "Boss Monster Kill"),
    ("Relic Exploration", "Relic Exploration"),
    ("Labor", "Labor"),
    ("Valueble Event", "Valuable Event"),
    ("Buy x10 Stamina", "Buy x10 Stamina (legacy)"),
)

GENERAL_KEY = "General"


class DailyActivitiesTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title="Daily Activities", show_apply_all=True, parent=parent)

        self.task_boxes: dict[str, QCheckBox] = {}
        self.unsupported_boxes: dict[str, QCheckBox] = {}

        general = QGroupBox("General")
        general_grid = QGridLayout(general)
        self.buy_stamina = QCheckBox("Buy Stamina")
        self.stamina_quantity = QComboBox()
        self.stamina_quantity.addItems(["10", "20", "30"])
        self.stamina_quantity.setCurrentText("10")
        self.stamina_quantity.setEnabled(False)
        self.buy_hammers = QCheckBox("Buy All Hammers")
        general_grid.addWidget(self.buy_stamina, 0, 0)
        general_grid.addWidget(QLabel("Quantity"), 0, 1)
        general_grid.addWidget(self.stamina_quantity, 0, 2)
        general_grid.addWidget(self.buy_hammers, 0, 3)
        # Offering: số lần bấm "Offer Gems" (tốn kim cương) — chỉ bật khi tích Offering.
        self.offer_gems = QComboBox()
        self.offer_gems.addItems([str(n) for n in OFFER_GEMS_CHOICES])
        self.offer_gems.setCurrentText(str(OFFER_GEMS_DEFAULT))
        self.offer_gems.setToolTip("Số lần bấm Offer Gems ở Đền thờ (mỗi lần tốn kim cương). 0 = không offer.")
        general_grid.addWidget(QLabel("Offer Gems (times)"), 1, 0)
        general_grid.addWidget(self.offer_gems, 1, 2)
        general_grid.setColumnStretch(4, 1)
        self.add_row(general)

        selection = QGroupBox("Selection Daily")
        selection_grid = QGridLayout(selection)
        for index, (key, label) in enumerate(SUPPORTED_TASKS):
            box = QCheckBox(label)
            # Preserve the old form's default while keeping the stored key compatible.
            box.setChecked(key == "Troop Heading")
            self.task_boxes[key] = box
            selection_grid.addWidget(box, index // 4, index % 4)
        for column in range(4):
            selection_grid.setColumnStretch(column, 1)
        self.add_row(selection)

        unavailable = QGroupBox("Unavailable Daily — not implemented yet")
        unavailable_grid = QGridLayout(unavailable)
        for index, (key, label) in enumerate(UNSUPPORTED_TASKS):
            box = QCheckBox(label)
            box.setEnabled(False)
            box.setToolTip("This daily activity does not have automation logic yet.")
            self.unsupported_boxes[key] = box
            unavailable_grid.addWidget(box, index // 4, index % 4)
        for column in range(4):
            unavailable_grid.setColumnStretch(column, 1)
        self.add_row(unavailable)

        self.buy_stamina.toggled.connect(self.stamina_quantity.setEnabled)
        self.buy_stamina.clicked.connect(self.settings_changed)
        self.buy_hammers.clicked.connect(self.settings_changed)
        self.stamina_quantity.activated.connect(self.settings_changed)
        self.offer_gems.activated.connect(self.settings_changed)
        self.task_boxes["Offering"].toggled.connect(self.offer_gems.setEnabled)
        self.offer_gems.setEnabled(self.task_boxes["Offering"].isChecked())
        for box in self.task_boxes.values():
            box.clicked.connect(self.settings_changed)

    def get_settings(self) -> dict:
        settings = {key: box.isChecked() for key, box in self.task_boxes.items()}
        # Clear legacy unsupported selections instead of sending them to the runner.
        settings.update({key: False for key in self.unsupported_boxes})
        settings[OFFER_GEMS_KEY] = int(self.offer_gems.currentText())
        settings[GENERAL_KEY] = {
            "buy_stamina": self.buy_stamina.isChecked(),
            "stamina_quantity": int(self.stamina_quantity.currentText()),
            "buy_all_hammers": self.buy_hammers.isChecked(),
        }
        return settings

    def set_settings(self, data: dict):
        # Avoid writing partially restored state while loading a device.
        widgets = [self.buy_stamina, self.stamina_quantity, self.buy_hammers, self.offer_gems,
                   *self.task_boxes.values()]
        blockers = [QSignalBlocker(widget) for widget in widgets]
        try:
            for key, box in self.task_boxes.items():
                value = data.get(key)
                if key == "Resource Gathering" and key not in data:
                    value = data.get("Resource Garthering")
                if value is not None:
                    box.setChecked(bool(value))

            general = data.get(GENERAL_KEY, {})
            if not isinstance(general, dict):
                general = {}
            # Migrate the old standalone checkbox into the new General setting.
            buy_stamina = general.get("buy_stamina", data.get("Buy x10 Stamina", False))
            self.buy_stamina.setChecked(bool(buy_stamina))
            quantity = str(general.get("stamina_quantity", 10))
            if self.stamina_quantity.findText(quantity) >= 0:
                self.stamina_quantity.setCurrentText(quantity)
            self.buy_hammers.setChecked(bool(general.get("buy_all_hammers", False)))
            self.stamina_quantity.setEnabled(self.buy_stamina.isChecked())
            offer = str(data.get(OFFER_GEMS_KEY, OFFER_GEMS_DEFAULT))
            if self.offer_gems.findText(offer) >= 0:
                self.offer_gems.setCurrentText(offer)
            self.offer_gems.setEnabled(self.task_boxes["Offering"].isChecked())
        finally:
            # Keep blockers alive through every assignment, then release together.
            del blockers
