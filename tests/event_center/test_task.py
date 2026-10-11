"""
Nhiệm vụ của Event Center do worker gọi thẳng (bot/worker/policies.py): Crazy Eggs (ô giờ ở mục General của
tab Daily Activities, đập lại mỗi N giờ tới khi đủ 4 quả vỡ) và event 3 ngày.
"""
import importlib
import unittest
from datetime import datetime
from unittest import mock

from bot.activities.event_center.crazy_eggs.constants import DONE_KEY, INTERVAL_KEY, TRIED_KEY
from bot.activities.event_center.three_day.constants import DONE_KEY as THREE_DAY_DONE_KEY
from bot.activities.result import TaskResult
from bot.worker.registry import REGISTRY

tasks = importlib.import_module("bot.worker.policies")
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


class CrazyEggsTaskTests(unittest.TestCase):
    def run_eggs(self, bot, hours, finish=False):
        """Chạy nhiệm vụ crazy_eggs; `finish` = lần đập này vỡ đủ 4 quả (run trả done=True)."""
        def fake_run(b, settings):
            return TaskResult(done=finish)
        with mock.patch.object(tasks.crazy_eggs, "run", side_effect=fake_run) as run:
            tasks.run_crazy_eggs(bot, {"General": {INTERVAL_KEY: hours}})
        return run

    def test_hours_setting(self):
        self.assertEqual(tasks.crazy_eggs_hours({INTERVAL_KEY: 2}), 2)
        self.assertEqual(tasks.crazy_eggs_hours({INTERVAL_KEY: "3"}), 3)
        self.assertEqual(tasks.crazy_eggs_hours({}), 0)
        self.assertEqual(tasks.crazy_eggs_hours(None), 0)
        self.assertEqual(tasks.crazy_eggs_hours({INTERVAL_KEY: "x"}), 0)

    def test_enabled_only_when_hours_set(self):
        enabled = DEFS["crazy_eggs"].enabled
        self.assertTrue(enabled({"General": {INTERVAL_KEY: 2}}))
        self.assertFalse(enabled({"General": {INTERVAL_KEY: 0}}))
        self.assertFalse(enabled({}))

    def test_run_is_own_function(self):
        self.assertIs(DEFS["crazy_eggs"].run, tasks.run_crazy_eggs)
        self.assertTrue(DEFS["crazy_eggs"].repeat)

    def test_off_does_nothing(self):
        bot = FakeBot()
        run = self.run_eggs(bot, 0)
        run.assert_not_called()
        self.assertIsNone(bot.again_after)

    def test_not_all_broken_again_in_interval(self):
        """Đập xong mà chưa đủ 4 quả vỡ: hẹn lại sau đúng 2 giờ."""
        bot = FakeBot()
        run = self.run_eggs(bot, 2)
        run.assert_called_once()
        self.assertIn(TRIED_KEY, bot.done)
        self.assertEqual(bot.again_after, 2 * 3600)

    def test_all_eggs_broken_done_for_today(self):
        """Đập xong đủ 4 quả vỡ: không hẹn lại nữa."""
        bot = FakeBot()
        run = self.run_eggs(bot, 2, finish=True)
        run.assert_called_once()
        self.assertIsNone(bot.again_after)
        self.assertIn(DONE_KEY, bot.done)

    def test_done_today_skips(self):
        bot = FakeBot({DONE_KEY: "2026-10-11T09:00:00"})
        run = self.run_eggs(bot, 2)
        run.assert_not_called()
        self.assertIsNone(bot.again_after)

    def test_interrupted_not_marked_tried(self):
        """Bị ngắt giữa chừng (hết 120 giây): chưa đánh dấu đã thử, lượt sau đập tiếp."""
        bot = FakeBot()
        with mock.patch.object(tasks.crazy_eggs, "run", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                tasks.run_crazy_eggs(bot, {"General": {INTERVAL_KEY: 2}})
        self.assertNotIn(TRIED_KEY, bot.done)


class ThreeDayTaskTests(unittest.TestCase):
    def test_three_day_in_event_group_enabled_by_group(self):
        enabled = DEFS["three_day_event"].enabled
        self.assertEqual(DEFS["three_day_event"].group, "Event")
        self.assertTrue(enabled({"three_day_alliance": {"value": 60}}))
        self.assertFalse(enabled({}))   # tab Event thiếu group 3-Day Event
        self.assertFalse(enabled({"three_day_alliance": {"value": 60}, "three_day_active": {"enabled": False}}))

    def test_three_day_run_is_own_function(self):
        bot = FakeBot()
        with mock.patch.object(tasks.three_day, "run", return_value=TaskResult(done=True)) as run:
            DEFS["three_day_event"].run(bot, {"x": 1})
        run.assert_called_once_with(bot, {"x": 1})
        self.assertIn(THREE_DAY_DONE_KEY, bot.done)

    def test_three_day_not_done_is_not_marked(self):
        bot = FakeBot()
        with mock.patch.object(tasks.three_day, "run", return_value=TaskResult()):
            DEFS["three_day_event"].run(bot, {"x": 1})
        self.assertNotIn(THREE_DAY_DONE_KEY, bot.done)

    def test_three_day_done_today_skips(self):
        bot = FakeBot({THREE_DAY_DONE_KEY: "2026-10-06T09:00:00"})
        with mock.patch.object(tasks.three_day, "run") as run:
            DEFS["three_day_event"].run(bot, {"x": 1})
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
