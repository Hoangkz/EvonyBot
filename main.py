"""
main.py — EvonyBot entry point.

Python/PyQt5 rewrite of the original WinForms `Form3`: a left sidebar
listing connected devices (was `panelistbutton`) next to a content
area (was `panelData`) that shows either the home/welcome screen or
the selected device's tabbed control panel.
"""
import ctypes
import os
import platform
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

# adb server do adbutils mở (adb 36.x) mặc định bật mDNS: mở UDP 5353 trên mọi mạng -> Windows Firewall hỏi quyền
# adb.exe trên máy mới. Bot chỉ nối giả lập local (127.0.0.1:port) nên tắt mDNS; đặt trước khi adb server được mở.
os.environ.setdefault("ADB_MDNS", "0")

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QHBoxLayout

from bot.common import GAME_PACKAGE

from bot.worker import BotManager

from database import Database
from ui import DeviceView, HomeView, Sidebar
from ui import theme
from ui.tabs.logs_tab import SHOW_SECONDS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evony Control App")
        self.db = Database()
        self.resize(1329, 708)
        self._center_on_screen()

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.home_view = HomeView()
        self.stack.addWidget(self.home_view)
        self.stack.setCurrentWidget(self.home_view)

        self.device_views: dict[str, DeviceView] = {}
        # Building a DeviceView is heavy (8 designer tabs), so new devices
        # are registered one per event-loop tick to keep the UI responsive.
        self._pending_devices: list[str] = []
        self._register_timer = QTimer(self)
        self._register_timer.setInterval(0)
        self._register_timer.timeout.connect(self._register_next_device)

        self.bots = BotManager(self)
        self.bots.activity_changed.connect(
            lambda serial, activity: self.home_view.update_device(serial, activity=activity)
        )
        self.bots.status_changed.connect(
            lambda serial, status: self.home_view.update_device(serial, status=status)
        )
        self.bots.running_changed.connect(self._on_bot_running_changed)
        self.bots.server_found.connect(self._on_server_found)
        # Giờ reset server chung mọi thiết bị (bảng settings, mặc định 14:00): người dùng chọn ở màn
        # Home; đổi là lưu DB và các worker đang chạy dùng giá trị mới ngay.
        self.bots.server_clock.set(self.db.server_time())
        self.home_view.set_reset_time(self.bots.server_clock.value)
        self.home_view.reset_time_changed.connect(self._on_reset_time_changed)
        # "Auto Times Out" chung mọi thiết bị (bảng settings): nạp lại giá trị đã lưu; đổi là lưu DB và
        # các worker đang chạy dùng ngay (tới giờ thì đóng game, ưu tiên ngay sau Bubble).
        self.home_view.set_auto_timeout(self.db.auto_timeout())
        self.bots.auto_timeout_minutes = self.home_view.auto_timeout_minutes
        self.home_view.auto_timeout_changed.connect(self._on_auto_timeout_changed)
        self.bots.daily_task_done.connect(self.db.mark_daily_task_done)
        self.bots.bubble_found.connect(self._on_bubble_found)
        self.bots.civilization_found.connect(self.db.set_civilization)
        self.bots.city_map_found.connect(self.db.set_city_map)
        self.bots.bubble_disabled.connect(self._on_bubble_disabled)
        self.bots.log_message.connect(self._on_log_message)
        self.bots.history.connect(self._on_history)
        # Sub-tab index kept across devices, so switching device stays on
        # the same tab instead of jumping back to Initialization.
        self._current_tab_index = 0

        self.sidebar.home_selected.connect(lambda: self.stack.setCurrentWidget(self.home_view))
        self.sidebar.device_selected.connect(self._show_device)
        self.home_view.devices_loaded.connect(self._on_devices_loaded)
        self.home_view.start_all_requested.connect(self._on_start_all_requested)
        self.home_view.stop_all_requested.connect(self._on_stop_all_requested)
        self.home_view.exit_all_requested.connect(self._on_exit_all_requested)

    def _center_on_screen(self):
        frame = self.frameGeometry()
        frame.moveCenter(self.screen().availableGeometry().center())
        self.move(frame.topLeft())

    def _on_devices_loaded(self, serials: list):
        # Start over: drop every old device (stops its bot), then re-add
        # the scanned ones from scratch.
        self._register_timer.stop()
        for device_id in list(self.device_views):
            self._unregister_device(device_id)
        self._pending_devices = list(serials)
        if self._pending_devices:
            self._register_timer.start()
        self._refresh_run_counts()

    def _register_next_device(self):
        if self._pending_devices:
            self._register_device(self._pending_devices.pop(0))
        # Làm mới số liệu sau mỗi thiết bị đăng ký để 2 nút Start/Stop All
        # (màn Home và tab Initialization) phản ánh đúng số máy đã thấy.
        self._refresh_run_counts()
        if not self._pending_devices:
            self._register_timer.stop()

    def _unregister_device(self, device_id: str):
        self.sidebar.remove_device(device_id)
        view = self.device_views.pop(device_id, None)
        if view is not None:
            if self.stack.currentWidget() is view:
                self.stack.setCurrentWidget(self.home_view)
                self.sidebar.select_home()
            self.stack.removeWidget(view)
            view.deleteLater()
        self.bots.stop(device_id)

    def _register_device(self, device_id: str):
        if device_id in self.device_views:
            return
        view = DeviceView(device_id)
        view.start_requested.connect(self._on_start_requested)
        view.start_all_requested.connect(self._on_start_all_requested)
        view.stop_all_requested.connect(self._on_stop_all_requested)
        view.apply_all_requested.connect(self._on_apply_all_requested)
        view.server_changed.connect(self._on_server_changed)
        view.tab_settings_changed.connect(self.db.save_settings)
        view.tabs.currentChanged.connect(self._on_tab_changed)

        # New device -> store its default config; known device -> restore it.
        if self.db.add_device(device_id):
            self.db.save_settings(device_id, view.get_settings())
        else:
            view.set_settings(self.db.load_settings(device_id))
            # Ghi lại tab Event theo event.json hiện tại (thêm nhiệm vụ mới,
            # cập nhật level / day khi file được sửa).
            self.db.save_settings(device_id, {"Event": view.event_tab.get_settings()})
        self.home_view.update_device(
            device_id, server=view.initialization_tab.get_settings()["server"]
        )
        # Tab Logs chỉ hiện log trong SHOW_SECONDS gần nhất; DB vẫn giữ đủ.
        since = (datetime.now() - timedelta(seconds=SHOW_SECONDS)).isoformat(timespec="seconds")
        for created_at, message in self.db.load_logs(device_id, since):
            view.append_history(created_at, message)

        self.device_views[device_id] = view
        view.set_run_counts(*self._run_counts())
        self.stack.addWidget(view)
        self.sidebar.add_device(device_id)

    def _show_device(self, device_id: str):
        view = self.device_views.get(device_id)
        if view is not None:
            view.tabs.setCurrentIndex(self._current_tab_index)
            self.stack.setCurrentWidget(view)

    def _on_tab_changed(self, index: int):
        if index >= 0:
            self._current_tab_index = index

    def _on_apply_all_requested(self, source_id: str, settings: dict):
        """Copy the active device's config onto every other device."""
        for device_id, view in self.device_views.items():
            if device_id != source_id:
                view.set_settings(settings)
        # One transaction for every device: a commit per device (30+
        # fsyncs) froze the UI for seconds.
        self.db.save_many_settings(
            {device_id: view.get_settings() for device_id, view in self.device_views.items()}
        )

    def closeEvent(self, event):
        self._register_timer.stop()
        self.bots.stop_all(wait=True)
        self.db.close()
        super().closeEvent(event)

    def _on_start_requested(self, device_id: str):
        """Start button toggles: starts the device's bot, or stops it if running."""
        if self.bots.is_running(device_id):
            self.bots.stop(device_id)
        else:
            self._start_bot(device_id)

    def _on_start_all_requested(self):
        """Start All (màn Home): chạy những thiết bị chưa hoạt động;
        thiết bị đang chạy được giữ nguyên."""
        for device_id in self.device_views:
            if not self.bots.is_running(device_id):
                self._start_bot(device_id)

    def _on_stop_all_requested(self):
        """Stop All (màn Home và tab Initialization): dừng mọi bot đang chạy."""
        self.bots.stop_all()

    def _on_reset_time_changed(self, server_time: str):
        self.db.set_server_time(server_time)
        self.bots.server_clock.set(server_time)

    def _on_auto_timeout_changed(self, minutes: str):
        self.db.set_auto_timeout(minutes)
        self.bots.auto_timeout_minutes = int(minutes)

    def _run_counts(self) -> tuple[int, int]:
        """(số bot đang chạy, tổng số thiết bị đã đăng ký)."""
        total = len(self.device_views)
        running = sum(1 for d in self.device_views if self.bots.is_running(d))
        return running, total

    def _refresh_run_counts(self):
        """Cập nhật số liệu (đang chạy, tổng thiết bị) cho màn Home và tab
        Initialization của mọi thiết bị -> 2 nút Start All / Stop All tự bật/tắt."""
        counts = self._run_counts()
        self.home_view.set_run_counts(*counts)
        for view in self.device_views.values():
            view.set_run_counts(*counts)

    def _start_bot(self, device_id: str):
        view = self.device_views.get(device_id)
        if view is None:
            return
        settings = view.get_settings()
        # Đây là dữ liệu riêng của thiết bị trong DB, không phải cấu hình Apply ALL.
        saved = self.db.load_settings(device_id)
        init = settings.setdefault("Initialization", {})
        # Bubble còn hạn trong DB thì bot không cần vào game kiểm tra lại.
        init["bubble_until"] = saved.get("Initialization", {}).get("bubble_until") or ""
        # Nền văn minh bot đã tự xếp (ảnh công trình học chung theo nền văn minh).
        init["civilization"] = saved.get("Initialization", {}).get("civilization")
        self.bots.start(
            device_id,
            view.initialization_tab.selected_activities(),
            settings,
            daily_done=self.db.daily_done(device_id),
        )

    def _on_bot_running_changed(self, device_id: str, running: bool):
        view = self.device_views.get(device_id)
        if view is not None:
            view.set_running(running)
        self._refresh_run_counts()

    def _on_server_changed(self, device_id: str, server: str):
        """Server của thiết bị đổi -> lưu DB và cập nhật cột Server ở Home."""
        self.db.set_server(device_id, server)
        self.home_view.update_device(device_id, server=server)

    def _on_server_found(self, device_id: str, server: str):
        """Bot vừa đọc được server trong game -> lưu DB và hiện lên tab Initialization."""
        self._on_server_changed(device_id, server)
        view = self.device_views.get(device_id)
        if view is not None:
            view.initialization_tab.set_settings({"server": server})

    def _on_bubble_found(self, device_id: str, seconds: int):
        """Bot vừa đọc / gia hạn bubble -> lưu DB và đếm ngược ở tab Initialization."""
        until = datetime.now() + timedelta(seconds=seconds) if seconds else None
        self.db.set_bubble_until(device_id, until.isoformat(timespec="seconds") if until else "")
        view = self.device_views.get(device_id)
        if view is not None:
            view.initialization_tab.set_bubble_remaining(seconds or None)

    def _on_bubble_disabled(self, device_id: str):
        """Không đủ kim cương mua bubble -> bỏ tích Bubble (tự lưu qua settings_changed)."""
        view = self.device_views.get(device_id)
        if view is not None:
            view.initialization_tab.set_settings({"bubble": False})

    def _on_log_message(self, device_id: str, message: str):
        """Dòng log của bot -> tab Logs của thiết bị đó."""
        view = self.device_views.get(device_id)
        if view is not None:
            view.append_log(message)

    def _on_history(self, device_id: str, message: str):
        """Sự kiện của bot (bắt đầu / xong / dừng nhiệm vụ, lỗi...) -> lưu DB (ghi nền, không chờ)
        và hiện ở tab Logs > History."""
        created_at = datetime.now().isoformat(timespec="seconds")
        self.db.add_log(device_id, message, created_at)
        view = self.device_views.get(device_id)
        if view is not None:
            view.append_history(created_at, message)

    def _on_exit_all_requested(self):
        """Exit All: đóng game (force-stop) trên mọi thiết bị. Gọi ADB trên thread nền để không đơ UI."""
        def close_games(serials):
            import adbutils
            for serial in serials:
                try:
                    adbutils.adb.device(serial=serial).shell(f"am force-stop {GAME_PACKAGE}")
                except Exception as e:
                    print(f"[{serial}] Exit All: không đóng được game: {e}")
        threading.Thread(target=close_games, args=(list(self.device_views),),
                         name="exit-all", daemon=True).start()


def main():
    # adbutils calls platform.system() on every socket. On Windows the
    # first call runs a WMI query that crashes (0x800703e5) when many ADB
    # connect threads hit it at once; call it here so the result is cached.
    platform.system()
    # Qt6 enables high-DPI scaling by default; Qt5 needs it opted in
    # (must be set before the QApplication is created).
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    # The installed app runs as pythonw.exe; give it its own taskbar
    # identity (matches the shortcut's AppUserModelID) and icon instead
    # of Python's.
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("EvonyBot")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "Images" / "icon.ico")))
    theme.apply(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
