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
from PyQt5.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget,
)

from bot.common import GAME_PACKAGE

from bot.worker import BotManager

import licensing
from database import DEFAULT_PROFILE, Database, is_event_key
from ui import DeviceView, HomeView, Sidebar
from ui import theme
from ui.activation_dialog import ActivationDialog
from ui.workers import LicenseWorker
from ui.tabs.constants import PROFILE_MAX
from ui.tabs.logs_tab import SHOW_SECONDS


CONTACT_HINT = f"Contact: {licensing.ADMIN_CONTACT}" if licensing.ADMIN_CONTACT else ""
LICENSE_CHECK_MS = 60 * 60 * 1000   # re-check the activation code with the server every hour


def ensure_license() -> tuple[bool, str | None]:
    """(may start, notice). A machine that already has a license starts when the server answers; the notice
    (revoked, expired...) is shown as a popup and the license file is never deleted. When the server cannot be
    reached the app offers Retry or Quit. The code dialog only appears when there is no license yet: one
    machine uses one code, so there is no way to enter another one from the app."""
    if licensing.stored_code():
        while True:
            try:
                licensing.verify()
                return True, None
            except licensing.LicenseError as e:
                return True, str(e)
            except licensing.OfflineError:
                box = QMessageBox(
                    QMessageBox.Critical, "Connection error",
                    "Unable to load information from the server.\nPlease check your internet connection and try again.")
                retry = box.addButton("Retry", QMessageBox.AcceptRole)
                box.addButton("Quit", QMessageBox.RejectRole)   # also what the window's X / Esc does
                box.setDefaultButton(retry)
                box.exec()
                if box.clickedButton() is not retry:
                    return False, None
    return ActivationDialog().exec() == QDialog.Accepted, None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evony Control App")
        self.db = Database()
        self.resize(1329, 708)
        self._center_on_screen()

        # A banner on top (shown while the license is not valid) above the whole UI, which is disabled then.
        outer = QWidget()
        self.setCentralWidget(outer)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        self.license_banner = QLabel()
        self.license_banner.setWordWrap(True)
        self.license_banner.setStyleSheet("background: #d32f2f; color: white; font-weight: bold; padding: 8px 12px;")
        self.license_banner.hide()
        outer_layout.addWidget(self.license_banner)
        self.content = QWidget()
        outer_layout.addWidget(self.content, 1)
        root = QHBoxLayout(self.content)
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

        # Tab Event hiện thời gian còn lại của event ở tiêu đề group: đọc mốc reset bot đã lưu trong DB (daily_done) mỗi phút.
        self._event_timer = QTimer(self)
        self._event_timer.setInterval(60_000)
        self._event_timer.timeout.connect(self._refresh_event_times)
        self._event_timer.start()

        # Activation code: re-checked with the server hourly; revoked / expired -> stop the bots and quit.
        self._license_worker: LicenseWorker | None = None
        self._license_notice: str | None = None
        self._license_timer = QTimer(self)
        self._license_timer.setInterval(LICENSE_CHECK_MS)
        self._license_timer.timeout.connect(self._check_license)
        self._license_timer.start()

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
        self.bots.daily_task_cleared.connect(lambda serial, task: self.db.mark_daily_task_done(serial, task, False))
        self.bots.daily_task_done.connect(lambda serial, _task: self._refresh_event_times(serial))
        self.bots.bubble_found.connect(self._on_bubble_found)
        self.bots.civilization_found.connect(self._on_civilization_found)
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

    def _check_license(self):
        if self._license_worker is not None and self._license_worker.isRunning():
            return
        self._license_worker = LicenseWorker("verify", parent=self)
        self._license_worker.done.connect(lambda: self.notify_license(None))
        self._license_worker.refused.connect(self.notify_license)
        # Offline is fine while the last signed answer is inside the grace period.
        self._license_worker.offline.connect(lambda _m: self.notify_license(licensing.check_local()))
        self._license_worker.start()

    def notify_license(self, notice: str | None):
        """License problem (revoked, expired...): stop the bots, lock the whole UI behind a red banner and show a popup
        (once per notice). The window stays open and the license file untouched; a valid answer unlocks it again."""
        locked = bool(notice)
        self.content.setEnabled(not locked)
        self.license_banner.setVisible(locked)
        if not locked:
            self._license_notice = None
            return
        self.license_banner.setText(f"{notice} {CONTACT_HINT}".strip())
        self.bots.stop_all()
        if notice != self._license_notice:
            self._license_notice = notice
            QMessageBox.warning(self, "Activation", f"{notice}\n{CONTACT_HINT}".strip())

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
        view.civilization_changed.connect(self._on_civilization_changed)
        view.reset_progress_requested.connect(self._on_reset_progress)
        view.reset_info_requested.connect(self._on_reset_info)
        view.tab_settings_changed.connect(self.db.save_settings)
        view.profile_selected.connect(self._on_profile_selected)
        view.profile_added.connect(self._on_profile_added)
        view.profile_deleted.connect(self._on_profile_deleted)
        view.tabs.currentChanged.connect(self._on_tab_changed)

        # New device -> store its default config; known device -> restore it.
        if self.db.add_device(device_id):
            self.db.save_settings(device_id, view.get_settings())
        else:
            view.set_settings(self.db.load_settings(device_id))
            # Ghi lại tab Event theo event.py hiện tại (thêm nhiệm vụ mới,
            # cập nhật level / day khi file được sửa).
            self.db.save_settings(device_id, {"Event": view.event_tab.get_settings()})
        self._refresh_profiles(device_id, view)
        self.home_view.update_device(
            device_id, server=view.initialization_tab.get_settings()["server"]
        )
        # Tab Logs chỉ hiện log trong SHOW_SECONDS gần nhất; DB vẫn giữ đủ.
        since = (datetime.now() - timedelta(seconds=SHOW_SECONDS)).isoformat(timespec="seconds")
        for created_at, message in self.db.load_logs(device_id, since):
            view.append_history(created_at, message)

        self.device_views[device_id] = view
        self._refresh_event_times(device_id)
        view.set_run_counts(*self._run_counts())
        self.stack.addWidget(view)
        self.sidebar.add_device(device_id)

    def _refresh_event_times(self, serial: str | None = None):
        """Cập nhật tiêu đề group của tab Event (thời gian còn lại của event) cho một thiết bị / mọi thiết bị."""
        for device_id, view in self.device_views.items():
            if serial is None or device_id == serial:
                view.event_tab.set_event_times(self.db.daily_done(device_id))

    def _show_device(self, device_id: str):
        view = self.device_views.get(device_id)
        self._refresh_event_times(device_id)
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

    def _refresh_profiles(self, device_id: str, view: DeviceView):
        """Hàng nút hồ sơ của thiết bị: các hồ sơ đã tạo (không gồm default) + hồ sơ đang dùng."""
        view.set_profiles(self.db.list_profiles(device_id), self.db.active_profile(device_id))

    def _switch_profile(self, device_id: str, view: DeviceView, target: str):
        """Chụp cấu hình đang dùng vào hồ sơ hiện tại, rồi nạp hồ sơ `target` lên máy (giữ nguyên device id, server...)
        và lưu thành cấu hình đang dùng."""
        self.db.save_profile(device_id, self.db.active_profile(device_id), view.shareable_settings())
        settings = self.db.load_profile(device_id, target)
        if settings:
            view.set_settings(settings)
            self.db.save_settings(device_id, view.get_settings())
        self.db.set_active_profile(device_id, target)

    def _on_profile_selected(self, device_id: str, name: str):
        """Bấm nút hồ sơ: chuyển sang nó. Bấm lại hồ sơ đang chọn thì giữ nguyên (nút vẽ lại để vẫn tích)."""
        view = self.device_views.get(device_id)
        if view is None:
            return
        if name != self.db.active_profile(device_id):
            self._switch_profile(device_id, view, name)
        self._refresh_profiles(device_id, view)

    def _on_profile_added(self, device_id: str, name: str):
        """Nút "+": hồ sơ mới = bản sao cấu hình hiện tại, và máy chuyển sang dùng nó."""
        view = self.device_views.get(device_id)
        if view is None or len(self.db.list_profiles(device_id)) >= PROFILE_MAX:
            return
        self.db.save_profile(device_id, self.db.active_profile(device_id), view.shareable_settings())
        self.db.save_profile(device_id, name, view.shareable_settings())
        self.db.set_active_profile(device_id, name)
        self._refresh_profiles(device_id, view)

    def _on_profile_deleted(self, device_id: str, name: str):
        view = self.device_views.get(device_id)
        if view is None:
            return
        if self.db.active_profile(device_id) == name:
            # Xoá hồ sơ đang dùng: chuyển sang hồ sơ đầu tiên còn lại (không còn hồ sơ nào thì về default).
            remaining = [n for n in self.db.list_profiles(device_id) if n != name]
            self._switch_profile(device_id, view, remaining[0] if remaining else DEFAULT_PROFILE)
        self.db.delete_profile(device_id, name)
        self._refresh_profiles(device_id, view)

    def closeEvent(self, event):
        self._register_timer.stop()
        self._license_timer.stop()
        if self._license_worker is not None:
            self._license_worker.wait()
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

    def _on_reset_info(self, device_id: str):
        """Nút Reset info: đưa bubble, server, nền văn minh, route của máy về trống (DB và giao diện)."""
        self._on_server_changed(device_id, "")
        self.db.set_bubble_until(device_id, "")
        self.db.set_civilization(device_id, 0)
        self.db.set_city_map(device_id, "")
        view = self.device_views.get(device_id)
        if view is not None:
            view.initialization_tab.set_settings({"server": "", "bubble_until": "", "civilization": 0})

    def _on_reset_progress(self, device_id: str, event: bool):
        """Nút Reset progress: xoá dấu "đã làm" (DB và worker đang chạy) để bot làm lại các nhiệm vụ của tab."""
        self.db.clear_daily_done(device_id, event)
        self.bots.clear_daily_done(device_id, lambda key: "_cycle_reset_" not in key and is_event_key(key) == event)

    def _on_civilization_changed(self, device_id: str, civilization: int):
        """Người dùng đổi nền văn minh -> lưu DB và xoá route (bản đồ thành) cũ về null để bot quét lại."""
        self.db.set_civilization(device_id, civilization)
        self.db.set_city_map(device_id, "")

    def _on_civilization_found(self, device_id: str, civilization: int):
        """Bot vừa tự xếp nền văn minh -> lưu DB và hiện lên tab Initialization."""
        self.db.set_civilization(device_id, civilization)
        view = self.device_views.get(device_id)
        if view is not None:
            view.initialization_tab.set_civilization(civilization)

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
    # The installed app runs as EvonyBot.exe (renamed pythonw.exe); give it its own taskbar
    # identity (matches the shortcut's AppUserModelID) and icon instead
    # of Python's.
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("EvonyBot")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "Images" / "icon.ico")))
    theme.apply(app)
    may_start, notice = ensure_license()
    if not may_start:
        sys.exit(0)
    window = MainWindow()
    window.show()
    if notice:   # the app opens normally; the popup comes right after the window shows
        QTimer.singleShot(0, lambda: window.notify_license(notice))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
