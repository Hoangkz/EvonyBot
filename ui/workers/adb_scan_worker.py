"""
adb_scan_worker.py — scans ADB ports and lists connected devices.
"""
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtCore import QThread, pyqtSignal

ADB_HOST = "127.0.0.1"
PORT_START = 21503
PORT_END = 25000
PORT_STEP = 10


class AdbScanWorker(QThread):
    """Connects to every port concurrently, waits for all, then lists devices."""

    finished_scan = pyqtSignal(list)
    failed = pyqtSignal(str)

    def run(self):
        try:
            import adbutils

            adb = adbutils.adb
            addresses = [f"{ADB_HOST}:{p}" for p in range(PORT_START, PORT_END + 1, PORT_STEP)]

            def connect(addr: str):
                try:
                    return adb.connect(addr, timeout=15.0)
                except Exception:
                    return None

            # Fire all connects at once and wait for every one to finish (like Promise.all).
            try:
                with ThreadPoolExecutor(max_workers=len(addresses)) as pool:
                    list(pool.map(connect, addresses))
            except Exception:
                pass  # best-effort only

            serials = [d.serial for d in adb.device_list()]
            self.finished_scan.emit(serials)
        except Exception as e:
            self.failed.emit(str(e))
