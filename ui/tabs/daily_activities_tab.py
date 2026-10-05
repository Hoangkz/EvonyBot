"""Configuration UI for the Daily Activities automation.

Only tasks backed by an implementation in ``bot.activities.daily_activities``
are selectable. The remaining legacy entries stay visible at the bottom, but
cannot accidentally enable work that the bot cannot perform.
"""
from PyQt5.QtCore import QSignalBlocker
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QWidget)

from bot.activities.daily_activities import alliance_donation, alliance_help
from bot.activities.daily_activities.offering.constants import (
    OFFER_GEMS_CHOICES,
    OFFER_GEMS_DEFAULT,
    OFFER_GEMS_KEY,
)
from bot.activities.daily_activities.resource_tax.constants import (
    TAX_CHOICES,
    TAX_DEFAULT,
    TAX_FREE_DEFAULT,
    TAX_FREE_KEY,
    TAX_KEY,
    TAX_RESOURCES,
)

from .tab_placeholder import BaseTab


# The key stays compatible with the database and automation Task label; display
# text fixes spelling mistakes from the original WinForms form.
SUPPORTED_TASKS = (
    ("Offering", "Offering"),   # ô chọn số lần (không phải checkbox) -> đặt đầu; thứ tự chạy ở run.py TASKS
    ("Monster Killing", "Monster Killing"),
    ("Resource Collecting", "Resource Collecting"),
    ("Resource Gathering", "Resource Gathering"),
    ("Resource Tax", "Resource Tax"),
    ("Gold Levy", "Gold Levy"),
    ("Troop Training", "Troop Training"),
    ("Troop Heading", "Troop Healing"),
    ("Trap Buiding", "Trap Building"),
    ("Alliance Donation", "Alliance Donation"),
    ("Alliance Help", "Alliance Help"),
    ("Black Market", "Black Market"),
    ("General Enhancing", "General Enhancing"),
    ("Wheel of Fortune", "Wheel of Fortune"),
    ("Patrol", "Patrol"),
    ("Material Composing", "Material Composing"),
)

