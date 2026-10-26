"""
dev_ui.py — chạy app thật (MainWindow, mọi logic giao diện như cũ) nhưng không đụng giả lập / ADB / giấy phép: `poe dev:ui`.

Khác bản thật:
- Load Devices: mọi port trong khoảng Start - End (bước PORT_STEP) đều "có máy", không kết nối thật.
- Nút + Add device: luôn kết nối thành công.
- DB: file tạm, xoá khi thoát (không lưu gì).
- Start: bot giả, chỉ đổi trạng thái Running / Stopped, không chạm giả lập.
- Giấy phép: bỏ qua (không hỏi server, không giới hạn số máy); không kiểm tra bản cập nhật.
"""
import tempfile
import time
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal

import database
import licensing
import main
import ui.add_device_dialog as add_dialog
import ui.home_view as home_module
from bot.worker import BotManager
from bot.worker.status import STATUS_RUNNING, STATUS_STOPPED
from ui.workers.adb_scan_worker import ADB_HOST, PORT_STEP


class FakeScanWorker(QThread):
    finished_scan = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, parent=None, port_start: int = 0, port_end: int = 0):
        super().__init__(parent)
        self.port_start, self.port_end = port_start, port_end

    def run(self):
        time.sleep(0.5)
        self.finished_scan.emit([f"{ADB_HOST}:{p}" for p in range(self.port_start, self.port_end + 1, PORT_STEP)])


class FakeConnectWorker(QThread):
    done = pyqtSignal(bool)

    def __init__(self, address: str, parent=None):
        super().__init__(parent)

    def run(self):
        time.sleep(1)
        self.done.emit(True)


class FakeWorker(QObject):
    """Chỗ của BotWorker: giữ chỗ trong BotManager._workers cho tới khi stop()."""

    def wait(self):
        pass


class FakeBotManager(BotManager):
    def start(self, serial, activities, settings, daily_done=None):
        if self.is_running(serial):
            return False
        if self.at_limit():
            return False
        if not activities:
            self.log_message.emit(serial, "No activity selected")
            return False
        self._workers[serial] = FakeWorker()
        self._peak = max(self._peak, len(self._workers))
        self.running_changed.emit(serial, True)
        self.status_changed.emit(serial, STATUS_RUNNING)
        self.activity_changed.emit(serial, activities[0])
        self.log_message.emit(serial, "Mock bot started")
        return True

    def stop(self, serial):
        if self._workers.pop(serial, None) is not None:
            self.status_changed.emit(serial, STATUS_STOPPED)
            self.activity_changed.emit(serial, "None")
            QTimer.singleShot(0, lambda: self.running_changed.emit(serial, False))


def main_ui():
    tmp = tempfile.TemporaryDirectory(prefix="evonybot_ui_", ignore_cleanup_errors=True)
    db_path = Path(tmp.name) / "evonybot.db"

    home_module.AdbScanWorker = FakeScanWorker
    add_dialog.ConnectWorker = FakeConnectWorker
    main.BotManager = FakeBotManager
    main.Database = lambda: database.Database(db_path)
    main.MainWindow._check_license = lambda self, startup=False: None
    home_module.HomeView.check_update_silently = lambda self, *a, **k: None
    licensing.stored_code = lambda: "DEV"
    licensing.max_devices = lambda: None
    licensing.check_local = lambda: None
    main.main()


if __name__ == "__main__":
    main_ui()
