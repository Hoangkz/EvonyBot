"""Vòng kiểm tra 3 lần của hoạt động quà (bot/activities/gift_claims/scan.py)."""
import unittest
from unittest import mock

from bot.activities.gift_claims import scan
from bot.activities.gift_claims.common import mark_task_done
from bot.activities.gift_claims.event_center import zone as event_center_zone


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
        self.assertTrue(any("kiểm tra A không xuất hiện (lượt 1/3)" in line
                            for line in bot.log))
        self.assertTrue(any("kiểm tra A không xuất hiện (lượt 2/3)" in line
                            for line in bot.log))
        self.assertTrue(any("kiểm tra A không xuất hiện (lượt 3/3)" in line
                            for line in bot.log))

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
        self.assertFalse(any("không xuất hiện" in line for line in bot.log))

    def test_custom_sweep_limit_allows_two_three_pass_categories(self):
        bot, calls = FakeBot(), []

        def sweep(_bot, pending):
            calls.append(list(pending))
            return {"a"} if len(calls) <= 3 else {"b"}

        self.assertTrue(scan.run_zone(
            bot, "zone", TASKS, sweep, max_sweeps=scan.MAX_MISSES * 2))
        self.assertEqual(6, len(calls))

    def test_done_task_is_skipped(self):
        bot, seen = FakeBot(), []
        bot.done["a"] = "now"

        def sweep(bot, pending):
            seen.append(list(pending))
            mark_task_done(bot, "b")
            return set(pending)

        self.assertTrue(scan.run_zone(bot, "zone", TASKS, sweep))
        self.assertEqual([["b"]], seen)

    def test_seen_but_unfinished_event_is_not_counted_as_missing(self):
        bot = FakeBot()
        key = "gift_dwarfs_treasure"
        with (mock.patch.object(event_center_zone, "open_event_center",
                                return_value=object()),
              mock.patch.object(event_center_zone, "identify",
                                return_value=None),
              mock.patch.object(event_center_zone, "run_opened",
                                return_value=False),
              mock.patch.object(event_center_zone, "return_home")):
            inspected = event_center_zone._sweep(bot, [key])

        self.assertNotIn(key, inspected)
        self.assertNotIn(key, bot.done)

    def test_event_center_rows_survive_an_interrupted_sweep(self):
        bot = FakeBot()
        marker = b"limited-row"

        def interrupted(_bot, handled):
            handled.add(marker)
            raise RuntimeError("simulated boss yield")

        with (mock.patch.object(event_center_zone, "open_event_center",
                                return_value=object()),
              mock.patch.object(event_center_zone, "identify",
                                return_value=None),
              mock.patch.object(event_center_zone, "run_opened",
                                side_effect=interrupted),
              self.assertRaises(RuntimeError)):
            event_center_zone._sweep(bot, ["gift_dwarfs_treasure"])

        self.assertEqual({marker}, getattr(bot, event_center_zone.HANDLED_ATTR))


if __name__ == "__main__":
    unittest.main()
