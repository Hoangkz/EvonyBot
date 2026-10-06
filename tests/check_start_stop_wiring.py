"""Kiểm tra wiring 2 nút Start All / Stop All ở MainWindow (chạy tay, offscreen).

Không đụng DB thật: chỉ dựng MainWindow rồi giả lập device_views / bot manager.
"""
import os
import sys
from pathlib import Path

# Chạy trực tiếp `python tests/...` -> sys.path[0] là thư mục tests, cần thêm gốc repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    from main import MainWindow
    window = MainWindow()

    called: list[str] = []
    window.bots.stop_all = lambda wait=False: called.append("stop_all")
    window._start_bot = lambda device_id: called.append(f"start:{device_id}")
    from ui.device_view import DeviceView
    window.device_views = {"devA": DeviceView("devA"), "devB": DeviceView("devB")}
    window.bots.is_running = lambda serial: serial == "devA"   # devA chạy, devB idle

    window._refresh_run_counts()
    home = window.home_view
    print("home buttons :", home.start_all_button.text(), home.start_all_button.isEnabled(),
          "|", home.stop_all_button.text(), home.stop_all_button.isEnabled())
    print("run counts   :", window._run_counts())

    home.start_all_button.click()
    home.stop_all_button.click()
    print("after click  :", called)

    # Tab Initialization của một device view trong danh sách
    view = window.device_views["devA"]
    forwarded: list[str] = []
    view.start_all_requested.connect(lambda: forwarded.append("start"))
    view.stop_all_requested.connect(lambda: forwarded.append("stop"))
    view.set_run_counts(1, 2)
    start, stop = view.initialization_tab.controls["button9"], \
        view.initialization_tab.controls["buttonStopAll"]
    print("tab buttons  :", start.text(), start.isEnabled(), "|", stop.text(), stop.isEnabled(),
          "| geometry:", start.geometry().getRect(), stop.geometry().getRect())
    start.click()
    stop.click()
    print("tab clicked  :", forwarded)

    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
