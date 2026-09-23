"""
update_check_worker.py — checks GitHub for the latest release.
"""
from PyQt5.QtCore import QThread, pyqtSignal

import updater


class UpdateCheckWorker(QThread):
    """Asks GitHub for the latest release; result is None when up to date."""

    result = pyqtSignal(object)
    failed = pyqtSignal(str)

    def run(self):
        try:
            self.result.emit(updater.check_latest())
        except Exception as e:
            self.failed.emit(str(e))
