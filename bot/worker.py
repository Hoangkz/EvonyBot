"""
worker.py — one bot thread per device, plus the manager that owns them.

BotWorker runs the device's selected activities in a loop on its own
QThread until it is stopped. Each activity lives in its own module
under bot/activities/ (see ACTIVITIES there).

BotManager keeps one worker per device and re-emits the workers'
signals, so the UI only has to connect to the manager.
"""
import threading

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from .activities import ACTIVITIES
from .context import BotContext, BotInterrupted

STATUS_IDLE = "InActive"
STATUS_RUNNING = "Running"
STATUS_STOPPING = "Stopping..."
STATUS_STOPPED = "Stopped"
STATUS_ERROR = "Error"


class BotWorker(QThread):
    activity_changed = pyqtSignal(str, str)   # (serial, activity)
    status_changed = pyqtSignal(str, str)     # (serial, status)

    def __init__(self, serial: str, activities: list[str], settings: dict, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.activities = list(activities)
        self.settings = settings            # DeviceView.get_settings() snapshot
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
            while not self._stop.is_set():
                for activity in self.activities:
                    if self._stop.is_set():
                        break
                    self.activity_changed.emit(self.serial, activity)
                    self._run_activity(activity, self.settings.get(activity, {}))
        except BotInterrupted:
            pass
        except Exception as e:
            status = f"{STATUS_ERROR}: {e}"
            print(f"[{self.serial}] {status}")
        finally:
            self.activity_changed.emit(self.serial, "None")
            self.status_changed.emit(self.serial, status)

    def _run_activity(self, activity: str, tab_settings: dict):
        run = ACTIVITIES.get(activity)
        if run is None:
            self.log(f"Unknown activity: {activity}")
            self.ctx.sleep(1.0)
            return
        run(self.ctx, tab_settings)

    def log(self, message: str):
        print(f"[{self.serial}] {message}")


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
