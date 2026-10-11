"""
Hàm run riêng của các nhiệm vụ Daily Activities do worker gọi thẳng (luật chạy: bot/worker/daily/policy.py, khai báo ở
bot/worker/daily/tasks.py; việc làm trong game: bot/activities/daily_activities/): nhiệm vụ Daily thường (chưa xong thì hẹn thử lại), nhiệm vụ theo giờ, nhận thưởng cuối. Crazy Eggs: xem
tests/event_center/test_task.py.
"""
import importlib
import unittest
from datetime import datetime
from unittest import mock

from bot.activities.result import NOT_DONE, TaskResult
from bot.worker.registry import REGISTRY

daily = importlib.import_module("bot.worker.daily.policy")
DEFS = {d.key: d for d in REGISTRY}


class FakeBot:
    def __init__(self, done=None):
        self.done = dict(done or {})
        self.again_after = None

    def is_daily_done(self, key):
        return key in self.done

    def mark_daily_done(self, key):
        self.done[key] = datetime.now().isoformat(timespec="seconds")

    def done_at(self, key):
        return self.done.get(key)

    def check(self):
        pass

    def log(self, message):
        pass

    record = log


class DailyTaskTests(unittest.TestCase):
    def test_enabled_follows_tab_settings(self):
        self.assertTrue(DEFS["daily_offering"].enabled({"Offering": True}))
        self.assertFalse(DEFS["daily_offering"].enabled({"Offering": False}))
        self.assertTrue(DEFS["daily_alliance_donation"].enabled({"Alliance Donation": 4}))
        self.assertFalse(DEFS["daily_alliance_donation"].enabled({"Alliance Donation": 0}))
        self.assertTrue(DEFS["daily_buy_stamina"].enabled({"General": {"buy_stamina": True, "stamina_quantity": 10}}))
        self.assertFalse(DEFS["daily_buy_stamina"].enabled({"General": {"buy_stamina": True, "stamina_quantity": 0}}))
        self.assertTrue(DEFS["daily_buy_hammers"].enabled({"General": {"buy_all_hammers": True}}))
        self.assertFalse(DEFS["daily_rewards"].enabled({"Alliance Donation": 4}))   # chỉ có việc theo giờ
        self.assertTrue(DEFS["daily_rewards"].enabled({"Offering": True}))

    def test_not_finished_task_retries_then_gives_up(self):
        bot = FakeBot()
        with mock.patch.object(daily, "run_task", return_value=NOT_DONE):
            for attempt in range(daily.MAX_ATTEMPTS):
                bot.again_after = None
                DEFS["daily_offering"].run(bot, {"Offering": True})
                if attempt < daily.MAX_ATTEMPTS - 1:
                    self.assertEqual(bot.again_after, daily.RETRY_AFTER)
        self.assertIsNone(bot.again_after)   # lần cuối: bỏ cuộc, không hẹn nữa
        self.assertNotIn("Offering", bot.done)

    def test_finished_task_marked_done(self):
        bot = FakeBot()
        with mock.patch.object(daily, "run_task", return_value=TaskResult(done=True)):
            DEFS["daily_offering"].run(bot, {"Offering": True})
        self.assertIn("Offering", bot.done)
        self.assertIsNone(bot.again_after)

    def test_done_task_skipped(self):
        bot = FakeBot({"Offering": "2026-10-11T09:00:00"})
        with mock.patch.object(daily, "run_task") as run:
            DEFS["daily_offering"].run(bot, {"Offering": True})
        run.assert_not_called()

    def test_hourly_not_due_waits_remaining(self):
        """Mới thử 1 giờ trước, chu kỳ 4h: không thử, hẹn lại sau ~3 giờ."""
        from datetime import timedelta
        tried = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        from bot.activities.daily_activities import alliance_donation
        bot = FakeBot({alliance_donation.constants.TRIED_KEY: tried})
        attempt = mock.Mock()
        task = next(task for task, _ in daily.HOURLY if task.key == "daily_alliance_donation")
        with mock.patch.object(daily, "HOURLY", ((task, attempt),)):
            DEFS["daily_alliance_donation"].run(bot, {"Alliance Donation": 4})
        attempt.assert_not_called()
        self.assertAlmostEqual(bot.again_after, 3 * 3600, delta=5)

    def test_rewards_not_marked_until_all_done(self):
        """Còn việc đã tích chưa xong: nhận thưởng nhưng chưa lưu "đã nhận", hẹn thử lại."""
        bot = FakeBot()
        with mock.patch.object(daily, "collect_activity_rewards") as collect, \
                mock.patch.object(daily.gifts, "run_gift_claims") as gifts:
            DEFS["daily_rewards"].run(bot, {"Offering": True})
        collect.assert_called_once()
        gifts.assert_not_called()
        self.assertNotIn(daily.REWARDS, bot.done)
        self.assertEqual(bot.again_after, daily.RETRY_AFTER)

    def test_rewards_all_done_runs_gifts(self):
        bot = FakeBot({"Offering": "x"})
        with mock.patch.object(daily, "collect_activity_rewards"), \
                mock.patch.object(daily.gifts, "run_gift_claims") as gifts:
            DEFS["daily_rewards"].run(bot, {"Offering": True})
        gifts.assert_called_once()
        self.assertIn(daily.REWARDS, bot.done)
        self.assertIsNone(bot.again_after)

    def test_offering_done_depends_on_quantity(self):
        """Xong với 6 lượt; tăng lên 10 ở tab UI -> chưa xong; giảm về 5 -> xong."""
        task = next(t for t in daily.DAILY_TASKS if t.label == "Offering")
        bot = FakeBot()
        daily.record_result(bot, task.key, task.label, TaskResult(done=True, reached=6))
        bot.daily_keys = lambda: list(bot.done)
        self.assertTrue(daily.is_complete(bot, task, {"Offer Gems": 6}))
        self.assertFalse(daily.is_complete(bot, task, {"Offer Gems": 10}))
        self.assertTrue(daily.is_complete(bot, task, {"Offer Gems": 5}))

    def test_offering_target_zero_is_done_whatever_the_quantity(self):
        """Dòng Offer không còn Go (mục tiêu 0): xong hôm nay dù đang chọn 30 lượt."""
        task = next(t for t in daily.DAILY_TASKS if t.label == "Offering")
        bot = FakeBot()
        daily.record_result(bot, task.key, task.label, TaskResult(done=True, reached=0))
        bot.daily_keys = lambda: list(bot.done)
        self.assertEqual(set(bot.done), {"Offering", "daily_offering_reached_0"})
        self.assertTrue(daily.is_complete(bot, task, {"Offer Gems": 30}))


if __name__ == "__main__":
    unittest.main()
