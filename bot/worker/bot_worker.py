"""
bot_worker.py — BotWorker: runs the device's selected activities once each
on its own QThread (Join Boss keeps going until it stops by itself or Stop).
"""
import threading
import time

from PyQt5.QtCore import QThread, pyqtSignal

from ..activities import ACTIVITIES
from ..activities.join_monster_war import IDLE as BOSS_IDLE
from ..common import get_server
from ..context import BotContext, BotInterrupted, TimedOut
from .status import STATUS_ERROR, STATUS_RUNNING, STATUS_STOPPED

JOIN_BOSS = "Join Monster War"
OTHERS_WINDOW = 120   # giây tối đa làm activity khác trước khi quay lại kiểm tra boss


class BotWorker(QThread):
    activity_changed = pyqtSignal(str, str)   # (serial, activity)
    status_changed = pyqtSignal(str, str)     # (serial, status)
    server_found = pyqtSignal(str, str)       # (serial, server)

    def __init__(self, serial: str, activities: list[str], settings: dict, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.activities = list(activities)
        self.settings = settings            # DeviceView.get_settings() snapshot
        self.server = settings.get("Initialization", {}).get("server") or ""
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        self.status_changed.emit(self.serial, STATUS_RUNNING)
        status = STATUS_STOPPED
        try:
            import adbutils

            device = adbutils.adb.device(serial=self.serial)
            self.ctx = BotContext(device, self._stop, None, self.log)
            self.ctx.settings = self.settings
            others = [a for a in self.activities if a != JOIN_BOSS]
            if JOIN_BOSS in self.activities and others:
                self._boss_priority(others)
            else:
                self._run_once(self.activities)
        except BotInterrupted:
            pass
        except Exception as e:
            status = f"{STATUS_ERROR}: {e}"
            print(f"[{self.serial}] {status}")
        finally:
            self.activity_changed.emit(self.serial, "None")
            self.status_changed.emit(self.serial, status)

    def _run_once(self, activities: list[str]):
        """Chạy tuần tự mỗi activity 1 lần (nhiệm vụ xong là xong)."""
        for activity in activities:
            if self._stop.is_set():
                break
            self._ensure_server()
            self.activity_changed.emit(self.serial, activity)
            self._run_activity(activity, self.settings.get(activity, {}))

    def _boss_priority(self, others: list[str]):
        """Ưu tiên Join Boss; boss rảnh -> làm activity khác tối đa OTHERS_WINDOW giây
        rồi quay lại kiểm tra boss. Activity bị cắt giữa chừng được làm tiếp đầu
        tiên ở lượt sau; activity chạy tới cuối là hoàn thành, bỏ khỏi danh sách.
        - Join Boss dừng hẳn (không phải rảnh) -> chạy nốt các activity chưa xong.
        - Các activity khác đã hoàn thành hết -> chỉ còn Join Boss."""
        pending = list(others)   # activity chưa hoàn thành, pending[0] là cái đang dở
        while not self._stop.is_set():
            if not pending:
                self._run_once([JOIN_BOSS])
                return

            self._ensure_server()
            self.activity_changed.emit(self.serial, JOIN_BOSS)
            result = self._run_activity(JOIN_BOSS, {**self.settings.get(JOIN_BOSS, {}), "exit_when_idle": True})
            if result != BOSS_IDLE:
                self._run_once(pending)   # bắt đầu từ activity đang dở
                return

            self.ctx._deadline = time.monotonic() + OTHERS_WINDOW
            try:
                while pending:
                    self.activity_changed.emit(self.serial, pending[0])
                    self._run_activity(pending[0], self.settings.get(pending[0], {}))
                    pending.pop(0)
            except TimedOut:
                pass    # hết 2 phút -> pending[0] là activity đang dở, lượt sau làm tiếp
            finally:
                self.ctx._deadline = None

    def _ensure_server(self):
        """Chưa có server -> đọc server trong game rồi báo ra UI để lưu lại."""
        if self.server:
            return
        self.activity_changed.emit(self.serial, "Get Server")
        server = get_server(self.ctx)
        if server:
            self.server = server
            self.server_found.emit(self.serial, server)

    def _run_activity(self, activity: str, tab_settings: dict):
        run = ACTIVITIES.get(activity)
        if run is None:
            self.log(f"Unknown activity: {activity}")
            self.ctx.sleep(1.0)
            return None
        return run(self.ctx, tab_settings)

    def log(self, message: str):
        print(f"[{self.serial}] {message}")
