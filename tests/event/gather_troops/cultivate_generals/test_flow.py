"""
Flow test Event / Gather Troops / Cultivate Generals
(bot/activities/event/gather_troops/cultivate_generals/): quà đăng nhập -> nút dưới
Event Center -> danh sách event -> Gather Troops -> tab "Recruit More" -> "Go" ->
Generals -> Cultivate -> Quick Cultivate -> x100 / Cancel tới 1000
(xem .claude/skills/flow-test/flows.md).

Mỗi nhiệm vụ Event có thư mục test riêng theo cấu trúc bot/activities/event/
(tests/event/<event>/<nhiệm vụ>/), kèm screens/ của nó.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704.
"""
import unittest
from pathlib import Path

import cv2

from bot.activities import event
from bot.activities.event.gather_troops import cultivate_generals
from bot.context import TEMPLATE_DIR
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
KEY = cultivate_generals.KEY
SETTINGS = {KEY: {"enabled": True, "day": 1}}

# Toạ độ bấm cứng (lệch so với template, xem bot/activities/event/constants.py):
LOGIN_GIFT_ICON = (361, 148)   # icon Login Gifts ở cột phải (góc dưới trái cũng có)
LOGIN_REWARD = (122, 587)      # chữ "Login Gifts" (56, 141) + (66, 446): ô quà Day 5
EVENT_BUTTON = (369, 281)      # chữ "Event Center" (359, 241) + (10, 40)
FIRST_GO = (335, 344)          # nút Go gần tab Recruit More nhất (dòng "500 time(s)")
FAVORITE_FILTER = (139, 208)   # trái tim lọc yêu thích trên danh sách Generals
LAST_GENERAL = (40, 634)       # (10%, 90%) của 396x704: thẻ tướng cuối sau khi kéo xuống

# Đã nhận quà / đã đi qua: chỉ cần màn chính, danh sách event, Gather Troops.
TO_RECRUIT_MORE = [
    Step("03_main.png", tap_at(*EVENT_BUTTON)),
    Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
    Step("05_gather_be_prepared.png", tap("Event/GatherTroops/recruitMore.png")),
]
# Danh sách Generals đã bỏ tích tim lọc -> kéo nhanh xuống cuối 3 lần, bấm thẻ cuối
# -> màn chi tiết tướng -> Cultivate -> bấm tab Quick Cultivate.
TO_QUICK_CULTIVATE = [
    Step("07_generals.png?heart_off",
         *[swipe(50, 85, 50, 15) for _ in range(3)], tap_at(*LAST_GENERAL)),
    Step("09_general_detail.png", tap("Event/GatherTroops/CultivateButton/1.png")),
    Step("10_cultivate.png", tap("Event/GatherTroops/quickCultivate.png")),
]


def x100_loop(done: int) -> list[Step]:
    """Tab Quick Cultivate: bấm "Cultivate x100" (+100), nút đổi thành "Cancel" -> bấm
    Cancel -> lại x100 ... tới khi đạt 1000 thì activity dừng (ở màn có Cancel)."""
    steps = []
    while True:
        steps.append(Step("11_quick_cultivate.png", tap("Event/GatherTroops/cultivateX100.png")))
        done += 100
        if done >= 1000:
            return steps + [Step("13_quick_cultivate_cancel.png", end())]
        steps.append(Step("13_quick_cultivate_cancel.png", tap("Event/GatherTroops/cancel.png")))


# Đi qua dòng Go "300 / 500" (đọc được 300): 7 lần x100 thì đủ 1000.
TO_CULTIVATE = [
    Step("07_generals.png", tap_at(*FAVORITE_FILTER)),   # tim lọc đang tích -> bỏ tích
    *TO_QUICK_CULTIVATE,
    *x100_loop(300),
]
# Vào thẳng danh sách Generals (không qua dòng Go nên không biết số đã làm): tới tab
# Quick Cultivate thì dừng, không bấm x100 (tránh tiêu gems khi không biết lúc nào dừng).
FROM_GENERALS_UNTICKED = [
    *TO_QUICK_CULTIVATE,
    Step("11_quick_cultivate.png", end()),
]


