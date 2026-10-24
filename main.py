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
import random
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
    QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QProgressBar, QStackedWidget,
    QVBoxLayout, QWidget,
)

from bot.activities.find_boss.angles import split_angles
from bot.activities.find_boss.constants import END_KEY, START_KEY
from bot.common import GAME_PACKAGE

from bot.worker import BotManager

import licensing
from database import DEFAULT_PROFILE, TAB_COLUMNS, Database, is_event_key
from ui import DeviceView, HomeView, Sidebar
from ui.device_view import subtract_craft_item
from ui import theme
from ui.activation_dialog import ActivationDialog
from ui.workers import LicenseWorker
from ui.tabs.constants import PROFILE_MAX
from ui.tabs.logs_tab import SHOW_SECONDS


CONTACT_HINT = f"Contact: {licensing.ADMIN_CONTACT}" if licensing.ADMIN_CONTACT else ""
# Re-check the activation code with the server at a random gap in this range (not a fixed period, so nobody can
# time their cheating around the check).
LICENSE_CHECK_MIN_MS = 10 * 60 * 1000
LICENSE_CHECK_MAX_MS = 60 * 60 * 1000


def next_license_check_ms() -> int:
    return random.randint(LICENSE_CHECK_MIN_MS, LICENSE_CHECK_MAX_MS)


def ensure_license() -> bool:
    """May the app start. A machine that already has a license opens right away; the window then checks it with
    the server in the background (MainWindow._check_license(startup=True)). The code dialog only appears when there
    is no license yet: one machine uses one code, so there is no way to enter another one from the app."""
    if licensing.stored_code():
        return True
    return ActivationDialog().exec() == QDialog.Accepted


def ask_retry_offline(parent=None) -> bool:
    """Server không trả lời: hỏi Retry (True) hay Quit (False)."""
    box = QMessageBox(
        QMessageBox.Critical, "Connection error",
        "Unable to load information from the server.\nPlease check your internet connection and try again.", parent=parent)
    retry = box.addButton("Retry", QMessageBox.AcceptRole)
    box.addButton("Quit", QMessageBox.RejectRole)   # also what the window's X / Esc does
    box.setDefaultButton(retry)
    box.exec()
    return box.clickedButton() is retry


PREBUILD_IDLE_SECONDS = 1.0   # chỉ dựng sẵn giao diện máy khi người dùng đã ngừng thao tác chừng này giây


