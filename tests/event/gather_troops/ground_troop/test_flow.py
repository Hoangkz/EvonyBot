"""
Flow test Event / Gather Troops / Ground Troop
(bot/activities/event/gather_troops/ground_troop/): quà đăng nhập -> nút dưới
Event Center -> danh sách event -> Gather Troops (giống hệt Cultivate Generals tới
05_gather_be_prepared.png), rồi dừng.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (chép từ
tests/event/gather_troops/cultivate_generals/screens/).
"""
import unittest
from pathlib import Path

from bot.activities import event
from bot.activities.event.gather_troops import ground_troop
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
KEY = ground_troop.KEY
SETTINGS = {KEY: {"value": 20000, "level": 13, "day": 2}}

# Toạ độ bấm cứng (lệch so với template, xem bot/activities/event/constants.py):
LOGIN_GIFT_ICON = (361, 148)   # icon Login Gifts ở cột phải (góc dưới trái cũng có)
LOGIN_REWARD = (122, 587)      # chữ "Login Gifts" (56, 141) + (66, 446): ô quà Day 5
EVENT_BUTTON = (369, 281)      # chữ "Event Center" (359, 241) + (10, 40)


def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng (xoá nút / icon chưa có ảnh chụp thật)."""
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


VARIANTS = {
    # Màn chính đã nhận quà: không còn icon Login Gifts (cột phải + góc dưới trái).
    "claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    # Danh sách event không có Gather Troops.
    "no_gather_troops": _blank(330, 400, 15, 85),
}


class GroundTroopFlow(unittest.TestCase):
    def test_main_flow(self):
        """Nhận quà đăng nhập trước, rồi Event Center -> danh sách event -> Gather Troops."""
        flow = [
            Step("01_main_login_gift.png", tap_at(*LOGIN_GIFT_ICON)),
            Step("02_login_gifts.png", tap_at(*LOGIN_REWARD), back()),
            # 03_main vẫn còn icon Login Gifts nhưng quà đã nhận trong lượt này -> bỏ qua.
            Step("03_main.png", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
            Step("05_gather_be_prepared.png", end()),
        ]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_disabled_skips(self):
        """Ô Ground Troop chọn 0: không làm gì."""
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, {KEY: {"value": 0, "level": None, "day": 2}})

    def test_gather_troops_not_found(self):
        """Danh sách event không có Gather Troops: cuộn xuống 4 lần rồi BACK, bỏ nhiệm vụ."""
        flow = [
            Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png?no_gather_troops",
                 *[swipe(50, 80, 50, 50) for _ in range(4)], back()),
            Step("03_main.png?claimed", end()),
        ]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)


if __name__ == "__main__":
    unittest.main()