def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng (xoá nút / icon chưa có ảnh chụp thật)."""
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


def _heart_off(bgr):
    """Biến thể ảnh: trái tim lọc trên danh sách Generals đã bỏ tích (dán ảnh tim xám
    của Join Boss vào đúng chỗ tim đỏ)."""
    off = cv2.imread(str(TEMPLATE_DIR / "JoinBoss/favoriteOff.png"))
    h, w = off.shape[:2]
    x, y = FAVORITE_FILTER[0] - w // 2, FAVORITE_FILTER[1] - h // 2
    bgr[y:y + h, x:x + w] = off
    return bgr


VARIANTS = {
    # Danh sách Generals, tim lọc đã bỏ tích (chưa có ảnh chụp thật).
    "heart_off": _heart_off,
    # Màn chính đã nhận quà: không còn icon Login Gifts (cột phải + góc dưới trái).
    "claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    # Tab Recruit More không còn nút Go nào (mọi dòng đã xong).
    "no_go": _blank(320, 480, 290, 380),
    # Danh sách event không có Gather Troops.
    "no_gather_troops": _blank(330, 400, 15, 85),
}


class EventFlow(unittest.TestCase):
    def test_main_flow(self):
        """Nhận quà đăng nhập trước, rồi Go của Cultivate Generals (đọc 300) -> bỏ tích tim
        lọc -> thẻ tướng cuối -> Cultivate -> Quick Cultivate -> x100 / Cancel tới 1000."""
        flow = [
            Step("01_main_login_gift.png", tap_at(*LOGIN_GIFT_ICON)),
            Step("02_login_gifts.png", tap_at(*LOGIN_REWARD), back()),
            # 03_main vẫn còn icon Login Gifts nhưng quà đã nhận trong lượt này -> bỏ qua.
            *TO_RECRUIT_MORE,
            Step("06_gather_recruit_more.png", tap_at(*FIRST_GO)),
            *TO_CULTIVATE,
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(KEY, device.daily_done)   # đủ 1000 -> đánh dấu xong

    def test_claim_all_first(self):
        """Thấy "Claim All" thì bấm trước mọi thứ, rồi mới xử lý tab Recruit More."""
        flow = [
            Step("08_gather_claim_all.png", tap("Event/claimAll.png")),
            Step("06_gather_recruit_more.png", tap_at(*FIRST_GO)),
            *TO_CULTIVATE,
        ]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_progress_unknown_does_not_use_gems(self):
        """Không qua dòng Go (không biết số đã làm): tới Quick Cultivate thì dừng, không
        bấm Cultivate x100, không đánh dấu xong."""
        device = run_flow(self, event.run, SCREENS, FROM_GENERALS_UNTICKED, SETTINGS,
                          variants=VARIANTS)
        self.assertNotIn(KEY, device.daily_done)

    def test_cultivate_button_4_columns(self):
        """Tướng có hàng 4 nút (thêm Specialty): nút Cultivate nhỏ hơn, ở (152, 677)."""
        flow = [
            FROM_GENERALS_UNTICKED[0],
            Step("12_general_detail_4_buttons.png", tap("Event/GatherTroops/CultivateButton/2.png")),
            *FROM_GENERALS_UNTICKED[2:],
        ]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_favorite_already_unticked(self):
        """Tim lọc đã bỏ tích sẵn: không bấm tim, kéo xuống cuối và mở tướng luôn."""
        run_flow(self, event.run, SCREENS, FROM_GENERALS_UNTICKED, SETTINGS, variants=VARIANTS)

    def test_no_go_marks_done(self):
        """Tab Recruit More không còn Go: đánh dấu nhiệm vụ đã xong rồi kết thúc."""
        flow = [
            Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
            *TO_RECRUIT_MORE[1:],
            Step("06_gather_recruit_more.png?no_go", end()),
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(KEY, device.daily_done)

    def test_already_done_skips(self):
        """Đã đánh dấu xong từ lần reset server gần nhất: không làm gì."""
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, daily_done={KEY: "2026-10-01T08:00:00"})

    def test_disabled_skips(self):
        """Ô Cultivate Generals không tích: không làm gì."""
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, {KEY: {"enabled": False, "day": 1}})

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
