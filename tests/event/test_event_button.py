"""
Chọn nút event trên màn chính (bot/activities/event/common.py find_event_button): trên chính ảnh
vừa thấy nút "•••", tìm đuôi ruy băng (Images/Event/ribbonTail.png) trong 2 vùng cố định — vùng
nào trả về toạ độ thì vùng đó đúng, ra MỘT nút duy nhất; không vùng nào thấy thì bấm ngay dưới
chữ "Event Center" như trước. Nút trên cùng bên phải (đuôi (331, 105)) không phải nút event.

Ảnh screens/ribbon/ (mỗi máy 10 khung khác nhau nhất trong 60 khung chụp liên tục 1 phút):
  01-10  máy 21913: Event Center ở cột 2 (281, 106), nút event ngay dưới: đuôi (253, 173)
         vùng trái -> bấm (283, 145).
  11-20  máy 21923: Event Center bị đẩy xuống (359, 309), bên dưới không có nút: đuôi
         (253, 105) vùng trái -> bấm (283, 77).
  kings_path/screens/03_main.png  bố cục cũ: đuôi (331, 308) vùng phải -> bấm (361, 280).
"""
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

import cv2

from bot.activities.event.common import find_event_button
from bot.activities.event.constants import MAIN_SCREEN
from bot.context import BotContext

HERE = Path(__file__).parent
BELOW_CENTER = [f"{i:02d}.png" for i in range(1, 11)]   # máy 21913
TOP_ROW = [f"{i:02d}.png" for i in range(11, 21)]        # máy 21923
TOL = 3


class EventButtonTests(unittest.TestCase):
    def setUp(self):
        self.ctx = BotContext(SimpleNamespace(serial="t"), threading.Event(), None, lambda _: None)

    def _screen(self, path):
        image = cv2.imread(str(HERE / path))
        if image is None:
            self.skipTest(f"thiếu ảnh {path}")
        self.assertIsNotNone(self.ctx.find(MAIN_SCREEN, screen=image), f"{path}: không phải màn chính")
        return image

    def assertNear(self, got, expected):
        self.assertIsNotNone(got)
        self.assertLessEqual(abs(got[0] - expected[0]), TOL, got)
        self.assertLessEqual(abs(got[1] - expected[1]), TOL, got)

    def test_left_column_below_event_center(self):
        for name in BELOW_CENTER:
            with self.subTest(frame=name):
                self.assertNear(find_event_button(self.ctx, self._screen(f"screens/ribbon/{name}")),
                                (283, 145))

    def test_left_column_top_row(self):
        # Nút trên cùng bên phải (361, 77) cũng có ruy băng nhưng không phải nút event.
        for name in TOP_ROW:
            with self.subTest(frame=name):
                self.assertNear(find_event_button(self.ctx, self._screen(f"screens/ribbon/{name}")),
                                (283, 77))

    def test_right_column(self):
        self.assertNear(find_event_button(self.ctx, self._screen("kings_path/screens/03_main.png")),
                        (361, 280))

    def test_lower_threshold(self):
        # Đuôi ruy băng bị đè 2 điểm (khớp 0,851 < ngưỡng đầu 0,86) vẫn tìm được ở ngưỡng thấp hơn.
        screen = self._screen("screens/ribbon/01.png")
        screen[173, 252] = screen[173, 254] = (50, 75, 150)
        score, _ = self.ctx.best_match("Event/ribbonTail.png", screen=screen, region=(60, 12, 70, 40))
        self.assertLess(score, 0.86)
        self.assertNear(find_event_button(self.ctx, screen), (283, 145))

    def test_no_ribbon_uses_event_center(self):
        # Không thấy ruy băng ở cả 2 vùng: bấm Event Center (359, 309) + (10, 40) như trước.
        screen = self._screen("screens/ribbon/11.png")
        screen[100:111, 248:259] = 0
        self.assertNear(find_event_button(self.ctx, screen), (369, 349))


if __name__ == "__main__":
    unittest.main()
