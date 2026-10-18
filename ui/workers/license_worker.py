"""
license_worker.py — talks to the license server off the UI thread.
"""
from PyQt5.QtCore import QThread, pyqtSignal

import licensing


class LicenseWorker(QThread):
    """mode "activate" (needs code and customer info) or "verify". Signals: done() on success,
    refused(msg) when the server rejects the code, offline(msg) when it cannot be reached."""

    done = pyqtSignal()
    refused = pyqtSignal(str)
    offline = pyqtSignal(str)

    def __init__(self, mode: str, code: str = "", customer: dict | None = None, parent=None):
        super().__init__(parent)
        self._mode = mode
        self._code = code
        self._customer = customer or {}

    def run(self):
        try:
            if self._mode == "activate":
                licensing.activate(self._code, self._customer)
            else:
                licensing.verify()
            self.done.emit()
        except licensing.LicenseError as e:
            self.refused.emit(str(e))
        except licensing.OfflineError as e:
            self.offline.emit(str(e))
