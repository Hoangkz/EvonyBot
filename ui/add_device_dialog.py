"""
add_device_dialog.py — popup nhập port thiết bị rồi adb connect trên thread nền.

Bấm Connect / Enter không đóng popup: vòng xoay hiện ở giữa popup trong lúc kết nối; thành công thì đóng (`address` là serial đã
kết nối), thất bại thì báo ngay trong popup để sửa port nhập lại. Giao diện chung ở ui/dialogs.py.
"""
import time

from PyQt5.QtCore import QThread, pyqtSignal

from .dialogs import StyledDialog

ADB_HOST = "127.0.0.1"
SETTLE_RETRIES = 10
SETTLE_DELAY = 0.5  # giây


class ConnectWorker(QThread):
    done = pyqtSignal(bool)

    def __init__(self, address: str, parent=None):
        super().__init__(parent)
        self.address = address

    def run(self):
        try:
            import adbutils

            adb = adbutils.adb
            adb.connect(self.address, timeout=10.0)
            for _ in range(SETTLE_RETRIES):
                if any(i.serial == self.address and i.state == "device" for i in adb.list()):
                    self.done.emit(True)
                    return
                time.sleep(SETTLE_DELAY)
        except Exception:
            pass
        self.done.emit(False)


class AddDeviceDialog(StyledDialog):
    def __init__(self, parent=None):
        super().__init__("Add device", "Add device",
                         f"Enter the emulator's ADB port (e.g. 5555). {ADB_HOST} is added automatically; "
                         "or type host:port.",
                         placeholder="Device port", ok_text="Connect", parent=parent)
        self.address = ""
        self._worker: ConnectWorker | None = None

    def _submit(self):
        port = self.edit.text().strip()
        if not port or self._worker is not None:
            return
        self.address = port if ":" in port else f"{ADB_HOST}:{port}"
        self.clear_error()
        self.edit.setEnabled(False)
        self.ok_button.setEnabled(False)
        self.set_busy(True, f"Connecting to {self.address}…")
        self._worker = ConnectWorker(self.address, self)
        self._worker.done.connect(self._finished)
        self._worker.start()

    def _finished(self, ok: bool):
        self._worker = None
        self.ok_button.setEnabled(True)
        self.edit.setEnabled(True)
        self.set_busy(False)
        if ok:
            self.accept()
            return
        self.show_error(f"Cannot connect to device {self.address}.")
        self.edit.setFocus()
        self.edit.selectAll()

    def reject(self):
        if self._worker is not None:   # đang kết nối: đợi xong rồi mới đóng được
            return
        super().reject()

    def closeEvent(self, event):
        if self._worker is not None:
            event.ignore()
        else:
            super().closeEvent(event)
