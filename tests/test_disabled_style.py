"""
test_disabled_style.py — nút bị disable phải hiển thị nền xám (theme chung)
để phân biệt rõ với nút đang bật.
"""
import os
import unittest

from PyQt5.QtGui import QColor


class DisabledButtonStyleTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt5.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])
        from ui import theme
        theme.apply(cls.app)                     # áp stylesheet toàn cục như khi chạy app thật

    def _bg(self, button) -> QColor:
        """Mẫu màu nền tại vùng có padding (không dính chữ)."""
        button.resize(170, 44)
        button.show()
        self.app.processEvents()
        return button.grab().toImage().pixelColor(10, 22)

    @staticmethod
    def _is_gray(color: QColor) -> bool:
        """Xám = các channel gần bằng nhau và KHÔNG phải trắng tinh (255)."""
        channels = (color.red(), color.green(), color.blue())
        return max(channels) - min(channels) <= 12 and max(channels) < 252

    def test_stylesheet_declares_disabled_rule(self):
        from ui import theme
        self.assertIn("QPushButton:disabled", theme.STYLESHEET)
        for key in ("disabled_bg", "disabled_border", "disabled_text"):
            self.assertIn(theme.COLORS[key], theme.STYLESHEET)

    def test_plain_button_turns_gray_when_disabled(self):
        from PyQt5.QtWidgets import QPushButton
        button = QPushButton("Start All(0)")
        button.setEnabled(True)
        enabled = self._bg(button)
        button.setEnabled(False)
        disabled = self._bg(button)

        self.assertFalse(self._is_gray(enabled), f"nút bật phải không phải xám: {enabled.name()}")
        self.assertTrue(self._is_gray(disabled), f"nút tắt phải xám: {disabled.name()}")
        self.assertLess(disabled.lightness(), enabled.lightness())

    def test_home_start_stop_all_gray_when_disabled(self):
        from ui.home_view import HomeView
        view = HomeView()

        view.set_run_counts(0, 0)                # không có gì để chạy/tắt -> cả 2 tắt
        self.assertTrue(self._is_gray(self._bg(view.start_all_button)))
        self.assertTrue(self._is_gray(self._bg(view.stop_all_button)))

        view.set_run_counts(1, 2)                # cả 2 nút đều bật
        self.assertFalse(self._is_gray(self._bg(view.start_all_button)))
        self.assertFalse(self._is_gray(self._bg(view.stop_all_button)))

        view.set_run_counts(2, 2)                # hết máy idle -> Start All tắt, Stop All bật
        self.assertTrue(self._is_gray(self._bg(view.start_all_button)))
        self.assertFalse(self._is_gray(self._bg(view.stop_all_button)))

    def test_tab_start_stop_all_gray_when_disabled(self):
        from ui.tabs.initialization_tab import InitializationTab
        tab = InitializationTab(device_id="127.0.0.1:5555")
        start, stop = tab.controls["button9"], tab.controls["buttonStopAll"]

        self.assertTrue(self._is_gray(self._bg(start)))     # mới tạo -> cả 2 tắt
        self.assertTrue(self._is_gray(self._bg(stop)))

        tab.set_run_counts(0, 3)
        self.assertFalse(self._is_gray(self._bg(start)))    # Start All bật
        self.assertTrue(self._is_gray(self._bg(stop)))      # Stop All vẫn tắt

        tab.set_run_counts(3, 3)
        self.assertTrue(self._is_gray(self._bg(start)))     # Start All tắt
        self.assertFalse(self._is_gray(self._bg(stop)))     # Stop All bật


if __name__ == "__main__":
    unittest.main()