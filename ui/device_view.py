"""
device_view.py — the workspace for a single connected device.

Python/PyQt5 counterpart of the C# `panelData` + `Start` TabControl: a
QTabWidget hosting one tab per bot module, in the same order as the
original Form3 (Initialization, Join Monster War, Alliance Capacity,
Daily Activities, Open Gift Box, Black Market, Event),
plus a Logs tab showing this device's bot log (not a settings tab).
"""
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractButton, QAbstractSpinBox, QButtonGroup, QCheckBox, QComboBox, QLineEdit, QPushButton, QRadioButton, QTabWidget,
    QVBoxLayout, QWidget,
)

from .flow_layout import FlowLayout

from .tabs import (
    AllianceCapacityTab,
    BlackMarketTab,
    CraftTab,
    GatherResourcesTab,
    DailyActivitiesTab,
    EventTab,
    FindBossTab,
    InitializationTab,
    JoinMonsterWarTab,
    LogsTab,
    OpenGiftBoxTab,
    RecruitGeneralTab,
)


def subtract_craft_item(data: dict, item_id: str):
    """Trừ 1 số lượng trang bị `item_id` trong cấu hình tab Craft (`data`, sửa tại chỗ); về 0 thì bỏ hẳn."""
    items = data.setdefault("items", {})
    if item_id in items:
        if items[item_id] > 1:
            items[item_id] -= 1
        else:
            items.pop(item_id)


