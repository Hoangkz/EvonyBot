"""
bot_worker.py — BotWorker: runs the device's selected activities in a loop
on its own QThread until it is stopped.
"""
import threading

from PyQt5.QtCore import QThread, pyqtSignal

from ..activities import ACTIVITIES
from ..context import BotContext, BotInterrupted
from .status import STATUS_ERROR, STATUS_RUNNING, STATUS_STOPPED


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
