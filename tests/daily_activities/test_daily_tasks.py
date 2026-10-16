"""
Nhiệm vụ Daily Activities trong bảng nhiệm vụ của worker (bot/worker/priority.py, dựng ở bot/worker/tasks.py): luật của từng
việc là dict {run, enabled, done, every} dựng cạnh code của việc (bot/activities/daily_activities/common.py): được tích chưa, hôm nay xong chưa (đọc DB), việc
theo giờ. Crazy Eggs: xem tests/event_center/test_task.py.
"""
import importlib
import unittest
from datetime import datetime, timedelta
from unittest import mock

from bot.activities.result import NOT_DONE, TaskResult
from bot.activities.daily_activities import alliance_donation
from bot.worker.tasks import REGISTRY, build_task

catalog = importlib.import_module("bot.activities.daily_activities.common")
DEFS = {d.key: d for d in REGISTRY}


class FakeBot:
    def __init__(self, done=None):
        self.done = dict(done or {})

    def is_daily_done(self, key):
        return key in self.done

    def mark_daily_done(self, key):
        self.done[key] = datetime.now().isoformat(timespec="seconds")

    def done_at(self, key):
        return self.done.get(key)

    def daily_keys(self):
        return list(self.done)

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
        buy = DEFS["daily_buy_general"].enabled
        self.assertTrue(buy({"General": {"buy_stamina": True, "stamina_quantity": 10}}))
        self.assertFalse(buy({"General": {"buy_stamina": True, "stamina_quantity": 0}}))
        self.assertTrue(buy({"General": {"buy_all_hammers": True}}))
        self.assertFalse(buy({"General": {}}))
        self.assertFalse(DEFS["daily_rewards"].enabled({"Alliance Donation": 4}))   # chỉ có việc theo giờ
        self.assertTrue(DEFS["daily_rewards"].enabled({"Offering": True}))

    def test_not_finished_task_is_not_marked(self):
        """Chưa xong: không lưu "xong hôm nay" (worker chuyển nhiệm vụ xuống cuối danh sách)."""
        bot = FakeBot()
        with mock.patch.object(catalog, "run_task", return_value=NOT_DONE):
            DEFS["daily_offering"].run(bot, {"Offering": True})
        self.assertNotIn("daily_offering", bot.done)
        self.assertFalse(DEFS["daily_offering"].done(bot, {"Offering": True}))

    def test_finished_task_marked_done(self):
        bot = FakeBot()
        with mock.patch.object(catalog, "run_task", return_value=TaskResult(done=True)):
            DEFS["daily_offering"].run(bot, {"Offering": True})
        self.assertIn("daily_offering", bot.done)
        self.assertTrue(DEFS["daily_offering"].done(bot, {"Offering": True}))

    def test_done_is_read_from_the_db(self):
        bot = FakeBot({"daily_offering": "2026-10-11T09:00:00"})
        self.assertTrue(DEFS["daily_offering"].done(bot, {"Offering": True}))

    def test_offering_done_follows_the_chosen_quantity(self):
        """Xong với 6 lượt; tăng lên 10 ở tab UI -> chưa xong; giảm về 5 hoặc về 6 -> xong lại (đọc DB mỗi lần)."""
        task = DEFS["daily_offering"]
        bot = FakeBot()
        catalog.record_result(bot, "daily_offering", TaskResult(done=True, reached=6))
        self.assertTrue(task.done(bot, {"Offer Gems": 6}))
        self.assertFalse(task.done(bot, {"Offer Gems": 10}))
        self.assertTrue(task.done(bot, {"Offer Gems": 5}))
        self.assertTrue(task.done(bot, {"Offer Gems": 6}))

    def test_offering_target_zero_is_done_whatever_the_quantity(self):
        """Dòng Offer không còn Go (mục tiêu 0): xong hôm nay dù đang chọn 30 lượt."""
        bot = FakeBot()
        catalog.record_result(bot, "daily_offering", TaskResult(done=True, reached=0))
        self.assertEqual(set(bot.done), {"daily_offering", "daily_offering_reached_0"})
        self.assertTrue(DEFS["daily_offering"].done(bot, {"Offer Gems": 30}))

    def test_hourly_due_only_after_the_interval(self):
        """Chu kỳ 4h: mới làm 1 giờ trước thì chưa tới giờ; qua 4 giờ thì tới giờ. Giờ lưu trong DB, mỗi vòng chỉ so giờ."""
        task = DEFS["daily_alliance_donation"]
        settings = {"Alliance Donation": 4}
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        old = (datetime.now() - timedelta(hours=5)).isoformat(timespec="seconds")
        self.assertFalse(task.due(FakeBot({"daily_alliance_donation_tried": recent}), settings))
        self.assertTrue(task.due(FakeBot({"daily_alliance_donation_tried": old}), settings))
        self.assertTrue(task.due(FakeBot(), settings))                      # chưa làm lần nào
        self.assertFalse(task.due(FakeBot(), {"Alliance Donation": 0}))     # ô giờ = 0: không làm

    def hourly_task(self, attempt):
        job = catalog.hourly_job(alliance_donation.TASK, attempt, alliance_donation.constants)
        return build_task({"key": "daily_alliance_donation", "priority": 394, "run": job}, "Daily Activities")

    def test_hourly_done_saves_the_time_and_done(self):
        bot = FakeBot()
        task = self.hourly_task(mock.Mock(return_value=TaskResult(done=True)))
        task.run(bot, {"Alliance Donation": 4})
        self.assertIn("daily_alliance_donation_tried", bot.done)   # giờ đã làm
        self.assertIn("daily_alliance_donation", bot.done)               # xong hôm nay
        self.assertTrue(task.done(bot, {"Alliance Donation": 4}))

    def test_hourly_not_done_saves_only_the_time(self):
        bot = FakeBot()
        task = self.hourly_task(mock.Mock(return_value=NOT_DONE))
        task.run(bot, {"Alliance Donation": 4})
        self.assertIn("daily_alliance_donation_tried", bot.done)
        self.assertNotIn("daily_alliance_donation", bot.done)
        self.assertFalse(task.done(bot, {"Alliance Donation": 4}))

    def test_hourly_interrupted_does_not_save_the_time(self):
        """Bị ngắt giữa chừng (hết 120 giây, có boss): chưa lưu giờ đã làm, lượt sau làm tiếp."""
        bot = FakeBot()
        task = self.hourly_task(mock.Mock(side_effect=KeyboardInterrupt))
        with self.assertRaises(KeyboardInterrupt):
            task.run(bot, {"Alliance Donation": 4})
        self.assertNotIn("daily_alliance_donation_tried", bot.done)

    def test_rewards_not_marked_until_all_done(self):
        """Còn việc đã tích chưa xong: nhận thưởng nhưng chưa lưu "đã nhận"."""
        bot = FakeBot()
        with mock.patch.object(catalog, "collect_activity_rewards") as collect:
            DEFS["daily_rewards"].run(bot, {"Offering": True})
        collect.assert_called_once()
        self.assertNotIn(catalog.REWARDS, bot.done)
        self.assertFalse(DEFS["daily_rewards"].done(bot, {"Offering": True}))

    def test_rewards_marked_when_all_done(self):
        bot = FakeBot({"daily_offering": "x"})
        with mock.patch.object(catalog, "collect_activity_rewards"):
            DEFS["daily_rewards"].run(bot, {"Offering": True})
        self.assertIn(catalog.REWARDS, bot.done)
        self.assertTrue(DEFS["daily_rewards"].done(bot, {"Offering": True}))

    def test_gift_claims_is_not_chained_after_daily_activities(self):
        """Gift Claims chờ điểm chạy riêng, không còn là đuôi của Daily."""
        self.assertNotIn("daily_gift_claims", DEFS)


if __name__ == "__main__":
    unittest.main()
