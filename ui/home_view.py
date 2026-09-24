"""
home_view.py — landing screen: scans ADB ports and lists devices.
"""
from pathlib import Path

from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import updater
from version import __version__

from .workers import AdbScanWorker, UpdateCheckWorker, UpdateDownloadWorker

TIMEOUT_OPTIONS = ["30", "60", "90", "120", "180", "240", "300", "360"]


class HomeView(QWidget):
    devices_loaded = pyqtSignal(list)
    start_all_requested = pyqtSignal()
    exit_all_requested = pyqtSignal()
    close_all_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeView")
        self._worker: AdbScanWorker | None = None
        self._device_count = 0
        self._all_running = False
        self._update_worker: QThread | None = None
        self._progress: QProgressDialog | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(10)

        # ---- Load Devices / Update ----
        top = QHBoxLayout()
        self.load_button = QPushButton("Load Devices")
        self.load_button.setMinimumSize(170, 50)
        self.load_button.clicked.connect(self._load_devices)
        top.addWidget(self.load_button)
        top.addStretch(1)
        self.update_button = QPushButton(f"Version {__version__}")
        self.update_button.setFixedHeight(32)
        self.update_button.clicked.connect(self._check_update)
        top.addWidget(self.update_button)
        layout.addLayout(top)

        title = QLabel("List Devices")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16pt;")
        layout.addWidget(title)

        layout.addSpacing(30)

        # ---- Toolbar ----
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(QLabel("Auto Times Out"))
        self.timeout_combo = QComboBox()
        self.timeout_combo.addItems(TIMEOUT_OPTIONS)
        self.timeout_combo.setCurrentText("180")
        self.timeout_combo.setFixedWidth(75)
        toolbar.addWidget(self.timeout_combo)
        toolbar.addWidget(QLabel("Minutes"))
        toolbar.addSpacing(12)

        exit_all = QPushButton("Exit All")
        exit_all.setMinimumSize(100, 36)
        exit_all.clicked.connect(self.exit_all_requested.emit)
        toolbar.addWidget(exit_all)

        close_all = QPushButton("Close All")
        close_all.setMinimumSize(100, 36)
        close_all.clicked.connect(self.close_all_requested.emit)
        toolbar.addWidget(close_all)

        toolbar.addStretch(1)

        self.start_all_button = QPushButton("Start All(0)")
        self.start_all_button.setMinimumSize(100, 36)
        self.start_all_button.clicked.connect(self.start_all_requested.emit)
        toolbar.addWidget(self.start_all_button)
        layout.addLayout(toolbar)

        # ---- Device table ----
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["DevicesName", "Activity", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setShowGrid(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(
            """
            QTableWidget { background: transparent; border: none; }
            QHeaderView::section {
                background: #3a73e8; color: white; font-size: 12pt;
                border: 1px solid #2b4a8a; padding: 4px; margin-right: 8px;
            }
            QTableWidget::item {
                background: #b3f7f7; border: 1px solid #555;
                margin-right: 8px; padding: 4px;
            }
            """
        )
        layout.addWidget(self.table, 1)

    # ------------------------------------------------------------------
    def _load_devices(self):
        if self._worker is not None and self._worker.isRunning():
            return
        self.load_button.setEnabled(False)
        self.load_button.setText("Loading...")
        self._worker = AdbScanWorker(self)
        self._worker.finished_scan.connect(self._on_scan_finished)
        self._worker.failed.connect(self._on_scan_failed)
        self._worker.start()

    def _on_scan_finished(self, serials: list):
        self._reset_load_button()
        self.set_devices(serials)
        self.devices_loaded.emit(serials)

    def _on_scan_failed(self, message: str):
        self._reset_load_button()
        print(f"[EvonyBot] ADB scan failed: {message}")

    def _reset_load_button(self):
        self.load_button.setEnabled(True)
        self.load_button.setText("Load Devices")

    # ---- update ------------------------------------------------------
    def _check_update(self):
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        self.update_button.setEnabled(False)
        self.update_button.setText("Checking...")
        self._update_worker = UpdateCheckWorker(self)
        self._update_worker.result.connect(self._on_update_checked)
        self._update_worker.failed.connect(self._on_update_failed)
        self._update_worker.start()

    def _on_update_checked(self, release: dict | None):
        self._reset_update_button()
        if release is None:
            QMessageBox.information(self, "Update", f"You are on the latest version ({__version__}).")
            return
        answer = QMessageBox.question(
            self, "Update",
            f"Version {release['version']} is available (current {__version__}).\n"
            "Download and install it now? The app will close (running bots are stopped) "
            "and reopen when the update is done.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._progress = QProgressDialog("Downloading update...", "", 0, 100, self)
        self._progress.setWindowTitle("Update")
        self._progress.setCancelButton(None)
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.show()
        self.update_button.setEnabled(False)
        self._update_worker = UpdateDownloadWorker(release, self)
        self._update_worker.progress.connect(self._progress.setValue)
        self._update_worker.downloaded.connect(self._on_update_downloaded)
        self._update_worker.failed.connect(self._on_update_failed)
        self._update_worker.start()

    def _on_update_downloaded(self, path: str):
        self._progress.close()
        try:
            updater.run_installer(Path(path))
        except Exception as e:
            self._on_update_failed(str(e))
            return
        # Quit so the installer can replace the app files.
        self.window().close()

    def _on_update_failed(self, message: str):
        if self._progress is not None:
            self._progress.close()
        self._reset_update_button()
        QMessageBox.warning(self, "Update", f"Update failed:\n{message}")

    def _reset_update_button(self):
        self.update_button.setEnabled(True)
        self.update_button.setText(f"Version {__version__}")

    def set_devices(self, serials: list):
        self.table.setRowCount(0)
        for serial in serials:
            self.add_device_row(serial)
        self._device_count = len(serials)
        self._refresh_start_all_text()

    def set_all_running(self, running: bool):
        """Start All becomes Stop All once every device's bot is running."""
        self._all_running = running
        self._refresh_start_all_text()

    def _refresh_start_all_text(self):
        label = "Stop All" if self._all_running else "Start All"
        self.start_all_button.setText(f"{label}({self._device_count})")

    def add_device_row(self, serial: str, activity: str = "None", status: str = "InActive"):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, text in enumerate((serial, activity, status)):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)

    def update_device(self, serial: str, activity: str | None = None, status: str | None = None):
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == serial:
                if activity is not None:
                    self.table.item(row, 1).setText(activity)
                if status is not None:
                    self.table.item(row, 2).setText(status)
                return

    @property
    def auto_timeout_minutes(self) -> int:
        return int(self.timeout_combo.currentText())
