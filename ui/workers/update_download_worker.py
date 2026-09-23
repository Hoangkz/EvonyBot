"""
update_download_worker.py — downloads a release installer.
"""
from PyQt5.QtCore import QThread, pyqtSignal

import updater


class UpdateDownloadWorker(QThread):
    progress = pyqtSignal(int)
    downloaded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, release: dict, parent=None):
        super().__init__(parent)
        self._release = release

    def run(self):
        try:
            path = updater.download(self._release["url"], self._release["name"], self.progress.emit)
            self.downloaded.emit(str(path))
        except Exception as e:
            self.failed.emit(str(e))