def _idle_seconds() -> float:
    """Số giây từ lần cuối người dùng thao tác chuột / bàn phím (Windows); nơi khác coi là đã rảnh."""
    if os.name != "nt":
        return PREBUILD_IDLE_SECONDS
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return PREBUILD_IDLE_SECONDS
    return max(0.0, (ctypes.windll.kernel32.GetTickCount() - info.dwTime) / 1000.0)


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
        # Khung loading nổi giữa cửa sổ trong lúc đang hỏi server (xem _check_license): giao diện bị khoá cho tới khi
        # có kết quả. Không nằm trong layout, _place_license_checking đặt nó vào giữa.
        self.license_checking = QFrame(outer)
        self.license_checking.setStyleSheet(
            "QFrame { background: #3a63f2; border-radius: 8px; }"
            " QLabel { color: white; font-weight: bold; background: transparent; }")
        checking_layout = QVBoxLayout(self.license_checking)
        checking_layout.setContentsMargins(24, 16, 24, 16)
        checking_label = QLabel("Checking license, please wait...")
        checking_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        checking_layout.addWidget(checking_label)
        checking_bar = QProgressBar()
        checking_bar.setRange(0, 0)   # chạy qua lại liên tục (không biết bao lâu)
        checking_bar.setTextVisible(False)
        checking_bar.setFixedHeight(8)
        checking_layout.addWidget(checking_bar)
        self.license_checking.hide()
        self._startup_check = False    # lần kiểm tra đang chạy là lần lúc mở app
        self._startup_offline = False  # lần đó không tới được server -> hỏi Retry / Quit
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
        self._active: dict[str, bool] = {}        # serial -> đang kích hoạt (nút Active/Inactive ở Home)
        self._active_flags: dict[str, bool] = {}
        self._saved_active: dict[str, bool] = {}
        # Dựng DeviceView rất nặng (~3 s/máy với theme), nên chỉ dựng khi cần (mở máy, Start, Apply ALL...);
        # danh sách máy đã đăng ký nằm ở _device_ids, device_views chỉ chứa máy đã dựng.
        self._device_ids: list[str] = []
        self._new_devices: set[str] = set()   # máy vừa thêm vào DB, chưa có cấu hình lưu
        self._register_timer = QTimer(self)
        self._register_timer.setInterval(0)
        self._register_timer.timeout.connect(self._register_next_device)
        # Start All: mỗi máy chưa dựng phải dựng DeviceView + đủ tab (~3 s) mới lấy được cấu hình; dựng liền 30 máy
        # trong một lần bấm làm app "Not Responding". Nên xếp hàng, mỗi lượt event loop chỉ start một máy.
        self._start_queue: list[str] = []
        self._start_timer = QTimer(self)
        self._start_timer.setInterval(0)
        self._start_timer.timeout.connect(self._start_next_queued)

        # Tab Event hiện thời gian còn lại của event ở tiêu đề group: đọc mốc reset bot đã lưu trong DB (daily_done) mỗi phút.
        self._event_timer = QTimer(self)
        self._event_timer.setInterval(60_000)
        self._event_timer.timeout.connect(self._refresh_event_times)
        self._event_timer.start()

        # Activation code: re-checked with the server hourly; revoked / expired -> stop the bots and quit.
        self._license_worker: LicenseWorker | None = None
        self._license_notice: str | None = None
        self._license_timer = QTimer(self)
        self._license_timer.setSingleShot(True)
        self._license_timer.timeout.connect(self._check_license)
        self._license_timer.start(next_license_check_ms())

        self.bots = BotManager(self)
        self.bots.max_running = licensing.max_devices()
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
        self.bots.craft_done.connect(self._on_craft_done)
        self.bots.log_message.connect(self._on_log_message)
        self.bots.history.connect(self._on_history)
        # Sub-tab index kept across devices, so switching device stays on
        # the same tab instead of jumping back to Initialization.
        self._current_tab_index = 0

        self.sidebar.home_selected.connect(lambda: self.stack.setCurrentWidget(self.home_view))
        self.sidebar.device_selected.connect(self._show_device)
        self.home_view.devices_loaded.connect(self._on_devices_loaded)
        self.home_view.active_toggled.connect(self._on_active_toggled)
        self.home_view.start_all_requested.connect(self._on_start_all_requested)
        self.home_view.stop_all_requested.connect(self._on_stop_all_requested)
        self.home_view.exit_all_requested.connect(self._on_exit_all_requested)
        self.home_view.active_all_requested.connect(self._on_active_all_requested)

    def _check_license(self, startup: bool = False):
        """Hỏi server giấy phép trên thread nền. `startup`: lần lúc mở app (app đã mở sẵn, không chờ) — không tới
        được server thì hỏi Retry / Quit như trước; các lần định kỳ sau thì dựa vào hạn offline (check_local)."""
        self._license_timer.start(next_license_check_ms())   # next check at a new random gap
        if self._license_worker is not None and self._license_worker.isRunning():
            return
        self._startup_check = startup
        self._startup_offline = False
        # Lúc mở app chưa có bot nào chạy: không gửi running / peak (như verify() trước đây).
        self._license_worker = LicenseWorker(
            "verify", parent=self,
            running=None if startup else self.bots.running_serials(),
            peak=None if startup else self.bots.peak_devices())
        # Đang hỏi server: báo cho người dùng và khoá giao diện tới khi có kết quả.
        self._place_license_checking()
        self.license_checking.show()
        self.license_checking.raise_()
        self.content.setEnabled(False)
        self._license_worker.finished.connect(self._end_license_check)
        # The server received the report (accepted or refused): start counting the next peak. Offline keeps it.
        self._license_worker.done.connect(lambda: (self.bots.reset_peak(), self.notify_license(None)))
        self._license_worker.refused.connect(lambda msg: (self.bots.reset_peak(), self.notify_license(msg)))
        self._license_worker.offline.connect(self._on_license_offline)
        self._license_worker.start()

    def _on_license_offline(self, _msg: str):
        if self._startup_check:
            self._startup_offline = True   # popup hiện ở _end_license_check, khi thread đã xong hẳn
        else:
            # Offline is fine while the last signed answer is inside the grace period.
            self.notify_license(licensing.check_local())

    def _end_license_check(self):
        """Hỏi server xong (kể cả lỗi bất ngờ): bỏ thông báo "đang kiểm tra"; mở khoá trừ khi giấy phép đang bị khoá.
        Lần lúc mở app mà không tới được server: popup Retry (hỏi lại) / Quit (đóng app); có kết quả rồi thì mới
        kiểm tra bản mới."""
        self.license_checking.hide()
        if self._startup_offline:
            self._startup_offline = False
            if ask_retry_offline(self):
                self._check_license(startup=True)
            else:
                self.close()
            return
        self.content.setEnabled(not self.license_banner.isVisible())
        if self._startup_check:
            self._startup_check = False
            self.home_view.check_update_silently()

    def _place_license_checking(self):
        box, area = self.license_checking, self.centralWidget().rect()
        box.adjustSize()
        box.resize(max(box.width(), 320), box.height())
        box.move(area.center() - box.rect().center())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_license_checking()

    def notify_license(self, notice: str | None):
        """License problem (revoked, expired...): stop the bots, lock the whole UI behind a red banner and show a popup
        (once per notice). The window stays open and the license file untouched; a valid answer unlocks it again."""
        locked = bool(notice)
        self.bots.max_running = licensing.max_devices()   # giấy phép vừa làm mới có thể đổi giới hạn
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
        for device_id in list(self._device_ids):
            self._unregister_device(device_id)
        self._pending_devices = list(serials)
        self._active = self._decide_active(serials)
        self.home_view.set_devices(serials, self._active)
        if self._pending_devices:
            self._register_timer.start()
            QTimer.singleShot(300, self._prebuild_next_view)
        self._refresh_run_counts()

    def _decide_active(self, serials: list) -> dict:
        """{serial: kích hoạt?}: ưu tiên giá trị đã lưu trong DB (không vượt số tối đa); máy mới chưa có trong DB
        được kích hoạt khi còn chỗ, hết chỗ thì không."""
        limit = self.bots.max_running
        room = lambda: limit is None or sum(self._active_flags.values()) < limit
        self._active_flags = {}
        stored = self.db.get_active_map()
        saved = {serial: stored.get(serial) for serial in serials}
        self._saved_active = stored
        for serial in serials:
            if saved[serial] and room():
                self._active_flags[serial] = True
        for serial in serials:
            if serial not in self._active_flags:
                self._active_flags[serial] = saved[serial] is None and room()
        return dict(self._active_flags)

    def _on_active_toggled(self, serial: str, want: bool):
        """Nút Active/Inactive ở Home: lưu DB; kích hoạt không được vượt số tối đa, tắt thì dừng bot của máy."""
        if want:
            limit = self.bots.max_running
            if limit is not None and sum(self._active.values()) >= limit:
                QMessageBox.warning(self, "Cannot activate this device", "Cannot activate this device")
                return
        self._active[serial] = want
        self.db.set_active(serial, want)
        self.home_view.set_active(serial, want)
        view = self.device_views.get(serial)
        if view is not None:
            view.set_active(want)
        if not want:
            self.bots.stop(serial)
        self._refresh_run_counts()

    def _on_active_all_requested(self):
        """Nút Active All ở Home: kích hoạt các máy đang Inactive (theo thứ tự danh sách), máy đã Active giữ nguyên;
        không vượt số tối đa của giấy phép, còn máy chưa bật được thì báo một lần."""
        limit = self.bots.max_running
        skipped = 0
        for serial in list(self._active):   # đủ máy vừa Load Devices, kể cả máy chưa kịp đăng ký
            if self._active[serial]:
                continue
            if limit is not None and sum(self._active.values()) >= limit:
                skipped += 1
                continue
            self._on_active_toggled(serial, True)
        if skipped:
            QMessageBox.warning(self, "Cannot activate all devices",
                                f"Device limit reached ({limit}): {skipped} device(s) left inactive.")

    def _register_next_device(self):
        if self._pending_devices:
            self._register_device(self._pending_devices.pop(0))
        # Làm mới số liệu sau mỗi thiết bị đăng ký để 2 nút Start/Stop All
        # (màn Home và tab Initialization) phản ánh đúng số máy đã thấy.
        self._refresh_run_counts()
        if not self._pending_devices:
            self._register_timer.stop()

    def _unregister_device(self, device_id: str):
        if device_id in self._device_ids:
            self._device_ids.remove(device_id)
        self._new_devices.discard(device_id)
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
        """Đăng ký máy (rẻ): thêm vào DB, sidebar, hàng Home. Giao diện máy dựng sau, ở _ensure_view."""
        if device_id in self._device_ids:
            return
        active = self._active.get(device_id, True)
        if self.db.add_device(device_id, active):
            self._new_devices.add(device_id)
        elif self._saved_active.get(device_id) != active:
            self.db.set_active(device_id, active)
        self._device_ids.append(device_id)
        server = self.db.load_settings(device_id).get("Initialization", {}).get("server", "")
        self.home_view.update_device(device_id, server=server)
        self.sidebar.add_device(device_id)

    def _ensure_view(self, device_id: str, busy: bool = True) -> "DeviceView | None":
        """DeviceView của máy, dựng ngay nếu chưa có (chặn giao diện vài giây)."""
        view = self.device_views.get(device_id)
        if view is None and device_id in self._device_ids:
            if busy:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                view = self._build_view(device_id)
            finally:
                if busy:
                    QApplication.restoreOverrideCursor()
        return view

    def _prebuild_next_view(self):
        """Lúc rảnh dựng sẵn từng máy một (mỗi lần một máy, giữa các lần giao diện vẫn nhận thao tác) để bấm sang máy
        không phải đợi dựng. Máy Active dựng trước."""
        if self._pending_devices:    # còn đang đăng ký máy: đợi xong đã
            QTimer.singleShot(100, self._prebuild_next_view)
            return
        todo = [d for d in self._device_ids if d not in self.device_views]
        if not todo:
            return
        if _idle_seconds() < PREBUILD_IDLE_SECONDS:   # người dùng đang thao tác: đợi, đừng chặn giao diện
            QTimer.singleShot(300, self._prebuild_next_view)
            return
        todo.sort(key=lambda d: not self._active.get(d, True))
        self._ensure_view(todo[0], busy=False)
        QTimer.singleShot(150, self._prebuild_next_view)

    def _ensure_all_views(self):
        for device_id in list(self._device_ids):
            self._ensure_view(device_id)

    def _build_view(self, device_id: str) -> DeviceView:
        view = DeviceView(device_id)
        view.start_requested.connect(self._on_start_requested)
        view.start_all_requested.connect(self._on_start_all_requested)
        view.stop_all_requested.connect(self._on_stop_all_requested)
        view.active_requested.connect(self._on_active_toggled)
        view.apply_all_requested.connect(self._on_apply_all_requested)
        view.server_changed.connect(self._on_server_changed)
        view.auto_angles_requested.connect(self._on_auto_angles)
        view.civilization_changed.connect(self._on_civilization_changed)
        view.reset_progress_requested.connect(self._on_reset_progress)
        view.reset_info_requested.connect(self._on_reset_info)
        view.tab_settings_changed.connect(self.db.save_settings)
        view.profile_selected.connect(self._on_profile_selected)
        view.profile_added.connect(self._on_profile_added)
        view.profile_deleted.connect(self._on_profile_deleted)
        view.tabs.currentChanged.connect(self._on_tab_changed)

        # New device -> store its default config; known device -> restore it.
        if device_id in self._new_devices:
            self._new_devices.discard(device_id)
            # Các tab khác chưa dựng: mỗi tab tự lưu cấu hình mặc định của nó khi được dựng (DeviceView._build_tab).
            self.db.save_settings(device_id, {"Initialization": view.initialization_tab.get_settings()})
        else:
            # Tab chưa dựng nhận cấu hình khi được dựng, rồi tự ghi lại theo code hiện tại (nhiệm vụ Event mới, level / day...).
            view.set_settings(self.db.load_settings(device_id))
        self._refresh_profiles(device_id, view)
        view.set_active(self._active.get(device_id, True))
        # Start All có thể đã chạy bot từ DB trước khi dựng giao diện.
        view.set_running(self.bots.is_running(device_id))
        # Tab Logs chỉ hiện log trong SHOW_SECONDS gần nhất; DB vẫn giữ đủ.
        since = (datetime.now() - timedelta(seconds=SHOW_SECONDS)).isoformat(timespec="seconds")
        for created_at, message in self.db.load_logs(device_id, since):
            view.append_history(created_at, message)

        self.device_views[device_id] = view
        self._refresh_event_times(device_id)
        view.set_run_counts(*self._run_counts())
        self.stack.addWidget(view)
        return view

    def _refresh_event_times(self, serial: str | None = None):
        """Cập nhật tiêu đề group của tab Event (thời gian còn lại của event) cho một thiết bị / mọi thiết bị."""
        for device_id, view in self.device_views.items():
            if serial is None or device_id == serial:
                view.set_event_times(self.db.daily_done(device_id))

    def _show_device(self, device_id: str):
        view = self._ensure_view(device_id)
        self._refresh_event_times(device_id)
        if view is not None:
            view.tabs.setCurrentIndex(self._current_tab_index)
            self.stack.setCurrentWidget(view)

    def _on_tab_changed(self, index: int):
        if index >= 0:
            self._current_tab_index = index

    def _on_apply_all_requested(self, source_id: str, settings: dict):
        """Copy the active device's config onto every other device."""
        self._ensure_all_views()
        for device_id, view in self.device_views.items():
            if device_id != source_id:
                view.set_settings(settings)
        # One transaction for every device: a commit per device (30+
        # fsyncs) froze the UI for seconds.
        self.db.save_many_settings(
            {device_id: view.get_settings() for device_id, view in self.device_views.items()}
        )

    def _on_auto_angles(self, device_id: str):
        """Nút Auto của tab Find Boss: chia đều 0..360° cho mọi thiết bị cùng server với `device_id` (xếp theo device id), mỗi máy một cung liền nhau,
        bội của ANGLE_STEP. Chưa biết server thì chỉ máy này (cả vòng)."""
        self._ensure_all_views()
        server = self.device_views[device_id].initialization_tab.get_settings()["server"].strip()
        ids = sorted(d for d, v in self.device_views.items() if server and v.initialization_tab.get_settings()["server"].strip() == server)
        if device_id not in ids:
            ids = [device_id]
        for d, (start, end) in zip(ids, split_angles(len(ids))):
            self.device_views[d].find_boss_tab.set_settings({START_KEY: start, END_KEY: end})
            self.db.save_settings(d, {"Find Boss": self.device_views[d].find_boss_tab.get_settings()})

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
        self._start_timer.stop()
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
        elif self._active.get(device_id, True):
            self._start_bot(device_id)

    def _on_start_all_requested(self):
        """Start All (màn Home): chạy những thiết bị chưa hoạt động;
        thiết bị đang chạy được giữ nguyên. Máy được start lần lượt qua _start_timer để giao diện không đơ."""
        for device_id in self._device_ids:
            if device_id not in self._start_queue:
                self._start_queue.append(device_id)
        self._start_timer.start()

    def _start_next_queued(self):
        """Start một máy trong hàng đợi Start All (bỏ qua máy đã chạy / không Active)."""
        while self._start_queue:
            device_id = self._start_queue.pop(0)
            if device_id not in self._device_ids or not self._active.get(device_id, True) \
                    or self.bots.is_running(device_id):
                continue
            if self.bots.at_limit():
                self.bots.start(device_id, [], {})   # chỉ để ghi log báo đã đạt giới hạn
                self._start_queue.clear()
                break
            self._start_bot(device_id)
            break
        if not self._start_queue:
            self._start_timer.stop()

    def _on_stop_all_requested(self):
        """Stop All (màn Home và tab Initialization): dừng mọi bot đang chạy và bỏ các máy Start All chưa kịp start."""
        self._start_queue.clear()
        self._start_timer.stop()
        self.bots.stop_all()

    def _on_reset_time_changed(self, server_time: str):
        self.db.set_server_time(server_time)
        self.bots.server_clock.set(server_time)

    def _on_auto_timeout_changed(self, minutes: str):
        self.db.set_auto_timeout(minutes)
        self.bots.auto_timeout_minutes = int(minutes)

    def _run_counts(self) -> tuple[int, int]:
        """(số bot đang chạy, tổng số thiết bị đã đăng ký)."""
        total = sum(1 for d in self._device_ids if self._active.get(d, True))
        running = sum(1 for d in self._device_ids if self.bots.is_running(d))
        return running, total

    def _refresh_run_counts(self):
        """Cập nhật số liệu (đang chạy, tổng thiết bị) cho màn Home và tab
        Initialization của mọi thiết bị -> 2 nút Start All / Stop All tự bật/tắt."""
        counts = self._run_counts()
        self.home_view.set_run_counts(*counts)
        for view in self.device_views.values():
            view.set_run_counts(*counts)

    def _start_bot(self, device_id: str):
        # Đây là dữ liệu riêng của thiết bị trong DB, không phải cấu hình Apply ALL.
        saved = self.db.load_settings(device_id)
        if device_id not in self.device_views and all(tab in saved for tab in TAB_COLUMNS):
            # Chưa dựng giao diện nhưng DB đã đủ cấu hình mọi tab (tab nào dựng xong cũng tự lưu): start thẳng từ DB,
            # khỏi dựng DeviceView + 10 tab (~3 s chặn giao diện mỗi máy, Start All lần đầu 30 máy mất ~2 phút).
            self.bots.start(
                device_id,
                saved["Initialization"].get("activities", []),
                saved,
                daily_done=self.db.daily_done(device_id),
            )
            return
        view = self._ensure_view(device_id)
        if view is None:
            return
        settings = view.get_settings()
        init = settings.setdefault("Initialization", {})
        # Bubble còn hạn trong DB thì bot không cần vào game kiểm tra lại.
        init["bubble_until"] = saved.get("Initialization", {}).get("bubble_until") or ""
        # Nền văn minh bot đã tự xếp (ảnh công trình học chung theo nền văn minh).
        init["civilization"] = saved.get("Initialization", {}).get("civilization")
        # Bản đồ thành bot đã quét (route công trình): không có thì mỗi lần Start lại quét từ đầu.
        init["city_map"] = saved.get("Initialization", {}).get("city_map") or {}
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
        else:   # bot start từ DB, chưa dựng giao diện: sửa thẳng DB
            init = self.db.load_settings(device_id).get("Initialization", {})
            self.db.save_settings(device_id, {"Initialization": {**init, "bubble": False}})

    def _on_craft_done(self, device_id: str, item_id: str):
        """Bot vừa chế tạo xong một trang bị: tab Craft trừ 1 số lượng (về 0 thì bỏ tích) rồi lưu cấu hình mới vào DB, lần Start sau không làm lại."""
        view = self.device_views.get(device_id)
        if view is not None:
            self.db.save_settings(device_id, {"Craft": view.apply_craft_done(item_id)})
        else:   # bot start từ DB, chưa dựng giao diện: trừ thẳng trong DB
            craft = self.db.load_settings(device_id).get("Craft", {})
            subtract_craft_item(craft, item_id)
            self.db.save_settings(device_id, {"Craft": craft})

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
        threading.Thread(target=close_games, args=(list(self._device_ids),),
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
    had_license = bool(licensing.stored_code())
    if not ensure_license():
        sys.exit(0)
    window = MainWindow()
    window.show()
    # Máy đã có giấy phép: app mở ngay, hỏi server trên nền (khung loading giữa cửa sổ). Máy vừa kích hoạt xong
    # thì server vừa trả lời rồi, khỏi hỏi lại.
    if had_license:
        QTimer.singleShot(0, lambda: window._check_license(startup=True))   # xong rồi mới kiểm tra bản mới
    else:
        QTimer.singleShot(0, window.home_view.check_update_silently)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
