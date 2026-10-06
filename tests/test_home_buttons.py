"""
test_home_buttons.py — 2 nút Start All / Stop All ở màn Home:
Start All bật khi còn thiết bị chưa chạy, Stop All bật khi có thiết bị đang chạy.
"""
import os
import unittest


class HomeStartStopAllTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt5.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def _state(self, view) -> tuple[str, bool, str, bool]:
        return (view.start_all_button.text(), view.start_all_button.isEnabled(),
                view.stop_all_button.text(), view.stop_all_button.isEnabled())

    def test_no_device_disables_both(self):
        from ui.home_view import HomeView
        view = HomeView()
        self.assertEqual(self._state(view), ("Start All(0)", False, "Stop All(0)", False))

    def test_counts_enable_only_relevant_button(self):
        from ui.home_view import HomeView
        view = HomeView()

        view.set_run_counts(0, 3)                      # mới load, chưa máy nào chạy
        self.assertEqual(self._state(view), ("Start All(3)", True, "Stop All(0)", False))

        view.set_run_counts(2, 3)                      # 2 đang chạy, 1 còn idle
        self.assertEqual(self._state(view), ("Start All(1)", True, "Stop All(2)", True))

        view.set_run_counts(3, 3)                      # hết máy idle -> Start All tắt
        self.assertEqual(self._state(view), ("Start All(0)", False, "Stop All(3)", True))

        view.set_run_counts(0, 0)                      # không còn thiết bị
        self.assertEqual(self._state(view), ("Start All(0)", False, "Stop All(0)", False))

    def test_signals(self):
        from ui.home_view import HomeView
        view = HomeView()
        emitted: list[str] = []
        view.start_all_requested.connect(lambda: emitted.append("start"))
        view.stop_all_requested.connect(lambda: emitted.append("stop"))

        view.set_run_counts(2, 3)                      # cả 2 nút đều bật
        view.start_all_button.click()
        view.stop_all_button.click()
        self.assertEqual(emitted, ["start", "stop"])

        emitted.clear()
        view.set_run_counts(0, 3)                      # Stop All tắt -> click không phát tín hiệu
        view.stop_all_button.click()
        self.assertEqual(emitted, [])


class InitializationStartStopAllTests(unittest.TestCase):
    """Tab Initialization của từng thiết bị: 2 nút Start All / Stop All riêng biệt."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt5.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def _tab(self):
        from ui.tabs.initialization_tab import InitializationTab
        return InitializationTab(device_id="127.0.0.1:5555")

    def _state(self, tab) -> tuple[str, bool, str, bool]:
        start, stop = tab.controls["button9"], tab.controls["buttonStopAll"]
        return (start.text(), start.isEnabled(), stop.text(), stop.isEnabled())

    def test_starts_disabled(self):
        tab = self._tab()
        self.assertEqual(self._state(tab), ("Start All", False, "Stop All", False))

    def test_counts_enable_only_relevant_button(self):
        tab = self._tab()

        tab.set_run_counts(0, 3)
        self.assertEqual(self._state(tab), ("Start All(3)", True, "Stop All(0)", False))

        tab.set_run_counts(2, 3)
        self.assertEqual(self._state(tab), ("Start All(1)", True, "Stop All(2)", True))

        tab.set_run_counts(3, 3)
        self.assertEqual(self._state(tab), ("Start All(0)", False, "Stop All(3)", True))

    def test_signals(self):
        tab = self._tab()
        emitted: list[str] = []
        tab.start_all_clicked.connect(lambda: emitted.append("start"))
        tab.stop_all_clicked.connect(lambda: emitted.append("stop"))

        tab.set_run_counts(2, 3)                      # cả 2 nút đều bật
        tab.controls["button9"].click()
        tab.controls["buttonStopAll"].click()
        self.assertEqual(emitted, ["start", "stop"])

        emitted.clear()
        tab.set_run_counts(0, 3)                      # Stop All tắt -> không phát tín hiệu
        tab.controls["buttonStopAll"].click()
        self.assertEqual(emitted, [])

    def test_buttons_are_side_by_side_and_clear(self):
        """2 nút nằm cạnh nhau, không đè lên GroupBox hay nút Start."""
        tab = self._tab()
        start, stop = tab.controls["button9"], tab.controls["buttonStopAll"]
        group, button_start = tab.controls["groupBox2"], tab.controls["buttonStart"]

        s, p = start.geometry(), stop.geometry()
        self.assertLessEqual(s.right(), p.left())           # Start nằm bên trái Stop
        self.assertTrue(group.geometry().bottom() <= s.top() or
                        not group.geometry().intersects(s))  # không đè GroupBox
        self.assertFalse(button_start.geometry().intersects(s))
        self.assertFalse(button_start.geometry().intersects(p))
        self.assertFalse(s.intersects(p))                    # 2 nút không chồng nhau

    def test_device_view_forwards_signals_and_counts(self):
        from ui.device_view import DeviceView
        view = DeviceView("127.0.0.1:5555")
        emitted: list[str] = []
        view.start_all_requested.connect(lambda: emitted.append("start"))
        view.stop_all_requested.connect(lambda: emitted.append("stop"))
        view.set_run_counts(1, 2)
        self.assertEqual(self._state(view.initialization_tab),
                         ("Start All(1)", True, "Stop All(1)", True))
        view.initialization_tab.controls["button9"].click()
        view.initialization_tab.controls["buttonStopAll"].click()
        self.assertEqual(emitted, ["start", "stop"])


if __name__ == "__main__":
    unittest.main()
