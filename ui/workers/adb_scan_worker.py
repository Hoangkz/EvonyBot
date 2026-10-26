"""
adb_scan_worker.py — scans ADB ports and lists connected devices.
"""
import time
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtCore import QThread, pyqtSignal

ADB_HOST = "127.0.0.1"
PORT_START = 21503   # mặc định; người dùng đổi ở màn Home (database.py: scan_ports)
PORT_END = 25000
PORT_STEP = 10
MAX_WORKERS = 400    # khoảng port do người dùng chọn có thể rất lớn: không mở quá chừng này luồng một lúc
SETTLE_RETRIES = 10
SETTLE_DELAY = 0.5  # seconds


class AdbScanWorker(QThread):
    """Connects to every port concurrently, waits for all, then lists devices."""

    finished_scan = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, parent=None, port_start: int = PORT_START, port_end: int = PORT_END):
        super().__init__(parent)
        self.port_start = port_start
        self.port_end = port_end

    def run(self):
        try:
            import adbutils

            adb = adbutils.adb
            addresses = [f"{ADB_HOST}:{p}" for p in range(self.port_start, self.port_end + 1, PORT_STEP)]

            def connect(addr: str):
                try:
                    return adb.connect(addr, timeout=15.0)
                except Exception:
                    return None

            # Fire the connects concurrently (up to MAX_WORKERS at a time) and wait for every one to finish.
            try:
                with ThreadPoolExecutor(max_workers=min(len(addresses), MAX_WORKERS)) as pool:
                    list(pool.map(connect, addresses))
            except Exception:
                pass  # best-effort only

            # Freshly connected devices report "offline" for a moment before
            # turning "device"; poll until they settle (or give up).
            infos = adb.list()
            for _ in range(SETTLE_RETRIES):
                if all(info.state == "device" for info in infos):
                    break
                time.sleep(SETTLE_DELAY)
                infos = adb.list()

            # Closed emulators can linger as "offline"; disconnect them so
            # they don't show up again, and only list online devices.
            serials = []
            for info in infos:
                if info.state == "device":
                    serials.append(info.serial)
                elif ":" in info.serial:
                    try:
                        adb.disconnect(info.serial)
                    except Exception:
                        pass
            self.finished_scan.emit(serials)
        except Exception as e:
            self.failed.emit(str(e))
