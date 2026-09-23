"""
manager.py — BotManager: keeps one worker per device and re-emits the
workers' signals, so the UI only has to connect to the manager.
"""
from PyQt5.QtCore import QObject, pyqtSignal

from .bot_worker import BotWorker
from .status import STATUS_STOPPING


class BotManager(QObject):
    activity_changed = pyqtSignal(str, str)   # (serial, activity)
    status_changed = pyqtSignal(str, str)     # (serial, status)
    running_changed = pyqtSignal(str, bool)   # (serial, running)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: dict[str, BotWorker] = {}

    def is_running(self, serial: str) -> bool:
        return serial in self._workers

    def start(self, serial: str, activities: list[str], settings: dict) -> bool:
        if self.is_running(serial):
            return False
        if not activities:
            print(f"[{serial}] No activity selected")
            return False

        worker = BotWorker(serial, activities, settings, self)
        worker.activity_changed.connect(self.activity_changed.emit)
        worker.status_changed.connect(self.status_changed.emit)
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
