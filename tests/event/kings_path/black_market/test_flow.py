"""
Flow test Event / King's Path / Black Market (bot/activities/event/kings_path/black_market/): tách từ test_flow.py.
Ảnh dùng chung ở ../screens/ (không chép sang thư mục nhiệm vụ).
"""
import sys
from types import SimpleNamespace
import unittest

import cv2

from bot.activities.event.kings_path import black_market
from bot.activities.event.kings_path.black_market.constants import (
    CONFIRM as BM_CONFIRM,
    INSTANT_REFRESH as BM_REFRESH,
    MENU_BLACK_MARKET as BM_MENU,
    SLOTS as BM_SLOTS)
from bot.context import TEMPLATE_DIR, BotContext
from tests.flow import Step, back, end, tap, tap_at, tap_pct
from tests.event.kings_path.common import SCREENS, KP, _run
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)


class BlackMarketFlow(unittest.TestCase):
    def test_black_market_open_day5(self):
        """Black Market: đang ở Day 1 -> bấm Day 5 (đã mở) -> tab Market Trade đang chọn -> dòng Go
        trên cùng (0 / 1) -> Go (phần sau Go: TODO)."""
        flow = [
            Step("day1_day5_open.png", tap(f"{KP}/Day/day5.png")),
            Step("day5_market_trade.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 100, "day": 5}})
        self.assertIn("Black Market: done 0, target 100", device.logs)

    def test_black_market_open_tab(self):
        """Day 5 đang mở tab War Horn: bấm tab Market Trade (ảnh "chưa chọn") -> Go."""
        flow = [
            Step("day5_war_horn.png", tap(f"{KP}/Tab/marketTrade.png")),
            Step("day5_market_trade.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        _run(self, flow, {black_market.KEY: {"value": 100, "day": 5}})

    def test_black_market_buy(self):
        """Black Market (đã mua 0, mục tiêu 2): Go -> bấm giữa (Chợ) -> icon Black Market -> mua món 1
        -> Confirm -> món 2 -> Confirm -> đủ, Back, xong. Món trả kim cương (ô 3) không bấm."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_screen.png", tap_at(*BM_SLOTS[0])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_screen.png", tap_at(*BM_SLOTS[1])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 2, "day": 5}})
        self.assertIn("Black Market: bought 2 / 2, done", device.logs)
        self.assertIn(black_market.KEY, device.daily_done)

    def test_black_market_refresh_and_continue(self):
        """Mua hết bộ hàng (nút giá đều xám) -> Instant Refresh -> chờ 3 s -> bộ mới -> mua tiếp tới đủ."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_screen.png?sold_out", tap(BM_REFRESH)),
            Step("bm_screen.png", tap_at(*BM_SLOTS[0])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 1, "day": 5}})
        self.assertIn("Black Market: all bought, Instant Refresh (0 / 1)", device.logs)
        self.assertIn(black_market.KEY, device.daily_done)

    def test_black_market_refresh_retry(self):
        """Bấm Refresh mà ô vật phẩm 1 vẫn y như trước (chờ 2 s + 10 lần x 1 s): bấm Refresh lại; lần
        này ô 1 đổi -> mua tiếp."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_screen.png?sold_out", tap(BM_REFRESH)),
            Step("bm_screen.png?sold_out", tap(BM_REFRESH)),
            Step("bm_screen_2.png", tap_at(*BM_SLOTS[0])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 1, "day": 5}})
        self.assertIn("Black Market: items unchanged after 10 checks, Refresh again", device.logs)

    def test_black_market_gem_items_skipped(self):
        """Bộ hàng nhiều món trả kim cương (ảnh thật): chỉ bấm món trả tài nguyên (ô 2 — 100k Iron)."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_screen_3.png", tap_at(*BM_SLOTS[1])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        _run(self, flow, {black_market.KEY: {"value": 1, "day": 5}})

    def test_black_market_buyable_slots(self):
        """Món mua được = nút giá xanh, không trả kim cương (7 mẫu thật, vị trí icon kim cương xê dịch
        theo độ dài số; ô đã mua xám)."""
        buyable = sys.modules["bot.activities.event.kings_path.black_market.run"]._buyable
        bot = SimpleNamespace(crop=BotContext.crop, find=lambda tpl, threshold, screen: (
            None if cv2.matchTemplate(screen, cv2.imread(str(TEMPLATE_DIR / tpl)), cv2.TM_CCOEFF_NORMED).max()
            < threshold else (0, 0)))
        expected = {
            "bm_screen.png": "110111", "bm_bought.png": "110110", "bm_screen_2.png": "110111",
            "bm_screen_3.png": "010000", "bm_refresh_gems.png": "001001", "bm_screen_4.png": "000001",
            "bm_screen_5.png": "000000", "bm_screen_6.png": "101000", "bm_screen_7.png": "001000",
        }
        for name, want in expected.items():
            screen = cv2.imread(str(SCREENS / name))
            got = "".join("1" if buyable(bot, screen, x, y) else "0" for x, y in BM_SLOTS)
            self.assertEqual(got, want, name)

    def test_black_market_paid_refresh(self):
        """Hết món, Instant Refresh bằng kim cương (nút "Instant Refresh 50"): vẫn bấm như bình thường;
        có hộp xác nhận thì Confirm (không tính là 1 lần mua)."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_refresh_gems.png?sold_out", tap(BM_REFRESH)),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_screen.png", tap_at(*BM_SLOTS[0])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 1, "day": 5}})
        self.assertIn("Black Market: confirm paid refresh", device.logs)
        self.assertIn("Black Market: buy confirmed (1 / 1)", device.logs)


if __name__ == "__main__":
    unittest.main()