class DeviceView(QWidget):
    start_requested = pyqtSignal(str)       # device_id
    start_all_requested = pyqtSignal()
    stop_all_requested = pyqtSignal()       # Stop All: dừng mọi bot đang chạy
    # (device_id, settings) — settings keyed by tab title, to be copied
    # onto every other device.
    apply_all_requested = pyqtSignal(str, dict)
    server_changed = pyqtSignal(str, str)   # (device_id, server)
    reset_progress_requested = pyqtSignal(str, bool)   # (device_id, True = tab Event, False = Daily Activities)
    active_requested = pyqtSignal(str, bool)   # device_id, muốn kích hoạt?
    reset_info_requested = pyqtSignal(str)   # device_id: xoá bubble, server, nền văn minh, route
    civilization_changed = pyqtSignal(str, int)   # (device_id, nền văn minh 1..7, 0 = tự nhận)
    # (device_id, {tab title: settings}) — một tab có `settings_changed` vừa được người dùng sửa.
    tab_settings_changed = pyqtSignal(str, dict)
    auto_angles_requested = pyqtSignal(str)   # device_id: nút Auto của tab Find Boss
    profile_selected = pyqtSignal(str, str)  # (device_id, tên hồ sơ) bấm nút hồ sơ
    profile_added = pyqtSignal(str, str)      # (device_id, tên hồ sơ mới) nút "+"
    profile_deleted = pyqtSignal(str, str)    # (device_id, tên hồ sơ)

    def __init__(self, device_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName("DeviceView")
        self.device_id = device_id
        self._shown_once = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Hàng tab nằm ngay phía trên nội dung như thanh tab thường nhưng tự xuống hàng (tối đa vài hàng) khi không đủ chỗ, nên luôn thấy hết
        # mà không phải cuộn. QTabWidget vẫn là nơi chứa các trang (view.tabs: settings, main.py), chỉ ẩn thanh tab của nó; hai bên đồng bộ chỉ mục.
        self.tab_strip = QWidget()
        self.tab_strip.setObjectName("TabStrip")
        self.tab_flow = FlowLayout(self.tab_strip, spacing=2)
        self.tab_buttons = QButtonGroup(self)
        self.tab_buttons.setExclusive(True)
        layout.addWidget(self.tab_strip)
        self.tabs = QTabWidget()
        self.tabs.tabBar().hide()
        self.tabs.currentChanged.connect(self._sync_tab_buttons)
        layout.addWidget(self.tabs)

        # Dựng cả 10 tab một lượt tốn ~1 s (theme áp lên từng widget). Chỉ Initialization và Logs dựng ngay; tab còn lại là
        # trang trống, dựng khi mở tab đó hoặc lúc rảnh (_build_next_tab), hoặc khi cần cả bộ (get_settings...).
        self._pending_settings: dict[str, dict] = {}   # cấu hình set_settings() cho tab chưa dựng
        self._event_done: dict | None = None            # daily_done cho tab Event chưa dựng
        self._lazy: dict[str, tuple] = {}               # tiêu đề -> (tên thuộc tính, hàm tạo) của tab chưa dựng
        self.initialization_tab = InitializationTab(device_id=device_id)
        self._add_tab(self.initialization_tab, "Initialization")
        for title, attr, factory in (
                ("Join Monster War", "join_monster_war_tab", JoinMonsterWarTab),
                ("Daily Activities", "daily_activities_tab", DailyActivitiesTab),
                ("Event", "event_tab", EventTab),
                ("Open Gift Box", "open_gift_box_tab", OpenGiftBoxTab),
                ("Alliance Capacity", "alliance_capacity_tab", AllianceCapacityTab),
                ("Black Market", "black_market_tab", BlackMarketTab),
                # Recruit General: đứng ngay trên tab Logs.
                ("Recruit General", "recruit_general_tab", RecruitGeneralTab),
                ("Find Boss", "find_boss_tab", FindBossTab),
                ("Craft", "craft_tab", CraftTab),
                ("Gather Resources", "gather_resources_tab", GatherResourcesTab)):
            self._lazy[title] = (attr, factory)
            self._add_tab_button(title, self.tabs.addTab(QWidget(), title))
        # Logs không có cấu hình: thêm thẳng, không nối Apply ALL / settings.
        self.logs_tab = LogsTab()
        self._add_tab_button("Logs", self.tabs.addTab(self.logs_tab, "Logs"))
        self.tabs.currentChanged.connect(self._build_tab_at)
        self._background_timer = QTimer(self)
        self._background_timer.setSingleShot(True)
        self._background_timer.timeout.connect(self._build_next_tab)

        self.initialization_tab.start_clicked.connect(
            lambda: self.start_requested.emit(self.device_id)
        )
        self.initialization_tab.start_all_clicked.connect(self.start_all_requested.emit)
        self.initialization_tab.stop_all_clicked.connect(self.stop_all_requested.emit)
        self.initialization_tab.profile_clicked.connect(
            lambda name: self.profile_selected.emit(self.device_id, name))
        self.initialization_tab.profile_added.connect(
            lambda name: self.profile_added.emit(self.device_id, name))
        self.initialization_tab.profile_deleted.connect(
            lambda name: self.profile_deleted.emit(self.device_id, name))
        self.initialization_tab.server_changed.connect(
            lambda server: self.server_changed.emit(self.device_id, server)
        )

        self.initialization_tab.active_clicked.connect(
            lambda want: self.active_requested.emit(self.device_id, want))
        self.initialization_tab.reset_info_clicked.connect(
            lambda: self.reset_info_requested.emit(self.device_id))
        self.initialization_tab.civilization_changed.connect(
            lambda civilization: self.civilization_changed.emit(self.device_id, civilization)
        )

    def showEvent(self, event):
        super().showEvent(event)
        if not self._shown_once:
            self._shown_once = True
            self._background_timer.start(50)   # lần hiện đầu xong mới dựng nốt các tab còn lại, từng tab một

    def __getattr__(self, name):
        """Tab chưa dựng (join_monster_war_tab, event_tab...) được dựng ngay khi có người dùng tới."""
        lazy = self.__dict__.get("_lazy")
        if lazy:
            for title, (attr, _factory) in list(lazy.items()):
                if attr == name:
                    self._build_tab(title)
                    return self.__dict__[name]
        raise AttributeError(name)

    def _build_tab_at(self, index: int):
        if index >= 0:
            self._build_tab(self.tabs.tabText(index))

    def _build_next_tab(self):
        if self._lazy:
            self._build_tab(next(iter(self._lazy)))
        if self._lazy:
            self._background_timer.start(30)

    def ensure_all_tabs(self):
        while self._lazy:
            self._build_tab(next(iter(self._lazy)))

    def _build_tab(self, title: str):
        """Dựng tab `title` (nếu chưa), thay trang trống, áp cấu hình đang chờ rồi lưu lại cấu hình mới của tab."""
        entry = self._lazy.pop(title, None)
        if entry is None:
            return
        attr, factory = entry
        index = next(i for i in range(self.tabs.count()) if self.tabs.tabText(i) == title)
        widget = factory()
        setattr(self, attr, widget)
        current = self.tabs.currentIndex()
        self.tabs.blockSignals(True)
        old = self.tabs.widget(index)
        self.tabs.removeTab(index)
        self.tabs.insertTab(index, widget, title)
        self.tabs.setCurrentIndex(current)
        self.tabs.blockSignals(False)
        self._sync_tab_buttons(current)
        old.deleteLater()
        self._wire_tab(widget, title)
        if title in self._pending_settings:
            widget.set_settings(self._pending_settings.pop(title))
        if title == "Event" and self._event_done is not None:
            widget.set_event_times(self._event_done)
        # Ghi lại cấu hình theo code hiện tại (tab / nhiệm vụ mới, level / day đổi trong event.py; máy mới thì mặc định).
        self.tab_settings_changed.emit(self.device_id, {title: widget.get_settings()})

    def _wire_tab(self, widget: QWidget, title: str):
        self._connect_tab(widget, title)
        if title == "Daily Activities":
            widget.reset_progress_clicked.connect(lambda: self.reset_progress_requested.emit(self.device_id, False))
        elif title == "Event":
            widget.reset_progress_clicked.connect(lambda: self.reset_progress_requested.emit(self.device_id, True))
        elif title == "Find Boss":
            widget.auto_clicked.connect(lambda: self.auto_angles_requested.emit(self.device_id))
        elif title == "Recruit General":
            widget.generals.start_background_build()

    def apply_craft_done(self, item_id: str) -> dict:
        """Một trang bị vừa chế tạo xong: trừ 1 số lượng ở tab Craft (về 0 thì bỏ tích). Trả cấu hình mới của tab để lưu DB; tab chưa dựng thì sửa cấu hình đang chờ."""
        if "Craft" in self._lazy:
            data = self._pending_settings.setdefault("Craft", {})
            subtract_craft_item(data, item_id)
            return data
        self.craft_tab.craft_done(item_id)
        return self.craft_tab.get_settings()

    def set_event_times(self, daily_done: dict):
        """Tiêu đề group của tab Event (thời gian còn lại); tab chưa dựng thì áp khi dựng xong."""
        self._event_done = daily_done
        if "Event" not in self._lazy:
            self.event_tab.set_event_times(daily_done)

    def _add_tab_button(self, title: str, index: int):
        """Nút trên hàng tab cho tab `index`: bấm thì mở tab đó."""
        button = QPushButton(title)
        button.setObjectName("TabButton")
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)
        self.tab_buttons.addButton(button, index)
        self.tab_flow.addWidget(button)
        button.clicked.connect(lambda _checked=False, i=index: self.tabs.setCurrentIndex(i))
        self._sync_tab_buttons(self.tabs.currentIndex())

    def _sync_tab_buttons(self, index: int):
        button = self.tab_buttons.button(index)
        if button is not None:
            button.setChecked(True)

    def _add_tab(self, widget: QWidget, title: str):
        self._add_tab_button(title, self.tabs.addTab(widget, title))
        self._connect_tab(widget, title)

    def _connect_tab(self, widget: QWidget, title: str):
        widget.setProperty("tab_title", title)
        widget.apply_all_clicked.connect(self._on_apply_all)
        if hasattr(widget, "settings_changed"):
            widget.settings_changed.connect(
                lambda: self.tab_settings_changed.emit(self.device_id,
                                                       {title: widget.get_settings()})
            )
        self._autosave_on_edit(widget, title)

    def _autosave_on_edit(self, widget: QWidget, title: str):
        """Nhiều tab (Join Monster War, Alliance Capacity, Black Market...) không tự phát `settings_changed`:
        nối mọi ô tích / combo / số / ô chữ người dùng sửa tới một lần lưu (gộp 300 ms). Chỉ dùng tín hiệu do
        người dùng gây ra nên set_settings() bằng code không kích hoạt lưu."""
        timer = QTimer(widget)
        timer.setSingleShot(True)
        timer.setInterval(300)
        timer.timeout.connect(
            lambda: self.tab_settings_changed.emit(self.device_id, {title: widget.get_settings()}))
        for box in widget.findChildren(QAbstractButton):
            if isinstance(box, (QCheckBox, QRadioButton)):
                box.clicked.connect(timer.start)
        for combo in widget.findChildren(QComboBox):
            combo.activated.connect(timer.start)
        for spin in widget.findChildren(QAbstractSpinBox):
            spin.editingFinished.connect(timer.start)
        for edit in widget.findChildren(QLineEdit):
            edit.editingFinished.connect(timer.start)

    def _on_apply_all(self):
        # Every tab's Apply ALL copies this device's whole config (all
        # tabs) onto every other device. The device id and server are never copied.
        self.apply_all_requested.emit(self.device_id, self.shareable_settings())

    def shareable_settings(self) -> dict:
        """Cấu hình mọi tab trừ phần riêng từng máy (device id, server): dùng cho Apply ALL và hồ sơ."""
        settings = self.get_settings()
        settings["Initialization"] = {
            k: v for k, v in settings["Initialization"].items() if k not in ("device_id", "server")
        }
        return settings

    def set_profiles(self, names: list, active: str = ""):
        """Hàng nút hồ sơ trong tab Initialization (không gồm default; `active` được tích)."""
        self.initialization_tab.set_profiles(names, active)

    def append_log(self, message: str):
        self.logs_tab.append(message)

    def append_history(self, created_at: str, message: str):
        self.logs_tab.append_history(created_at, message)

    def set_running(self, running: bool):
        self.initialization_tab.set_running(running)

    def set_active(self, active: bool):
        self.initialization_tab.set_active(active)

    def set_run_counts(self, running: int, total: int):
        """Hai nút Start All / Stop All trong tab Initialization."""
        self.initialization_tab.set_run_counts(running, total)

    def get_settings(self) -> dict:
        """Collect settings from every tab into one dict, keyed by tab title."""
        self.ensure_all_tabs()
        return {self.tabs.tabText(i): self.tabs.widget(i).get_settings()
                for i in range(self.tabs.count()) if self.tabs.widget(i) is not self.logs_tab}

    def set_settings(self, data: dict):
        for i in range(self.tabs.count()):
            title = self.tabs.tabText(i)
            if title in data and self.tabs.widget(i) is not self.logs_tab:
                if title in self._lazy:
                    self._pending_settings[title] = data[title]   # áp khi tab được dựng
                else:
                    self.tabs.widget(i).set_settings(data[title])
