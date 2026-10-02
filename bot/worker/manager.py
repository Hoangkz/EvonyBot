"""
manager.py — BotManager: keeps one worker per device and re-emits the
workers' signals, so the UI only has to connect to the manager.
"""
from PyQt5.QtCore import QObject, pyqtSignal

from .bot_worker import BotWorker
from .boss_board import BossBoard
from .server_clock import ServerClock
from .status import STATUS_STOPPING


class BotManager(QObject):
    activity_changed = pyqtSignal(str, str)   # (serial, activity)
    status_changed = pyqtSignal(str, str)     # (serial, status)
    running_changed = pyqtSignal(str, bool)   # (serial, running)
    server_found = pyqtSignal(str, str)       # (serial, server)

    daily_task_done = pyqtSignal(str, str)    # (serial, task Daily Activities vừa xong)
    bubble_found = pyqtSignal(str, int)       # (serial, giây bubble còn lại; 0 = không có)
    bubble_disabled = pyqtSignal(str)         # (serial) không đủ kim cương -> bỏ tích Bubble
    log_message = pyqtSignal(str, str)        # (serial, dòng log) -> tab Logs > Info
    history = pyqtSignal(str, str)            # (serial, sự kiện) -> lưu DB + tab Logs > History

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: dict[str, BotWorker] = {}
        self.boss_board = BossBoard()
        # Giờ reset server chung mọi thiết bị: main gán giá trị đã lưu trong DB / chọn ở màn Home.
        self.server_clock = ServerClock()

    def is_running(self, serial: str) -> bool:
        return serial in self._workers

    def start(self, serial: str, activities: list[str], settings: dict,
              daily_done: dict | None = None) -> bool:
        if self.is_running(serial):
            return False
        if not activities:
            print(f"[{serial}] No activity selected")
            self.log_message.emit(serial, "No activity selected")
            return False

        worker = BotWorker(serial, activities, settings, self,
                           boss_board=self.boss_board, daily_done=daily_done,
                           server_clock=self.server_clock)
        worker.activity_changed.connect(self.activity_changed.emit)
        worker.status_changed.connect(self.status_changed.emit)
        worker.server_found.connect(self.server_found.emit)
        worker.daily_task_done.connect(self.daily_task_done.emit)
        worker.bubble_found.connect(self.bubble_found.emit)
        worker.bubble_disabled.connect(self.bubble_disabled.emit)
        worker.log_message.connect(self.log_message.emit)
        worker.history.connect(self.history.emit)
        worker.finished.connect(lambda: self._on_finished(serial))
        self._workers[serial] = worker
        worker.start()
        self.running_changed.emit(serial, True)
        return True

    def stop(self, serial: str):
        worker = self._workers.get(serial)
        if worker is not None:
            worker.stop()
            self.status_changed.emit(serial, STATUS_STOPPING)

    def stop_all(self, wait: bool = False):
        workers = list(self._workers.values())
        for serial in self._workers:
            self.stop(serial)
        if wait:
            for worker in workers:
                worker.wait()

    def _on_finished(self, serial: str):
        worker = self._workers.pop(serial, None)
        if worker is not None:
            worker.deleteLater()
        self.running_changed.emit(serial, False)
