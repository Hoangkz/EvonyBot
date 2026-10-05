"""
Flow test Daily Activities / Black Market (bot/activities/daily_activities/black_market/), luồng mới `after_go`
(giống hệt King's Path Black Market sau Go): về thành, Chợ ở giữa -> menu "Black Market" -> mua các món không trả
bằng kim cương (mua hết bộ thì Instant Refresh) cho đủ BUY_GOAL = 3 lần -> Back, xong hôm nay. Thêm phần mở nhiệm vụ
(open_task_or_finish, giao diện CŨ): thẻ Black Market đã "Completed" -> xong hôm nay, không bấm Go.

Ảnh dùng chung, không chép (ảnh chụp nguyên màn hình giả lập 396x704): bm_* ở tests/event/kings_path/screens/ (màn
Black Market dùng chung với King's Path; bm_screen: 5 món mua được, ô 3 trả kim cương); 11..33 ở
tests/daily_activities/screens/ (33: thẻ Black Market "Completed", máy 21943; 05: danh sách Activity bản mới, Claim All
xám, máy 21913).
"""
import unittest

from bot.activities.daily_activities.black_market.constants import BUY_GOAL, LABEL
from bot.activities.daily_activities.black_market.run import TASK, after_go
from bot.activities.daily_activities.common import _search_list, open_task_or_finish, task_titles
from bot.activities.daily_activities.constants import TASK_OPENED
from bot.activities.event.kings_path.black_market.constants import (
    CONFIRM,
    INSTANT_REFRESH,
    MENU_BLACK_MARKET,
    SLOTS,
)
from tests.daily_activities import DAILY, KP, TESTS_DIR, old_grid_completed
from tests.flow import Step, back, end, run_flow, tap, tap_at, tap_pct

SCREENS = TESTS_DIR
# Sau Go: Chợ ở giữa màn thành -> menu Chợ -> icon "Black Market".
TO_MARKET = [
    Step(f"{KP}bm_city.png", tap_pct(50, 50)),
    Step(f"{KP}bm_menu.png", tap(MENU_BLACK_MARKET)),
]


def _buy(slot):
    """Bấm món `slot` (nút giá xanh) -> hộp "Are you sure ...?" -> Confirm (+1 lần mua)."""
    return [Step(f"{KP}bm_screen.png", tap_at(*SLOTS[slot])), Step(f"{KP}bm_confirm.png", tap(CONFIRM))]


def _blank(y0, y1, x0, x1):
    def apply(bgr):
        bgr[y0:y1, x0:x1] = 40
        return bgr
    return apply


def _sold_out(bgr):
    """Mọi nút giá xám (đã mua hết) — tô đen 6 nút giá."""
    for x, y in SLOTS:
        bgr[y - 10:y + 10, x - 44:x + 44] = 40
    return bgr


VARIANTS = {
    "sold_out": _sold_out,
    # Mua hết mà không có nút Instant Refresh (199, 584).
    "no_refresh": lambda bgr: _blank(565, 605, 100, 300)(_sold_out(bgr)),
}


def _after_go(bot, _settings):
    return after_go(bot)


class BlackMarketFlow(unittest.TestCase):
    def test_after_go_buys_three(self):
        """Mua món 1, 2 rồi món 4 (món 3 trả kim cương, bỏ qua) -> đủ 3 lần -> Back, xong hôm nay."""
        self.assertEqual(BUY_GOAL, 3)
        flow = [
            *TO_MARKET,
            *_buy(0), *_buy(1), *_buy(3),
            Step(f"{KP}bm_bought.png", back()),
            Step(f"{KP}bm_city.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {})
        self.assertIn(f"{LABEL}: bought 3 / 3, done", device.logs)
        self.assertIn(LABEL, device.daily_done)

    def test_refresh_then_buy(self):
        """Vào màn đã mua hết bộ -> Instant Refresh -> bộ mới -> mua đủ 3 lần."""
        flow = [
            *TO_MARKET,
            Step(f"{KP}bm_screen.png?sold_out", tap(INSTANT_REFRESH)),
            *_buy(0), *_buy(1), *_buy(3),
            Step(f"{KP}bm_bought.png", back()),
            Step(f"{KP}bm_city.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {}, variants=VARIANTS)
        self.assertIn(f"{LABEL}: all bought, Instant Refresh (0 / 3)", device.logs)
        self.assertIn(LABEL, device.daily_done)

    def test_no_refresh_stops_not_done(self):
        """Mua được 1 lần, hết hàng mà không có Instant Refresh -> Back, dừng, không đánh dấu xong."""
        flow = [
            *TO_MARKET,
            *_buy(0),
            Step(f"{KP}bm_screen.png?no_refresh", back()),
            Step(f"{KP}bm_city.png", end(result=False)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {}, variants=VARIANTS)
        self.assertNotIn(LABEL, device.daily_done)

    def test_open_task_completed_card(self):
        """Giao diện cũ: lưới Activity -> cuộn -> thẻ Black Market "Completed" -> xong hôm nay, không bấm Go (return False)."""
        flow = old_grid_completed("33_old_grid_end_black_market_completed.png")
        device = run_flow(self, lambda bot, _s: open_task_or_finish(bot, TASK), SCREENS, flow, {})
        self.assertIn(LABEL, device.daily_done)

    def test_list_gray_claim_all_not_tapped(self):
        """Giao diện mới (21913): Claim All xám (không có gì để nhận, vẫn khớp ảnh mẫu 0,86) -> không bấm; dòng
        "Buy items from the Black Market" -> Go (336, 489)."""
        flow = [
            Step(f"{DAILY}05_activity_claim_all_gray.png", tap_at(336, 489)),
            Step(f"{KP}bm_city.png", end(result=TASK_OPENED)),
        ]
        device = run_flow(self, lambda bot, _s: _search_list(bot, task_titles(TASK), 3), SCREENS, flow, {})
        self.assertNotIn("Daily Activities: Claim All", device.logs)


if __name__ == "__main__":
    unittest.main()
