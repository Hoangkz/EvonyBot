import os
import unittest
from unittest import mock

import cv2
import numpy as np

from bot.activities.daily_activities.buy_daily import run as general
from bot.activities.daily_activities.constants import HAMMER_DONE, STAMINA_REACHED
from bot.activities.result import TaskResult
from bot.activities.daily_activities.buy_daily.run import JOB


def run_buy(ctx, settings):
    """Chạy nhiệm vụ mua Stamina + Hammer như bảng priority.py khai báo (JOB['run']); nhiệm vụ tự lưu từng món vào DB."""
    return JOB["run"](ctx, settings)


class _PurchaseBot:
    def __init__(self, visible):
        self.visible = visible
        self.taps = []
        self.logs = []
        self._daily_image_positions = {}

    def check(self):
        pass

    def screenshot(self):
        return np.zeros((720, 400, 3), dtype=np.uint8)

    def find(self, path, **kwargs):
        return self.visible.get(path)

    def tap(self, x, y, **kwargs):
        self.taps.append((x, y))

    def tap_percent(self, x, y, **kwargs):
        self.taps.append((x * 4, y * 7.2))

    def swipe_percent(self, *args, **kwargs):
        pass

    def back(self, **kwargs):
        pass

    def log(self, message):
        self.logs.append(message)


