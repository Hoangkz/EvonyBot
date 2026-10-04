"""
Flow test Daily Activities / Offering (bot/activities/daily_activities/offering/), phiên bản giao
diện mới: màn chính -> Quests -> tab Activity -> Claim All -> cuộn -> dòng "Use the Offer feature in
Shrine" -> Go -> về thành, Đền thờ ở giữa (nhận ra theo ảnh mẫu civ) -> bấm Đền thờ -> menu "Offer"
-> màn Offer. TODO: bấm Offer Tribute / Offer Gems (chờ người dùng quyết).

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (01..04 chép từ
tests/daily_activities/screens/; 05 sau Go, 06 menu Đền thờ, 07 màn Offer, 08 popup Offer Gems).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities import offering
from bot.activities.daily_activities.constants import GO_BUTTON, TASK_OPENED
from bot.activities.daily_activities.offering.constants import (
    MENU_OFFER,
    OFFER_SCREEN,
    POPUP_OFFER,
    POPUP_PLUS,
)
from bot.activities.daily_activities.offering.run import after_go
from bot.activities.daily_activities.common import open_task, task_cards, task_titles
from tests.daily_activities import CLAIM_ALL_ONCE, SCROLL, TO_ACTIVITY, open_task_of, reopen
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
OFFER_GO_Y = 475   # Go dưới tiêu đề "Use the Offer feature in Shrine" (y 434) trên 04_activity_scrolled
SHRINE = (197, 345)   # chỗ khớp ảnh mẫu Đền thờ civ 1 trên 05_after_go (bấm vào công trình, không bấm giữa)
TO_GO = [
    *TO_ACTIVITY, *CLAIM_ALL_ONCE,
    Step("03_activity_top.png", SCROLL),
    Step("04_activity_scrolled.png", tap(GO_BUTTON)),
]


def _open_and_after_go(bot, _settings):
    """open_task (bấm Go) rồi phần sau Go của Offer."""
    if open_task(bot, task_titles(offering.TASK), task_cards(offering.TASK)) != TASK_OPENED:
        return False
    return after_go(bot)


class OfferingFlow(unittest.TestCase):
    def test_open_task(self):
        flow = [*TO_GO, Step("01_main.png", end(result=TASK_OPENED))]
        device = run_flow(self, open_task_of(offering.TASK), SCREENS, flow, {})
        go = [e for _, e in device.events if e[0] == "tap"][-1]
        self.assertEqual(go[2], OFFER_GO_Y, "Go của dòng Offer, không phải dòng khác")

    def test_second_offer_row(self):
        """Dòng Offer lần 2 ("...for 3 time(s)", 1/3) đang ở danh sách: tiêu đề vẫn khớp (chỉ cắt phần chữ
        "Use the Offer feature in Shrine") -> bấm đúng Go dưới nó (y 491, không phải 398 / 584).
        Claim All đang xám (0,86 < ngưỡng 0,9): không bấm."""
        flow = [
            *reopen("04b_activity_offer_second.png"),
            Step("04b_activity_offer_second.png", tap(GO_BUTTON)),
            Step("01_main.png", end(result=TASK_OPENED)),
        ]
        device = run_flow(self, open_task_of(offering.TASK), SCREENS, flow, {})
        go = [e for _, e in device.events if e[0] == "tap"][-1]
        self.assertEqual(go[2], 491)

    def test_row_without_recognised_button_is_not_done(self):
        """Thấy tiêu đề Offer nhưng không nhận ra nút nào dưới nó (ảnh biến thể: che nút Go y 491):
        không bấm, KHÔNG đánh dấu xong (lần sau thử lại)."""
        from bot.activities.daily_activities.common import open_task_or_finish

        def hide_go(bgr):
            bgr[478:505, 290:385] = 30
            return bgr
        flow = [*reopen("04b_activity_offer_second.png?no_go"),
                Step("04b_activity_offer_second.png?no_go", end(result=False))]
        device = run_flow(self, lambda bot, _s: open_task_or_finish(bot, offering.TASK), SCREENS, flow,
                          {}, variants={"no_go": hide_go})
        self.assertNotIn("Offering", device.daily_done)

    def test_after_go_opens_offer_screen(self):
        """Sau Go: Đền thờ ở giữa (khớp ảnh mẫu civ 1) -> bấm vào nó -> menu -> Offer -> màn Offer ->
        Offer Gems -> popup: Cost 25 (chưa offer) -> "+" 5 lần -> Cost 675 -> Offer (6 lần)."""
        flow = [
            *TO_GO,
            Step("05_after_go.png", tap_at(*SHRINE)),
            Step("06_shrine_menu.png", tap(MENU_OFFER)),
            # Offer Gems 6 lần, hôm nay chưa offer: popup Cost 25 (số lượng 1 -> đã làm 0) -> "+" 5 lần
            # -> Cost 675 = đúng 6 lượt từ 0 -> Offer.
            Step("07_offer_screen.png", tap(OFFER_SCREEN)),
            Step("08_offer_gems_popup.png", *[tap(POPUP_PLUS)] * 5),
            # Offer -> "Congratulations!" (15_offer_done) -> Back 2 lần về thành.
            Step("14_offer_gems_popup_6.png", tap(POPUP_OFFER)),
            Step("15_offer_done.png", back(), back()),
            Step("01_main.png", end(result=True)),
        ]
        device = run_flow(self, _open_and_after_go, SCREENS, flow, {},
                          ctx_settings={"Daily Activities": {"Offer Gems": 6}})
        self.assertEqual(device.ctx.civilization, 1, "chưa biết civ: khớp mẫu Đền thờ civ 1 -> gán civ 1")
        self.assertIn("Offering", device.daily_done)
        self.assertIn("daily_offering_reached_6", device.daily_done)

    def test_offer_gems_zero_does_not_spend_gems(self):
        """Ô "Offer Gems" = 0: tới màn Offer nhưng không bấm Offer Gems."""
        flow = [
            *TO_GO,
            Step("05_after_go.png", tap_at(*SHRINE)),
            Step("06_shrine_menu.png", tap(MENU_OFFER)),
            Step("07_offer_screen.png", end(result=True)),
        ]
        run_flow(self, _open_and_after_go, SCREENS, flow, {},
                 ctx_settings={"Daily Activities": {"Offer Gems": 0}})


class OfferPopupTests(unittest.TestCase):
    """_offer_in_popup với Cost giả (không mua lại lượt đã offer hôm nay)."""

    def _run(self, times, costs):
        from unittest import mock
        from bot.activities.daily_activities.offering import run as offer_run
        bot = mock.Mock()
        bot.find.return_value = (1, 1)
        with mock.patch.object(offer_run, "read_cost", side_effect=costs):
            result = offer_run._offer_in_popup(bot, times)
        taps = [c.args for c in bot.tap.call_args_list]
        return result, taps, bot

    def test_already_enough_does_not_buy(self):
        """Cost số lượng 1 = 1.500 (đã làm >= 15), chọn 10: đóng popup, không bấm "+" / Offer."""
        result, taps, bot = self._run(10, [1500])
        self.assertTrue(result)
        self.assertEqual(len(taps), 1)   # chỉ bấm X đóng popup
        bot.record.assert_called()

    def test_steps_back_when_more_done_than_guessed(self):
        """Cost 100 -> đã làm 2 hoặc 3; chọn 6: "+" 3 lần (4 lượt từ 2), Cost 1.075 = 4 lượt từ 3
        (100+200+200+400 = 900 khác 4 lượt từ 2 = 100+100+200+200 = 600) -> thực tế đã làm 3 -> "-" 1 lần -> Offer 3 lượt."""
        from bot.activities.daily_activities.offering.run import offer_total
        result, taps, bot = self._run(6, [100, offer_total(3, 4)])
        self.assertTrue(result)
        self.assertEqual(len(taps), 3 + 1 + 1)   # "+" x3, "-" x1, Offer
        self.assertEqual(bot.back.call_count, 2)   # Offer xong: Back 2 lần

    def test_unreadable_cost_does_not_buy(self):
        result, taps, _ = self._run(10, [None])
        self.assertFalse(result)
        self.assertEqual(len(taps), 1)   # đóng popup

    def test_done_today_depends_on_quantity(self):
        """Xong với 6 lượt; tăng lên 10 ở tab UI -> chưa xong; giảm về 5 -> xong."""
        from unittest import mock
        from bot.activities.daily_activities.offering.run import is_done_today, mark_done
        done = {}
        bot = mock.Mock()
        bot.is_daily_done.side_effect = lambda k: k in done
        bot.mark_daily_done.side_effect = lambda k: done.__setitem__(k, "t")
        bot.daily_keys.side_effect = lambda: list(done)
        bot.settings = {"Daily Activities": {"Offer Gems": 6}}
        mark_done(bot, 6)
        self.assertTrue(is_done_today(bot))
        bot.settings = {"Daily Activities": {"Offer Gems": 10}}
        self.assertFalse(is_done_today(bot))
        bot.settings = {"Daily Activities": {"Offer Gems": 5}}
        self.assertTrue(is_done_today(bot))

    def test_no_go_marks_done_with_target_zero(self):
        """Dòng Offer không còn Go / không có trong danh sách (open_task_or_finish đánh dấu mục tiêu 0):
        xong hôm nay dù đang chọn 30 lượt."""
        from unittest import mock
        from bot.activities.daily_activities.common import mark_task_done
        from bot.activities.daily_activities.offering.run import is_done_today
        done = {}
        bot = mock.Mock()
        bot.is_daily_done.side_effect = lambda k: k in done
        bot.mark_daily_done.side_effect = lambda k: done.__setitem__(k, "t")
        bot.daily_keys.side_effect = lambda: list(done)
        bot.settings = {"Daily Activities": {"Offer Gems": 30}}
        mark_task_done(bot, offering.TASK, 0)
        self.assertEqual(set(done), {"Offering", "daily_offering_reached_0"})
        self.assertTrue(is_done_today(bot))


if __name__ == "__main__":
    unittest.main()
