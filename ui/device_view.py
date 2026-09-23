"""
device_view.py — the workspace for a single connected device.

Python/PyQt5 counterpart of the C# `panelData` + `Start` TabControl: a
QTabWidget hosting one tab per bot module, in the same order as the
original Form3 (Initialization, Join Monster War, Alliance Capacity,
Daily Activities, Open Gift Box, Black Market, Event, Battlefield Shop).
"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .tabs import (
    AllianceCapacityTab,
    BattlefieldShopTab,
    BlackMarketTab,
    DailyActivitiesTab,
    EventTab,
    InitializationTab,
    JoinMonsterWarTab,
    OpenGiftBoxTab,
)


class DeviceView(QWidget):
    start_requested = pyqtSignal(str)       # device_id
    start_all_requested = pyqtSignal()
    # (device_id, settings) — settings keyed by tab title, to be copied
    # onto every other device.
    apply_all_requested = pyqtSignal(str, dict)

    def __init__(self, device_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName("DeviceView")
        self.device_id = device_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.initialization_tab = InitializationTab(device_id=device_id)
        self.join_monster_war_tab = JoinMonsterWarTab()
        self.alliance_capacity_tab = AllianceCapacityTab()
        self.daily_activities_tab = DailyActivitiesTab()
        self.open_gift_box_tab = OpenGiftBoxTab()
        self.black_market_tab = BlackMarketTab()
        self.event_tab = EventTab()
        self.battlefield_shop_tab = BattlefieldShopTab()

        self._add_tab(self.initialization_tab, "Initialization")
        self._add_tab(self.join_monster_war_tab, "Join Monster War")
        self._add_tab(self.alliance_capacity_tab, "Alliance Capacity")
        self._add_tab(self.daily_activities_tab, "Daily Activities")
        self._add_tab(self.open_gift_box_tab, "Open Gift Box")
        self._add_tab(self.black_market_tab, "Black Market")
        self._add_tab(self.event_tab, "Event")
        self._add_tab(self.battlefield_shop_tab, "Battlefield Shop")

        self.initialization_tab.start_clicked.connect(
            lambda: self.start_requested.emit(self.device_id)
        )
        self.initialization_tab.start_all_clicked.connect(self.start_all_requested.emit)

    def _add_tab(self, widget: QWidget, title: str):
        self.tabs.addTab(widget, title)
        widget.setProperty("tab_title", title)
        widget.apply_all_clicked.connect(self._on_apply_all)

    def _on_apply_all(self):
        # Every tab's Apply ALL copies this device's whole config (all
        # tabs) onto every other device. The device id is never copied.
        settings = self.get_settings()
        settings["Initialization"] = {
            k: v for k, v in settings["Initialization"].items() if k != "device_id"
        }
        self.apply_all_requested.emit(self.device_id, settings)

    def set_running(self, running: bool):
        self.initialization_tab.set_running(running)

    def set_all_running(self, running: bool):
        self.initialization_tab.set_all_running(running)

    def get_settings(self) -> dict:
        """Collect settings from every tab into one dict, keyed by tab title."""
        return {self.tabs.tabText(i): self.tabs.widget(i).get_settings()
                for i in range(self.tabs.count())}

    def set_settings(self, data: dict):
        for i in range(self.tabs.count()):
            title = self.tabs.tabText(i)
            if title in data:
                self.tabs.widget(i).set_settings(data[title])
