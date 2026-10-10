"""
device_view.py — the workspace for a single connected device.

Python/PyQt5 counterpart of the C# `panelData` + `Start` TabControl: a
QTabWidget hosting one tab per bot module, in the same order as the
original Form3 (Initialization, Join Monster War, Alliance Capacity,
Daily Activities, Open Gift Box, Black Market, Event),
plus a Logs tab showing this device's bot log (not a settings tab).
"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .tabs import (
    AllianceCapacityTab,
    BlackMarketTab,
    DailyActivitiesTab,
    EventTab,
    InitializationTab,
    JoinMonsterWarTab,
    LogsTab,
    OpenGiftBoxTab,
)


class DeviceView(QWidget):
    start_requested = pyqtSignal(str)       # device_id
    start_all_requested = pyqtSignal()
    stop_all_requested = pyqtSignal()       # Stop All: dừng mọi bot đang chạy
    # (device_id, settings) — settings keyed by tab title, to be copied
    # onto every other device.
    apply_all_requested = pyqtSignal(str, dict)
    server_changed = pyqtSignal(str, str)   # (device_id, server)
    # (device_id, {tab title: settings}) — một tab có `settings_changed` vừa được người dùng sửa.
    tab_settings_changed = pyqtSignal(str, dict)

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

        self._add_tab(self.initialization_tab, "Initialization")
        self._add_tab(self.join_monster_war_tab, "Join Monster War")
        self._add_tab(self.alliance_capacity_tab, "Alliance Capacity")
        self._add_tab(self.daily_activities_tab, "Daily Activities")
        self._add_tab(self.open_gift_box_tab, "Open Gift Box")
        self._add_tab(self.black_market_tab, "Black Market")
        self._add_tab(self.event_tab, "Event")
        # Logs không có cấu hình: thêm thẳng, không nối Apply ALL / settings.
        self.logs_tab = LogsTab()
        self.tabs.addTab(self.logs_tab, "Logs")

        self.initialization_tab.start_clicked.connect(
            lambda: self.start_requested.emit(self.device_id)
        )
        self.initialization_tab.start_all_clicked.connect(self.start_all_requested.emit)
        self.initialization_tab.stop_all_clicked.connect(self.stop_all_requested.emit)
        self.initialization_tab.server_changed.connect(
            lambda server: self.server_changed.emit(self.device_id, server)
        )

    def _add_tab(self, widget: QWidget, title: str):
        self.tabs.addTab(widget, title)
        widget.setProperty("tab_title", title)
        widget.apply_all_clicked.connect(self._on_apply_all)
        if hasattr(widget, "settings_changed"):
            widget.settings_changed.connect(
                lambda: self.tab_settings_changed.emit(self.device_id,
                                                       {title: widget.get_settings()})
            )

    def _on_apply_all(self):
        # Every tab's Apply ALL copies this device's whole config (all
        # tabs) onto every other device. The device id and server are never copied.
        settings = self.get_settings()
        settings["Initialization"] = {
            k: v for k, v in settings["Initialization"].items() if k not in ("device_id", "server")
        }
        self.apply_all_requested.emit(self.device_id, settings)

    def append_log(self, message: str):
        self.logs_tab.append(message)

    def append_history(self, created_at: str, message: str):
        self.logs_tab.append_history(created_at, message)

    def set_running(self, running: bool):
        self.initialization_tab.set_running(running)

    def set_run_counts(self, running: int, total: int):
        """Hai nút Start All / Stop All trong tab Initialization."""
        self.initialization_tab.set_run_counts(running, total)

    def get_settings(self) -> dict:
        """Collect settings from every tab into one dict, keyed by tab title."""
        return {self.tabs.tabText(i): self.tabs.widget(i).get_settings()
                for i in range(self.tabs.count()) if self.tabs.widget(i) is not self.logs_tab}

    def set_settings(self, data: dict):
        for i in range(self.tabs.count()):
            title = self.tabs.tabText(i)
            if title in data and self.tabs.widget(i) is not self.logs_tab:
                self.tabs.widget(i).set_settings(data[title])
