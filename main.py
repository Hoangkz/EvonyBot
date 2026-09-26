"""
main.py — EvonyBot entry point.

Python/PyQt5 rewrite of the original WinForms `Form3`: a left sidebar
listing connected devices (was `panelistbutton`) next to a content
area (was `panelData`) that shows either the home/welcome screen or
the selected device's tabbed control panel.
"""
import ctypes
import platform
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QHBoxLayout

from bot.worker import BotManager
from database import Database
from ui import DeviceView, HomeView, Sidebar
from ui import theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evony Control App")
        self.db = Database()
        self.resize(1329, 708)
        self._center_on_screen()

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.home_view = HomeView()
        self.stack.addWidget(self.home_view)
        self.stack.setCurrentWidget(self.home_view)

        self.device_views: dict[str, DeviceView] = {}
        # Building a DeviceView is heavy (8 designer tabs), so new devices
        # are registered one per event-loop tick to keep the UI responsive.
        self._pending_devices: list[str] = []
        self._register_timer = QTimer(self)
        self._register_timer.setInterval(0)
        self._register_timer.timeout.connect(self._register_next_device)

        self.bots = BotManager(self)
        self.bots.activity_changed.connect(
            lambda serial, activity: self.home_view.update_device(serial, activity=activity)
        )
        self.bots.status_changed.connect(
            lambda serial, status: self.home_view.update_device(serial, status=status)
        )
        self.bots.running_changed.connect(self._on_bot_running_changed)
        # Sub-tab index kept across devices, so switching device stays on
        # the same tab instead of jumping back to Initialization.
        self._current_tab_index = 0

        self.sidebar.home_selected.connect(lambda: self.stack.setCurrentWidget(self.home_view))
        self.sidebar.device_selected.connect(self._show_device)
        self.home_view.devices_loaded.connect(self._on_devices_loaded)
        self.home_view.start_all_requested.connect(self._on_start_all_requested)
        self.home_view.exit_all_requested.connect(self._on_exit_all_requested)
        self.home_view.close_all_requested.connect(self._on_close_all_requested)

    def _center_on_screen(self):
        frame = self.frameGeometry()
        frame.moveCenter(self.screen().availableGeometry().center())
        self.move(frame.topLeft())

    def _on_devices_loaded(self, serials: list):
        # Drop devices that are no longer connected (emulator closed).
        for device_id in list(self.device_views):
            if device_id not in serials:
                self._unregister_device(device_id)
        self._pending_devices = [s for s in serials if s not in self.device_views]
        if self._pending_devices:
            self._register_timer.start()
        self.home_view.set_all_running(self._all_running())

    def _register_next_device(self):
        if self._pending_devices:
            self._register_device(self._pending_devices.pop(0))
        if not self._pending_devices:
            self._register_timer.stop()
            self.home_view.set_all_running(self._all_running())

    def _unregister_device(self, device_id: str):
        self.sidebar.remove_device(device_id)
        view = self.device_views.pop(device_id, None)
        if view is not None:
            if self.stack.currentWidget() is view:
                self.stack.setCurrentWidget(self.home_view)
                self.sidebar.select_home()
            self.stack.removeWidget(view)
            view.deleteLater()
        self.bots.stop(device_id)

    def _register_device(self, device_id: str):
        if device_id in self.device_views:
            return
        view = DeviceView(device_id)
        view.start_requested.connect(self._on_start_requested)
        view.start_all_requested.connect(self._on_start_all_requested)
        view.apply_all_requested.connect(self._on_apply_all_requested)
        view.tabs.currentChanged.connect(self._on_tab_changed)

        # New device -> store its default config; known device -> restore it.
        if self.db.add_device(device_id):
            self.db.save_settings(device_id, view.get_settings())
        else:
            view.set_settings(self.db.load_settings(device_id))

        self.device_views[device_id] = view
        view.set_all_running(self._all_running())
        self.stack.addWidget(view)
        self.sidebar.add_device(device_id)

    def _show_device(self, device_id: str):
        view = self.device_views.get(device_id)
        if view is not None:
            view.tabs.setCurrentIndex(self._current_tab_index)
            self.stack.setCurrentWidget(view)

    def _on_tab_changed(self, index: int):
        if index >= 0:
            self._current_tab_index = index

    def _on_apply_all_requested(self, source_id: str, settings: dict):
        """Copy the active device's config onto every other device."""
        for device_id, view in self.device_views.items():
            if device_id != source_id:
                view.set_settings(settings)
            self.db.save_settings(device_id, view.get_settings())

    def closeEvent(self, event):
        self._register_timer.stop()
        self.bots.stop_all(wait=True)
        self.db.close()
        super().closeEvent(event)

    def _on_start_requested(self, device_id: str):
        """Start button toggles: starts the device's bot, or stops it if running."""
        if self.bots.is_running(device_id):
            self.bots.stop(device_id)
        else:
            self._start_bot(device_id)

    def _on_start_all_requested(self):
        """Start All toggles: stops every bot once all are running,
        otherwise starts the ones that aren't running yet."""
        if self._all_running():
            self.bots.stop_all()
            return
        for device_id in self.device_views:
            if not self.bots.is_running(device_id):
                self._start_bot(device_id)

    def _all_running(self) -> bool:
        return bool(self.device_views) and all(
            self.bots.is_running(d) for d in self.device_views
        )

    def _start_bot(self, device_id: str):
        view = self.device_views.get(device_id)
        if view is None:
            return
        self.bots.start(
            device_id,
            view.initialization_tab.selected_activities(),
            view.get_settings(),
        )

    def _on_bot_running_changed(self, device_id: str, running: bool):
        view = self.device_views.get(device_id)
        if view is not None:
            view.set_running(running)
        all_running = self._all_running()
        self.home_view.set_all_running(all_running)
        for v in self.device_views.values():
            v.set_all_running(all_running)

    def _on_exit_all_requested(self):
        # TODO: wire up to the actual automation/bot backend.
        print("[EvonyBot] Exit ALL requested")

    def _on_close_all_requested(self):
        # TODO: wire up to the actual automation/bot backend.
        print("[EvonyBot] Close ALL requested")


def main():
    # adbutils calls platform.system() on every socket. On Windows the
    # first call runs a WMI query that crashes (0x800703e5) when many ADB
    # connect threads hit it at once; call it here so the result is cached.
    platform.system()
    # Qt6 enables high-DPI scaling by default; Qt5 needs it opted in
    # (must be set before the QApplication is created).
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    # The installed app runs as pythonw.exe; give it its own taskbar
    # identity (matches the shortcut's AppUserModelID) and icon instead
    # of Python's.
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("EvonyBot")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "Images" / "icon.ico")))
    theme.apply(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