class DailyGeneralPurchaseTests(unittest.TestCase):
    @mock.patch.object(general, "delay", lambda *args, **kwargs: None)
    @mock.patch.object(general, "open_features", lambda bot: True)
    def test_buy_hammers_selects_all_then_confirms(self):
        bot = _PurchaseBot({
            "DailyActivites/ActivitiesBuyDaily/bua.png": (180, 300),
            "DailyActivites/ActivitiesBuyDaily/plus.png": (250, 400),
        })

        self.assertTrue(general.buy_all_hammers(bot))

        self.assertEqual(bot.taps, [(250, 400)] * general.HAMMER_MAX_TAPS + [(200, 510)])

    @staticmethod
    def _ctx(done):
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add
        bot.daily_keys.side_effect = lambda: list(done)
        return bot

    @mock.patch("bot.activities.daily_activities.buy_daily.run.buy_all_hammers", return_value=True)
    @mock.patch("bot.activities.daily_activities.buy_daily.run.buy_stamina", return_value=True)
    def test_general_marks_each_item_and_does_not_rebuy(self, stamina, hammers):
        done = set()
        bot = self._ctx(done)
        settings = {"General": {"buy_stamina": True, "stamina_quantity": 20, "buy_all_hammers": True}}
        for _ in range(2):   # lần hai: đã xong hôm nay, worker không mua lại
            run_buy(bot, settings)

        stamina.assert_called_once_with(bot, 20)
        hammers.assert_called_once_with(bot)
        self.assertEqual(done, {f"{STAMINA_REACHED} 20", HAMMER_DONE})

    @mock.patch("bot.activities.daily_activities.buy_daily.run.buy_all_hammers", return_value=True)
    @mock.patch("bot.activities.daily_activities.buy_daily.run.buy_stamina", return_value=True)
    def test_raising_the_target_buys_only_the_rest(self, stamina, hammers):
        """Đã mua tới mốc 10 và Hammer: nâng lên 16 -> chỉ mua Stamina tới 16 (popup tự tính phần còn lại), không mua Hammer."""
        done = {f"{STAMINA_REACHED} 10", HAMMER_DONE}
        bot = self._ctx(done)
        run_buy(bot, {"General": {"buy_stamina": True, "stamina_quantity": 16,
                                                      "buy_all_hammers": True}})
        stamina.assert_called_once_with(bot, 16)
        hammers.assert_not_called()
        self.assertIn(f"{STAMINA_REACHED} 16", done)
        stamina.reset_mock()
        run_buy(bot, {"General": {"buy_stamina": True, "stamina_quantity": 10}})   # hạ mốc: không mua
        stamina.assert_not_called()

    @mock.patch("bot.activities.daily_activities.buy_daily.run.buy_all_hammers", return_value=False)
    @mock.patch("bot.activities.daily_activities.buy_daily.run.buy_stamina", return_value=True)
    def test_failed_item_is_not_marked_but_the_other_is(self, stamina, hammers):
        done = set()
        bot = self._ctx(done)
        run_buy(bot, {"General": {"buy_stamina": True, "stamina_quantity": 10,
                                                      "buy_all_hammers": True}})
        self.assertEqual(done, {f"{STAMINA_REACHED} 10"})   # lần sau chỉ mua lại Hammer
        stamina.reset_mock()
        run_buy(bot, {"General": {"buy_stamina": True, "stamina_quantity": 10,
                                                      "buy_all_hammers": True}})
        stamina.assert_not_called()
        self.assertEqual(hammers.call_count, 2)

    # Tổng giá đo trên popup thật khi hôm nay đã mua 1 cái (screens/06..24): số lượng -> giá.
    REAL_TOTALS = ((1, 200), (2, 400), (3, 600), (4, 800), (5, 1000), (10, 2200), (13, 3400), (16, 5000), (17, 5800),
                   (18, 6600), (19, 8200), (20, 9800), (21, 11400), (22, 14600), (23, 17800), (30, 59400))

    def test_stamina_total_matches_real_popups(self):
        for quantity, cost in self.REAL_TOTALS:
            self.assertEqual(general.stamina_total(1, quantity), cost, quantity)

    def test_stamina_price_by_tier(self):
        self.assertEqual(general.STAMINA_MILESTONES, (10, 16, 20))
        prices = [general.stamina_price(n) for n in (1, 10, 11, 16, 17, 19, 20, 22, 23, 25, 26)]
        self.assertEqual(prices, [200, 200, 400, 400, 800, 800, 1600, 1600, 3200, 3200, 6400])

    def test_stamina_done_from_cost(self):
        self.assertEqual(general.stamina_done([200]), list(range(10)))
        self.assertEqual(general.stamina_done([400]), list(range(10, 16)))
        self.assertEqual(general.stamina_done([800]), [16, 17, 18])
        self.assertEqual(general.stamina_done([1600]), [19, 20, 21])
        self.assertEqual(general.stamina_done([300]), [])

    def test_reads_cost_from_real_popup(self):
        bot = mock.Mock()
        bot.crop.side_effect = lambda im, x, y, w, h: im[y:y + h, x:x + w]
        for name, cost in (("06_stamina_popup_1", 200), ("07_stamina_popup_10", 2200), ("10_hammer_popup_max", 2000),
                           ("11_stamina_popup_2", 400), ("12_stamina_popup_3", 600), ("13_stamina_popup_4", 800),
                           ("14_stamina_popup_5", 1000), ("15_stamina_popup_13", 3400),
                           ("16_stamina_popup_16", 5000), ("17_stamina_popup_23", 17800),
                           ("18_stamina_popup_30", 59400), ("26_stamina_popup_1_price_400", 400), ("19_stamina_popup_17", 5800),
                           ("20_stamina_popup_18", 6600), ("21_stamina_popup_19", 8200),
                           ("22_stamina_popup_20", 9800), ("23_stamina_popup_21", 11400),
                           ("24_stamina_popup_22", 14600)):
            image = cv2.imread(os.path.join(os.path.dirname(__file__), "buy_daily", "screens", name + ".png"))
            self.assertEqual(general.read_cost(bot, image), cost, name)

    def _popup(self, costs, target):
        bot = _PurchaseBot({"DailyActivites/ActivitiesBuyDaily/plus.png": (313, 354)})
        with mock.patch.object(general, "read_cost", side_effect=costs),                 mock.patch.object(general, "stamina_done", wraps=general.stamina_done):
            ok = general._buy_in_popup(bot, bot.screenshot(), target)
        return ok, bot

    def test_popup_fresh_day_buys_all(self):
        ok, bot = self._popup([200, 2000], 10)
        self.assertTrue(ok)
        self.assertEqual(bot.taps, [(313, 354)] * 9 + [(200, 464)])

    def test_popup_one_bought_buys_nine(self):
        ok, bot = self._popup([200, general.stamina_total(1, 10)], 10)
        self.assertTrue(ok)
        # 9 lần "+", 1 lần "-" (lùi từ 10 xuống 9), rồi mua
        self.assertEqual(bot.taps, [(313, 354)] * 9 + [(400 - 313, 354), (200, 464)])

    def test_popup_distinguishes_last_tier_before_1600(self):
        """Mốc 20, giá 800 (đã mua 16-18): tổng 4 cái khác nhau theo số đã mua -> chỉ mua phần thiếu."""
        ok, bot = self._popup([800, general.stamina_total(18, 4)], 20)
        self.assertTrue(ok)
        self.assertEqual(bot.taps, [(313, 354)] * 3 + [(400 - 313, 354)] * 2 + [(200, 464)])

    def test_popup_already_enough_buys_nothing(self):
        ok, bot = self._popup([400], 10)
        self.assertTrue(ok)
        self.assertEqual(bot.taps, [])

    def test_popup_unreadable_cost_buys_nothing(self):
        ok, bot = self._popup([None], 10)
        self.assertFalse(ok)
        self.assertEqual(bot.taps, [])

    @mock.patch("bot.activities.daily_activities.buy_daily.run.buy_all_hammers", return_value=True)
    @mock.patch("bot.activities.daily_activities.buy_daily.run.buy_stamina", return_value=True)
    def test_general_buys_only_ticked_items(self, stamina, hammers):
        bot = self._ctx(set())
        run_buy(bot, {"General": {"buy_all_hammers": True}})
        stamina.assert_not_called()
        hammers.assert_called_once_with(bot)


if __name__ == "__main__":
    unittest.main()
