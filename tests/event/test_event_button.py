"""
Chọn nút event trên màn chính (bot/activities/event/common.py find_event_button): trên chính ảnh
vừa thấy nút "•••", tìm đuôi ruy băng (Images/Event/ribbonTail.png) trong 2 vùng cố định — vùng
nào trả về toạ độ thì vùng đó đúng, ra MỘT nút duy nhất; không vùng nào thấy thì trả None
(event đã hết). Nút trên cùng bên phải (đuôi (331, 105)) không phải nút event.

Ảnh screens/ribbon/ (mỗi máy 10 khung khác nhau nhất trong 60 khung chụp liên tục 1 phút):
  01-10  máy 21913: Event Center ở cột 2 (281, 106), nút event ngay dưới: đuôi (253, 173)
         vùng trái -> bấm (283, 145).
  11-20  máy 21923: Event Center bị đẩy xuống (359, 309), bên dưới không có nút: đuôi
         (253, 105) vùng trái -> bấm (283, 77).
  kings_path/screens/03_main.png  bố cục cũ: đuôi (331, 308) vùng phải -> bấm (361, 280).

Icon nút event (Images/Event/ButtonIcon/, bot/activities/event/button_icon.py) được thử TRƯỚC ruy băng:
  screens/button_icon/01-02  màn chính có icon lâu đài ma ngay dưới Event Center (chụp 2026-10-26,
         máy 21923, 2 lần cách nhau vài phút): tâm ảnh mẫu haunted_castle.png (18x12) ở (360, 211).
Các ảnh ruy băng ở trên là event cũ, không có icon -> rơi về cách tìm ruy băng.
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

    def test_icon_found_first(self):
        # Icon lâu đài ma khớp (điểm >= 0,8) -> bấm tâm ảnh mẫu.
        from bot.activities.event.button_icon import find_button_icon
        for name in ("01.png", "02.png"):
            with self.subTest(frame=name):
                screen = self._screen(f"screens/button_icon/{name}")
                self.assertNear(find_button_icon(self.ctx, screen), (360, 211))
                self.assertNear(find_event_button(self.ctx, screen), (360, 211))

    def test_fruit_basket_icon(self):
        # Giỏ trái cây (ảnh mẫu 10x8 cắt từ chính ảnh trong join_monster_war): tâm ảnh mẫu (354, 290).
        from bot.activities.event.button_icon import find_button_icon
        for i in (5, 8, 12):
            with self.subTest(frame=i):
                screen = self._screen(f"../join_monster_war/screens/boss_count_{i}.png")
                self.assertNear(find_button_icon(self.ctx, screen), (354, 290))

    def test_beer_mugs_icon(self):
        # Cốc bia (ảnh mẫu 32x20 cắt tay, chỉ khớp tốt khi so màu thẳng): tâm ảnh mẫu (360, 286).
        from bot.activities.event.button_icon import find_button_icon
        for i in (1, 5, 10):
            with self.subTest(frame=i):
                screen = self._screen(f"screens/event_center/{i:02d}.png")
                self.assertNear(find_button_icon(self.ctx, screen), (360, 286))

    def test_beer_mugs_variants(self):
        # Hai khung cốc bia mà ảnh gốc bỏ sót: bọt sát ngưỡng (0,79-0,80, có thùng gỗ) và hết bọt (0,53-0,57).
        # Nút nằm hàng trên cột trái (283, 77): tâm ảnh mẫu lệch (-1, +6) so với điểm bấm ruy băng.
        from bot.activities.event.button_icon import find_button_icon
        for path in ("event/city_building/screens/civ6/workshop/01.png", "event/city_building/screens/civ4/rally_spot/01.png",
                     "event/city_building/screens/civ5/war_hall/01.png", "event/city_building/screens/civ1/embassy/01.png"):
            with self.subTest(frame=path):
                screen = self._screen(f"../{path}")
                self.assertNear(find_button_icon(self.ctx, screen), (282, 83))

    def test_icon_missing_falls_back_to_ribbon(self):
        # Màn event cũ không có icon lâu đài (điểm < 0,8): vẫn ra nút theo ruy băng như trước,
        # và không có chỗ nào khớp nhầm.
        from bot.activities.event.button_icon import find_button_icon
        for path, expected in (("screens/ribbon/01.png", (283, 145)), ("kings_path/screens/03_main.png", (361, 280))):
            with self.subTest(frame=path):
                screen = self._screen(path)
                self.assertIsNone(find_button_icon(self.ctx, screen))
                self.assertNear(find_event_button(self.ctx, screen), expected)

    def test_no_ribbon_means_event_ended(self):
        # Không thấy ruy băng ở cả 2 vùng: None (Event Center vẫn thấy -> event đã hết).
        screen = self._screen("screens/ribbon/11.png")
        screen[100:111, 248:259] = 0
        self.assertIsNone(find_event_button(self.ctx, screen))


if __name__ == "__main__":
    unittest.main()
