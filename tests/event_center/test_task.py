"""
Nhiệm vụ của Event Center trong bảng nhiệm vụ của worker (bot/worker/priority.py): Crazy Eggs (ô giờ ở mục General của tab Daily
Activities, đập lại mỗi N giờ tới khi đủ 4 quả vỡ) và event 3 ngày. Luật của từng việc nằm cuối run.py của việc
(crazy_eggs/run.py, three_day/run.py); nhiệm vụ tự lưu kết quả vào DB, worker chỉ kiểm tra "xong chưa" và "tới giờ chưa".
"""
import importlib
import unittest
from datetime import datetime, timedelta
from unittest import mock

from bot.activities.event_center.crazy_eggs.constants import DONE_KEY, INTERVAL_KEY, TRIED_KEY
from bot.activities.event_center.three_day.constants import DONE_KEY as THREE_DAY_DONE_KEY
from bot.activities.result import TaskResult
from bot.worker.tasks import REGISTRY

eggs_run = importlib.import_module("bot.activities.event_center.crazy_eggs.run")
three_day_run = importlib.import_module("bot.activities.event_center.three_day.run")
DEFS = {d.key: d for d in REGISTRY}


class FakeBot:
    def __init__(self, done=None):
        self.done = dict(done or {})
        self.logs = []

    def is_daily_done(self, key):
        return key in self.done

    def mark_daily_done(self, key):
        self.done[key] = datetime.now().isoformat(timespec="seconds")

    def done_at(self, key):
        return self.done.get(key)

    def check(self):
        pass

    def log(self, message):
        self.logs.append(message)

    record = log


class CrazyEggsTaskTests(unittest.TestCase):
    def run_eggs(self, bot, hours, finish=False):
        """Chạy nhiệm vụ crazy_eggs (worker chỉ gọi khi tới giờ); `finish` = lần đập này vỡ đủ 4 quả (run trả done=True)."""
        with mock.patch.object(eggs_run, "run", return_value=TaskResult(done=finish)) as run:
            DEFS["crazy_eggs"].run(bot, {"General": {INTERVAL_KEY: hours}})
        return run

    def test_hours_setting(self):
        self.assertEqual(eggs_run.crazy_eggs_hours({"General": {INTERVAL_KEY: 2}}), 2)
        self.assertEqual(eggs_run.crazy_eggs_hours({"General": {INTERVAL_KEY: "3"}}), 3)
        self.assertEqual(eggs_run.crazy_eggs_hours({}), 0)
        self.assertEqual(eggs_run.crazy_eggs_hours({"General": None}), 0)
        self.assertEqual(eggs_run.crazy_eggs_hours({"General": {INTERVAL_KEY: "x"}}), 0)

    def test_enabled_only_when_hours_set(self):
        enabled = DEFS["crazy_eggs"].enabled
        self.assertTrue(enabled({"General": {INTERVAL_KEY: 2}}))
        self.assertFalse(enabled({"General": {INTERVAL_KEY: 0}}))
        self.assertFalse(enabled({}))

    def test_due_only_after_the_interval(self):
        """Tới giờ đập: chưa đập lần nào, hoặc đã qua N giờ kể từ lần trước (giờ lưu trong DB); ô giờ = 0 thì không bao giờ."""
        settings = {"General": {INTERVAL_KEY: 2}}
        due = DEFS["crazy_eggs"].due
        recent = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        old = (datetime.now() - timedelta(hours=3)).isoformat(timespec="seconds")
        self.assertTrue(due(FakeBot(), settings))
        self.assertFalse(due(FakeBot({TRIED_KEY: recent}), settings))
        self.assertTrue(due(FakeBot({TRIED_KEY: old}), settings))
        self.assertFalse(due(FakeBot(), {"General": {INTERVAL_KEY: 0}}))

    def test_not_all_broken_saves_the_time_not_done(self):
        """Đập xong mà chưa đủ 4 quả vỡ: nhiệm vụ tự lưu giờ vừa đập, chưa lưu xong (chờ tới giờ đập kế tiếp)."""
        bot = FakeBot()
        run = self.run_eggs(bot, 2)
        run.assert_called_once()
        self.assertIn(TRIED_KEY, bot.done)
        self.assertNotIn(DONE_KEY, bot.done)
        self.assertFalse(DEFS["crazy_eggs"].done(bot, {}))

    def test_all_eggs_broken_done_for_today(self):
        """Đập xong đủ 4 quả vỡ: nhiệm vụ tự lưu xong hôm nay."""
        bot = FakeBot()
        run = self.run_eggs(bot, 2, finish=True)
        run.assert_called_once()
        self.assertIn(DONE_KEY, bot.done)
        self.assertTrue(DEFS["crazy_eggs"].done(bot, {}))

    def test_interrupted_not_marked_tried(self):
        """Bị ngắt giữa chừng (hết 120 giây): chưa lưu giờ đã đập, lượt sau đập tiếp."""
        bot = FakeBot()
        with mock.patch.object(eggs_run, "run", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                DEFS["crazy_eggs"].run(bot, {"General": {INTERVAL_KEY: 2}})
        self.assertNotIn(TRIED_KEY, bot.done)

    def test_error_is_saved_to_the_db(self):
        """Lỗi thật: lưu `crazy_eggs_error` vào DB (và một dòng History) rồi báo lỗi lên."""
        bot = FakeBot()
        with mock.patch.object(eggs_run, "run", side_effect=ValueError("hỏng")):
            with self.assertRaises(ValueError):
                DEFS["crazy_eggs"].run(bot, {"General": {INTERVAL_KEY: 2}})
        self.assertIn("crazy_eggs_error", bot.done)
        self.assertNotIn(TRIED_KEY, bot.done)
        self.assertTrue(any("crazy_eggs" in line and "ValueError" in line for line in bot.logs))


class ThreeDayTaskTests(unittest.TestCase):
    def test_three_day_in_event_group_enabled_by_group(self):
        enabled = DEFS["three_day_event"].enabled
        self.assertEqual(DEFS["three_day_event"].group, "Event")
        self.assertTrue(enabled({"three_day_alliance": {"value": 60}}))
        self.assertFalse(enabled({}))   # tab Event thiếu group 3-Day Event
        self.assertFalse(enabled({"three_day_alliance": {"value": 60}, "three_day_active": {"enabled": False}}))

    def test_done_saves_the_done_key(self):
        bot = FakeBot()
        with mock.patch.object(three_day_run, "run", return_value=TaskResult(done=True)) as run:
            DEFS["three_day_event"].run(bot, {"x": 1})
        run.assert_called_once_with(bot, {"x": 1})
        self.assertIn(THREE_DAY_DONE_KEY, bot.done)
        self.assertTrue(DEFS["three_day_event"].done(bot, {}))

    def test_not_done_is_not_marked(self):
        bot = FakeBot()
        with mock.patch.object(three_day_run, "run", return_value=TaskResult()):
            DEFS["three_day_event"].run(bot, {"x": 1})
        self.assertNotIn(THREE_DAY_DONE_KEY, bot.done)
        self.assertFalse(DEFS["three_day_event"].done(bot, {}))

    def test_done_today_is_read_from_the_db(self):
        bot = FakeBot({THREE_DAY_DONE_KEY: "2026-10-06T09:00:00"})
        self.assertTrue(DEFS["three_day_event"].done(bot, {}))


if __name__ == "__main__":
    unittest.main()
