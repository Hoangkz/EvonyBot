"""
Flow test Daily Activities / Buy Daily (bot/activities/daily_activities/buy_daily/): màn chính -> bấm góc trên
bên phải (mở Store) -> Items -> War -> cuộn -> 50 Stamina -> popup -> mua; và Special -> Hammer -> popup -> mua.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704. Tài khoản chụp đã mua 1 Stamina trước đó
(06: số lượng 1 giá 200; 07: số lượng 10 giá 2,200 = 9 x 200 + 1 x 400) và chưa mua Hammer (Daily Limit 10 / 10).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities.buy_daily import run as buy
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at, tap_pct

SCREENS = Path(__file__).parent / "screens"
PLUS = f"{buy.BUY}/plus.png"
PLUS_XY = (313, 354)            # tâm nút "+" của popup (khớp plus.png 1,00)
MINUS_XY = (396 - 313, 354)     # "-" đối xứng với "+"
CONFIRM = (198, 464)            # nút mua xanh, plus[1] + 110

OPEN_STORE = [
    Step("01_home.png", tap_pct(*buy.FEATURES_BUTTON)),
    Step("02_store_membership.png", tap(f"{buy.BUY}/item.png")),
]


class BuyDailyFlow(unittest.TestCase):
    def test_buy_stamina_when_one_already_bought(self):
        """Mốc 10, đã mua 1: giá 200 (đã mua 0-9) -> "+" 9 lần -> 2,200 = đã mua đúng 1 -> "-" một lần
        (9 cái) -> mua."""
        flow = [
            *OPEN_STORE,
            Step("03_items_resources.png", tap(f"{buy.BUY}/war.png")),
            Step("04_items_war.png", swipe()),
            Step("05_war_scrolled.png", tap_at(334, 468, tol=20)),
            Step("06_stamina_popup_1.png", *[tap(PLUS)] * 9),
            Step("07_stamina_popup_10.png", tap_at(*MINUS_XY), tap_at(*CONFIRM)),
            Step("01_home.png", end(result=True)),
        ]
        run_flow(self, lambda bot, _s: buy.buy_stamina(bot, 10), SCREENS, flow, {})

    def test_stamina_target_already_reached_buys_nothing(self):
        """Giá ở số lượng 1 là 400 = đã mua 10-15 cái, mốc 10 đã đủ: chỉ Back đóng popup, không bấm "+" / mua."""
        flow = [
            *OPEN_STORE,
            Step("03_items_resources.png", tap(f"{buy.BUY}/war.png")),
            Step("04_items_war.png", swipe()),
            Step("05_war_scrolled.png", tap_at(334, 468, tol=20)),
            Step("26_stamina_popup_1_price_400.png", back()),
            Step("01_home.png", end(result=True)),
        ]
        run_flow(self, lambda bot, _s: buy.buy_stamina(bot, 10), SCREENS, flow, {})

    def test_buy_hammers_takes_the_max(self):
        flow = [
            *OPEN_STORE,
            Step("03_items_resources.png", tap(f"{buy.BUY}/special.png")),
            Step("08_special_list.png", tap(f"{buy.BUY}/checkSpecial.png"), tap_pct(87.5, 35)),
            Step("09_hammer_popup_1.png", tap_at(PLUS_XY[0] - 20, PLUS_XY[1] + 2), tap_at(*CONFIRM)),
            Step("01_home.png", end(result=True)),
        ]
        run_flow(self, lambda bot, _s: buy.buy_all_hammers(bot), SCREENS, flow, {})

    def test_hammers_sold_out_buys_nothing(self):
        """Dòng Hammer "Daily Limit: 0 / 10", nút giá xám: không bấm gì thêm, coi là xong."""
        flow = [
            *OPEN_STORE,
            Step("03_items_resources.png", tap(f"{buy.BUY}/special.png")),
            Step("25_special_hammer_sold_out.png", end(result=True)),
        ]
        run_flow(self, lambda bot, _s: buy.buy_all_hammers(bot), SCREENS, flow, {})


if __name__ == "__main__":
    unittest.main()