UNSUPPORTED_TASKS = (
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
# Nhiệm vụ theo giờ: ô chọn giờ (0 / 1h .. 4h) thay cho checkbox; 0 = không làm. {key: (constants, tooltip)}.
HOURLY_TASKS = {
    alliance_donation.constants.INTERVAL_KEY: (
        alliance_donation.constants,
        "Donate lượt miễn phí ở Alliance Science, chưa xong thì làm lại sau chừng này giờ (không ưu tiên). "
        "0 = không làm."),
    alliance_help.constants.INTERVAL_KEY: (
        alliance_help.constants,
        "Help All ở Alliance Help, chưa xong thì làm lại sau chừng này giờ (không ưu tiên, sau Alliance "
        "Donation). 0 = không làm."),
}
OFFERING_KEY = "Offering"


class DailyActivitiesTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(title="Daily Activities", show_apply_all=True, parent=parent)

        self.task_boxes: dict[str, QCheckBox] = {}
        self.unsupported_boxes: dict[str, QCheckBox] = {}
        self.hourly_combos: dict[str, QComboBox] = {}

        general = QGroupBox("General")
        general_grid = QGridLayout(general)
        # Buy Stamina: 0 = không mua.
        self.stamina_quantity = QComboBox()
        self.stamina_quantity.addItems(["0", "10", "20", "30"])
        self.stamina_quantity.setCurrentText("0")
        self.buy_hammers = QCheckBox("Buy Hammer")
        general_grid.addWidget(QLabel("Buy Stamina"), 0, 0)
        general_grid.addWidget(self.stamina_quantity, 0, 2)
        general_grid.addWidget(self.buy_hammers, 0, 3)
        general_grid.setColumnStretch(4, 1)
        self.add_row(general)

        selection = QGroupBox("Selection Daily")
        selection_grid = QGridLayout(selection)
        for index, (key, label) in enumerate(SUPPORTED_TASKS):
            if key == OFFERING_KEY:
                # Offering: số lần bấm "Offer Gems" (tốn kim cương) thay cho checkbox; 0 = không làm.
                self.offer_gems = QComboBox()
                self.offer_gems.addItems([str(n) for n in OFFER_GEMS_CHOICES])
                self.offer_gems.setCurrentText("0")
                self.offer_gems.setToolTip("Số lần bấm Offer Gems ở Đền thờ (mỗi lần tốn kim cương). 0 = không offer.")
                cell = QWidget()
                row = QHBoxLayout(cell)
                row.setContentsMargins(0, 0, 0, 0)
                row.addWidget(QLabel(label))
                row.addWidget(self.offer_gems)
                row.addStretch(1)
                selection_grid.addWidget(cell, index // 4, index % 4)
                continue
            if key in HOURLY_TASKS:
                # Nhiệm vụ theo giờ: chu kỳ thử (giờ) thay cho checkbox; 0 = không làm.
                consts, tip = HOURLY_TASKS[key]
                combo = QComboBox()
                combo.addItems(_hours_text(h) for h in consts.INTERVAL_CHOICES)
                combo.setCurrentText(_hours_text(consts.INTERVAL_DEFAULT))
                combo.setToolTip(tip)
                self.hourly_combos[key] = combo
                cell = QWidget()
                row = QHBoxLayout(cell)
                row.setContentsMargins(0, 0, 0, 0)
                row.addWidget(QLabel(label))
                row.addWidget(combo)
                row.addStretch(1)
                selection_grid.addWidget(cell, index // 4, index % 4)
                continue
            box = QCheckBox(label)
            # Preserve the old form's default while keeping the stored key compatible.
            box.setChecked(key == "Troop Heading")
            self.task_boxes[key] = box
            selection_grid.addWidget(box, index // 4, index % 4)
        # City Tax: số lần thu mỗi loại + ô Free (chỉ một loại được tích).
        tax = QGroupBox("City Tax")
        tax_grid = QGridLayout(tax)
        self.tax_counts: dict[str, QComboBox] = {}
        self.tax_free: dict[str, QCheckBox] = {}
        for index, name in enumerate(TAX_RESOURCES):
            count = QComboBox()
            count.addItems([str(n) for n in TAX_CHOICES])
            count.setCurrentText(str(TAX_DEFAULT))
            free = QCheckBox("Free")
            free.setChecked(name == TAX_FREE_DEFAULT)
            free.setToolTip("Thu hết lượt miễn phí ở loại này rồi cộng thêm số lần chọn (chỉ tích được một loại).")
            free.clicked.connect(lambda checked, name=name: self._on_tax_free(name, checked))
            self.tax_counts[name] = count
            self.tax_free[name] = free
            tax_grid.addWidget(QLabel(name), index, 0)
            tax_grid.addWidget(count, index, 1)
            tax_grid.addWidget(free, index, 2)
        tax_grid.setColumnStretch(3, 1)
        selection_grid.addWidget(tax, (len(SUPPORTED_TASKS) + 3) // 4, 0, 1, 4)
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

        self.buy_hammers.clicked.connect(self.settings_changed)
        self.stamina_quantity.activated.connect(self.settings_changed)
        self.offer_gems.activated.connect(self.settings_changed)
        for combo in self.hourly_combos.values():
            combo.activated.connect(self.settings_changed)
        for count in self.tax_counts.values():
            count.activated.connect(self.settings_changed)
        for box in self.task_boxes.values():
            box.clicked.connect(self.settings_changed)

    def _on_tax_free(self, name: str, checked: bool):
        """Ô Free chỉ được tích ở một loại: tích loại này thì bỏ tích các loại khác."""
        if checked:
            for other, box in self.tax_free.items():
                if other != name:
                    box.setChecked(False)
        self.settings_changed.emit()

    def get_settings(self) -> dict:
        settings = {key: box.isChecked() for key, box in self.task_boxes.items()}
        # Clear legacy unsupported selections instead of sending them to the runner.
        settings.update({key: False for key in self.unsupported_boxes})
        offer = int(self.offer_gems.currentText())
        settings[OFFERING_KEY] = offer > 0
        settings[OFFER_GEMS_KEY] = offer
        for key, combo in self.hourly_combos.items():
            settings[key] = _hours_value(combo.currentText())
        tax = {name: int(box.currentText()) for name, box in self.tax_counts.items()}
        tax[TAX_FREE_KEY] = next((name for name, box in self.tax_free.items() if box.isChecked()), None)
        settings[TAX_KEY] = tax
        quantity = int(self.stamina_quantity.currentText())
        settings[GENERAL_KEY] = {
            "buy_stamina": quantity > 0,
            "stamina_quantity": quantity,
            "buy_all_hammers": self.buy_hammers.isChecked(),
        }
        return settings

    def set_settings(self, data: dict):
        # Avoid writing partially restored state while loading a device.
        widgets = [self.stamina_quantity, self.buy_hammers, self.offer_gems, *self.hourly_combos.values(),
                   *self.task_boxes.values(), *self.tax_counts.values(), *self.tax_free.values()]
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
            # Cấu hình cũ có checkbox Buy Stamina riêng (hoặc "Buy x10 Stamina"): bỏ tích = 0.
            buy_stamina = general.get("buy_stamina", data.get("Buy x10 Stamina", False))
            quantity = str(general.get("stamina_quantity", 10)) if buy_stamina else "0"
            if self.stamina_quantity.findText(quantity) >= 0:
                self.stamina_quantity.setCurrentText(quantity)
            self.buy_hammers.setChecked(bool(general.get("buy_all_hammers", False)))
            # Cấu hình cũ: checkbox Offering + ô Offer Gems riêng; bỏ tích Offering = 0.
            offer = str(data.get(OFFER_GEMS_KEY, OFFER_GEMS_DEFAULT)) if data.get(OFFERING_KEY) else "0"
            if self.offer_gems.findText(offer) >= 0:
                self.offer_gems.setCurrentText(offer)
            # Nhiệm vụ theo giờ: số giờ; cấu hình cũ là ô tích (True -> mặc định, False -> 0).
            for key, combo in self.hourly_combos.items():
                consts = HOURLY_TASKS[key][0]
                hours = data.get(key, consts.INTERVAL_DEFAULT)
                if isinstance(hours, bool):
                    hours = consts.INTERVAL_DEFAULT if hours else 0
                if hours not in consts.INTERVAL_CHOICES:
                    hours = consts.INTERVAL_DEFAULT
                combo.setCurrentText(_hours_text(hours))
            tax = data.get(TAX_KEY, {})
            if not isinstance(tax, dict):
                tax = {}
            for name, box in self.tax_counts.items():
                count = str(tax.get(name, TAX_DEFAULT))
                box.setCurrentText(count if box.findText(count) >= 0 else str(TAX_DEFAULT))
            for name, box in self.tax_free.items():
                box.setChecked(tax.get(TAX_FREE_KEY, TAX_FREE_DEFAULT) == name)
        finally:
            # Keep blockers alive through every assignment, then release together.
            del blockers


def _hours_text(hours) -> str:
    """Chữ hiển thị của ô chọn giờ (nhiệm vụ theo giờ): 0 -> "0", 4 -> "4h"."""
    return "0" if not hours else f"{int(hours)}h"


def _hours_value(text: str) -> int:
    """Ngược lại _hours_text: "4h" -> 4, "0" -> 0."""
    return int(text.rstrip("h") or 0)
