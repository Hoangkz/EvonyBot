"""
MẪU flow test nhiệm vụ Event — copy sang tests/event/<event>/<nhiệm vụ>/ cùng với
bot/activities/event/_template/my_task/ (xem bot/activities/event/_template/__init__.py).

Bước 01..05 (màn chính -> event vừa mở) giống mọi nhiệm vụ Event; mẫu này dùng tạm ảnh
của Cultivate Generals. Khi copy: đổi SCREENS thành `Path(__file__).parent / "screens"`,
chép ảnh 01..05 vào screens/ rồi thêm Step cho các màn riêng sau 05.

Ảnh là ảnh chụp nguyên màn hình giả lập 396x704.
"""
import unittest
from pathlib import Path

from bot.activities.event._template import my_task
from bot.activities.event.common import EventState
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at

SCREENS = Path(__file__).parents[2] / "gather_troops" / "cultivate_generals" / "screens"
KEY = my_task.KEY
SETTINGS = {KEY: {"enabled": True, "day": 1}}

# Toạ độ bấm cứng (lệch so với template, xem bot/activities/event/constants.py):
LOGIN_GIFT_ICON = (361, 148)   # icon Login Gifts ở cột phải (góc dưới trái cũng có)
LOGIN_REWARD = (122, 587)      # chữ "Login Gifts" (56, 141) + (66, 446): ô quà Day 5
EVENT_BUTTON = (369, 281)      # chữ "Event Center" (359, 241) + (10, 40)

# Màn chính -> event vừa mở: giống mọi nhiệm vụ Event.
TO_EVENT = [
    Step("01_main_login_gift.png", tap_at(*LOGIN_GIFT_ICON)),
    Step("02_login_gifts.png", tap_at(*LOGIN_REWARD), back()),
    # 03_main vẫn còn icon Login Gifts nhưng quà đã nhận trong lượt này -> bỏ qua.
    Step("03_main.png", tap_at(*EVENT_BUTTON)),
    Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
]


def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng (xoá nút / icon chưa có ảnh chụp thật)."""
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


VARIANTS = {
    # Màn chính đã nhận quà: không còn icon Login Gifts (cột phải + góc dưới trái).
    "claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    # Danh sách event không có icon event.
    "no_event": _blank(330, 400, 15, 85),
}


def _run(bot, settings):
    """Mẫu chưa nằm trong TASKS của event/run.py nên gọi thẳng. Khi copy và đã thêm vào
    TASKS thì dùng `event.run` (from bot.activities import event) như các test khác."""
    task = settings.get(KEY)
    if task and task.get("enabled", True):
        my_task.run(bot, task, EventState())


class MyTaskFlow(unittest.TestCase):
    def test_main_flow(self):
        """Nhận quà đăng nhập -> Event Center -> danh sách event -> event -> phần riêng."""
        flow = [
            *TO_EVENT,
            # TODO: thay bằng các bước riêng của nhiệm vụ, bước cuối end().
            Step("05_gather_be_prepared.png", tap("Event/GatherTroops/CultivateGenerals/recruitMore.png")),
            Step("06_gather_recruit_more.png", end()),
        ]
        run_flow(self, _run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_already_done_skips(self):
        """Đã đánh dấu xong từ lần reset server gần nhất: không làm gì."""
        flow = [Step("03_main.png", end())]
        run_flow(self, _run, SCREENS, flow, SETTINGS, daily_done={KEY: "2026-10-01T08:00:00"})

    def test_disabled_skips(self):
        """Ô nhiệm vụ không bật: không làm gì."""
        flow = [Step("03_main.png", end())]
        run_flow(self, _run, SCREENS, flow, {KEY: {"enabled": False, "day": 1}})

    def test_event_not_found(self):
        """Danh sách event không có icon event: cuộn xuống 4 lần rồi BACK, bỏ nhiệm vụ."""
        flow = [
            Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png?no_event",
                 *[swipe(50, 80, 50, 50) for _ in range(4)], back()),
            Step("03_main.png?claimed", end()),
        ]
        run_flow(self, _run, SCREENS, flow, SETTINGS, variants=VARIANTS)


if __name__ == "__main__":
    unittest.main()
