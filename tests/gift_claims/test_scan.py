"""Vòng kiểm tra 3 lần của hoạt động quà (bot/activities/gift_claims/scan.py)."""
import unittest

from bot.activities.gift_claims import scan
from bot.activities.gift_claims.common import mark_task_done


class FakeBot:
    def __init__(self):
        self.done = {}
        self.log = []

    def check(self): pass
    def record(self, message): self.log.append(message)
    def is_daily_done(self, key): return key in self.done
    def mark_daily_done(self, key): self.done[key] = "now"
    def done_at(self, key): return self.done.get(key)
    def forget_daily(self, key): self.done.pop(key, None)


TASKS = [("a", "A"), ("b", "B")]


class ScanTest(unittest.TestCase):
    def test_three_misses_mark_done(self):
        bot, calls = FakeBot(), []

        def sweep(bot, pending):
            calls.append(list(pending))
            return set(pending)

        self.assertTrue(scan.run_zone(bot, "zone", TASKS, sweep))
        self.assertEqual(3, len(calls))
        self.assertTrue({"a", "b", "zone"} <= set(bot.done))

    def test_found_resets_counter_and_marks_done(self):
        bot = FakeBot()
        bot.done["a_miss_1"] = bot.done["a_miss_2"] = "now"

        def sweep(bot, pending):
            mark_task_done(bot, "a")
            return set(pending)

        scan.run_zone(bot, "zone", [("a", "A")], sweep)
        self.assertIn("a", bot.done)
        self.assertEqual(0, scan.misses(bot, "a"))

    def test_zone_not_opened_is_not_a_miss(self):
        bot = FakeBot()
        self.assertFalse(scan.run_zone(bot, "zone", TASKS, lambda bot, pending: set()))
        self.assertEqual(0, scan.misses(bot, "a"))
        self.assertNotIn("zone", bot.done)

    def test_done_task_is_skipped(self):
        bot, seen = FakeBot(), []
        bot.done["a"] = "now"

        def sweep(bot, pending):
            seen.append(list(pending))
            mark_task_done(bot, "b")
            return set(pending)

        self.assertTrue(scan.run_zone(bot, "zone", TASKS, sweep))
        self.assertEqual([["b"]], seen)


if __name__ == "__main__":
    unittest.main()
