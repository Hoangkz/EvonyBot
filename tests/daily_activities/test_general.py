import unittest
from unittest import mock

import numpy as np

from bot.activities.daily_activities import general
from bot.activities.daily_activities.constants import BUY_HAMMERS, BUY_STAMINA
from bot.activities.result import TaskResult
from bot.worker.daily import policy


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
    def test_buy_stamina_uses_selected_quantity(self):
        bot = _PurchaseBot({
            "JoinBoss/Buy/buystamina.png": (180, 300),
            "JoinBoss/Buy/plus.png": (250, 400),
        })

        self.assertTrue(general.buy_stamina(bot, 10))

        self.assertEqual(bot.taps[:-1], [(250, 400)] * 9)
        self.assertEqual(bot.taps[-1], (200, 510))

    @mock.patch.object(general, "delay", lambda *args, **kwargs: None)
    def test_buy_hammers_selects_all_then_confirms(self):
        bot = _PurchaseBot({
            "JoinBoss/Buy/bua.png": (180, 300),
            "JoinBoss/Buy/plus.png": (250, 400),
        })

        self.assertTrue(general.buy_all_hammers(bot))

        self.assertEqual(bot.taps, [(230, 402), (200, 510)])

    @mock.patch("bot.activities.daily_activities.run.buy_all_hammers", return_value=True)
    @mock.patch("bot.activities.daily_activities.run.buy_stamina", return_value=True)
    def test_general_marks_purchases_done(self, stamina, hammers):
        done = set()
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add

        settings = {"General": {"buy_stamina": True, "stamina_quantity": 20, "buy_all_hammers": True}}
        for _ in range(2):   # lần hai: đã xong hôm nay, worker không mua lại
            policy.run_buy_stamina_task(bot, settings)
            policy.run_buy_hammers_task(bot, settings)

        stamina.assert_called_once_with(bot, 20)
        hammers.assert_called_once_with(bot)
        self.assertEqual(done, {BUY_STAMINA, BUY_HAMMERS})


if __name__ == "__main__":
    unittest.main()
