"""Vòng kiểm tra 3 lần của hoạt động quà (bot/activities/gift_claims/scan.py)."""
import unittest
from importlib import import_module
from unittest import mock
from types import SimpleNamespace

from bot.activities import gift_claims
from bot.activities.gift_claims import common, scan
from bot.activities.gift_claims.common import mark_task_done
from bot.activities.gift_claims.event_center import zone as event_center_zone

event_center_run = import_module(
    "bot.activities.gift_claims.event_center.run")


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
    def test_job_runs_when_checked_and_is_done_by_zone_key(self):
        bot = FakeBot()
        zone = SimpleNamespace(KEY="gift_zone", run=mock.Mock(return_value=True))
        job = gift_claims.job(zone)

        self.assertTrue(job["enabled"]({}))
        self.assertTrue(job["enabled"]({"General": {"gift_claims": True}}))
        self.assertFalse(job["enabled"]({"General": {"gift_claims": False}}))
        self.assertFalse(job["done"](bot, {}))
        self.assertTrue(job["run"](bot, {}))
        zone.run.assert_called_once_with(bot)
        self.assertFalse(job["done"](bot, {}))
        bot.mark_daily_done("gift_zone")
        self.assertTrue(job["done"](bot, {}))

    def test_zone_pending_waits_for_next_120_second_window(self):
        bot = FakeBot()
        zone = SimpleNamespace(KEY="gift_zone", run=mock.Mock(return_value=False))
        job = gift_claims.job(zone)

        with mock.patch.object(gift_claims.time, "monotonic",
                               side_effect=(100.0, 219.9, 220.0)):
            self.assertFalse(job["run"](bot, {}))
            self.assertTrue(job["done"](bot, {}))
            self.assertFalse(job["done"](bot, {}))

        zone.run.assert_called_once_with(bot)
        self.assertTrue(any("120s kế tiếp" in line for line in bot.log))

    def test_job_skipped_for_run_counts_as_done_until_next_start(self):
        bot = FakeBot()
        job = gift_claims.job(SimpleNamespace(KEY="gift_zone", run=mock.Mock()))
        common.skip_for_run(bot, "gift_zone")
        self.assertTrue(job["done"](bot, {}))          # worker loại khỏi danh sách trong lần Start này
        self.assertFalse(job["done"](FakeBot(), {}))   # Start lại: context mới, làm lại
        self.assertNotIn("gift_zone", bot.done)        # không ghi DB

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

    def test_event_center_persists_completed_category_before_later_timeout(self):
        bot = FakeBot()
        key = "gift_dragon_battle"

        def interrupted_after_limited(_bot, _handled):
            setattr(bot, event_center_zone.SCANNED_CATEGORIES_ATTR,
                    {"limited"})
            setattr(bot, event_center_zone.SEEN_POLICIES_ATTR, set())
            raise RuntimeError("simulated Activities timeout")

        with (mock.patch.object(event_center_zone, "open_event_center",
                                return_value=object()),
              mock.patch.object(event_center_zone, "identify",
                                return_value=None),
              mock.patch.object(event_center_zone, "run_opened",
                                side_effect=interrupted_after_limited),
              self.assertRaises(RuntimeError)):
            event_center_zone._sweep(bot, [key])

        self.assertEqual(1, event_center_zone._limited_misses(bot, key))
        self.assertIn(f"{key}_miss_done_1", bot.done)

    def test_event_center_resumes_miss_counter_across_three_windows(self):
        bot = FakeBot()
        key = "gift_dragon_battle"

        def scanned_limited(_bot, _handled):
            setattr(bot, event_center_zone.SCANNED_CATEGORIES_ATTR,
                    {"limited"})
            setattr(bot, event_center_zone.SEEN_POLICIES_ATTR, set())
            return False

        with (mock.patch.object(event_center_zone, "open_event_center",
                                return_value=object()),
              mock.patch.object(event_center_zone, "identify",
                                return_value=None),
              mock.patch.object(event_center_zone, "run_opened",
                                side_effect=scanned_limited)):
            event_center_zone._sweep(bot, [key])
            self.assertEqual(1, event_center_zone._limited_misses(bot, key))
            event_center_zone._sweep(bot, [key])
            self.assertEqual(2, event_center_zone._limited_misses(bot, key))
            event_center_zone._sweep(bot, [key])

        self.assertIn(key, bot.done)
        self.assertTrue(all(f"{key}_miss_done_{index}" in bot.done
                            for index in range(1, 4)))

    def test_event_center_activities_never_accrues_limited_miss_done(self):
        bot = FakeBot()
        key = "gift_dwarfs_lucky_apple"
        setattr(bot, event_center_zone.SCANNED_CATEGORIES_ATTR, {"activities"})
        setattr(bot, event_center_zone.SEEN_POLICIES_ATTR, set())

        event_center_zone._checkpoint_categories(bot, [key])

        self.assertEqual(0, event_center_zone._limited_misses(bot, key))
        self.assertNotIn(key, bot.done)

    def test_event_center_resume_category_rotates_durably(self):
        bot = FakeBot()
        self.assertEqual("limited",
                         event_center_run._ordered_categories(bot)[0][0])

        event_center_run._set_resume_category(bot, "activities")
        self.assertEqual("activities",
                         event_center_run._ordered_categories(bot)[0][0])
        self.assertIn(
            event_center_run.CATEGORY_RESUME_KEYS["activities"], bot.done)

        event_center_run._set_resume_category(bot, "limited")
        self.assertEqual("limited",
                         event_center_run._ordered_categories(bot)[0][0])
        self.assertNotIn(
            event_center_run.CATEGORY_RESUME_KEYS["activities"], bot.done)

    def test_limited_completion_checkpoints_activities_before_timeout(self):
        bot = FakeBot()
        bot.screenshot = lambda: object()

        with (mock.patch.object(event_center_run, "find",
                                return_value=(198, 25)),
              mock.patch.object(event_center_run, "_select_category",
                                return_value=True),
              mock.patch.object(event_center_run, "_category_db_done",
                                return_value=False),
              mock.patch.object(event_center_run, "_scan_category",
                                side_effect=(True,
                                             RuntimeError("Activities timeout"))),
              self.assertRaises(RuntimeError)):
            event_center_run.run_opened(bot, set())

        self.assertEqual("activities",
                         event_center_run._ordered_categories(bot)[0][0])


if __name__ == "__main__":
    unittest.main()
