"""
Hàm run riêng của các nhiệm vụ Event do worker gọi thẳng (luật chạy: bot/worker/event/policy.py; việc làm trong
game: bot/activities/event/run.py; bảng nhiệm vụ: bot/worker/registry.py).
"""
import importlib
import unittest
from unittest import mock

from bot.activities.event.common import mark_done, mark_locked, mark_target_reached
from bot.worker.registry import REGISTRY

event = importlib.import_module("bot.activities.event.run")
policy = importlib.import_module("bot.worker.event.policy")
DEFS = {d.key: d for d in REGISTRY}

ON = {"enabled": True, "day": 1}
OFF = {"enabled": False, "day": 1}


class FakeBot:
    def __init__(self, done=()):
        self.done = dict.fromkeys(done, "2026-10-02T08:00:00")
        self.logs = []

    def is_daily_done(self, key):
        return key in self.done

    def mark_daily_done(self, key):
        self.done[key] = "2026-10-02T08:00:00"

    def done_at(self, key):
        return self.done.get(key)

    def daily_keys(self):
        return list(self.done)

    def check(self):
        pass

    def log(self, message):
        self.logs.append(message)

    record = log


class EventRegistryTests(unittest.TestCase):
    def test_every_event_task_is_registered(self):
        keys = {key for *_, tasks in event.EVENTS for key, _ in tasks}
        self.assertLessEqual(keys, set(DEFS))
        self.assertTrue(all(DEFS[key].group == "Event" for key in keys))

    def test_enabled_follows_tab_settings(self):
        settings = {"gather_troops_ground_troop": ON, "gather_troops_mounted_troop": OFF}
        self.assertTrue(DEFS["gather_troops_ground_troop"].enabled(settings))
        self.assertFalse(DEFS["gather_troops_mounted_troop"].enabled(settings))
        self.assertFalse(DEFS["kings_path_patrol"].enabled(settings))   # không có trong cấu hình

    def test_inactive_group_not_enabled(self):
        settings = {"gather_troops_ground_troop": ON, "gather_troops_active": {"enabled": False}}
        self.assertFalse(DEFS["gather_troops_ground_troop"].enabled(settings))
        self.assertFalse(DEFS["gather_troops_claim"].enabled(settings))

    def test_claim_enabled_only_with_some_task_enabled(self):
        self.assertTrue(DEFS["kings_path_claim"].enabled({"kings_path_patrol": ON}))
        self.assertFalse(DEFS["kings_path_claim"].enabled({}))



class EventRunTests(unittest.TestCase):
    def test_run_event_task_runs_only_that_task(self):
        """Hàm run của nhiệm vụ Event chạy đúng 1 nhiệm vụ, với cấu hình riêng của nó."""
        bot = FakeBot()
        calls = []
        settings = {"kings_path_patrol": ON}
        policy.run_event_task(bot, settings, key="kings_path_patrol",
                              run_task=lambda b, task, state: calls.append(task))
        self.assertEqual(calls, [ON])

    def test_skips_complete_task(self):
        bot = FakeBot(done=["kings_path_patrol_complete"])
        calls = []
        policy.run_event_task(bot, {"kings_path_patrol": ON}, key="kings_path_patrol",
                              run_task=lambda *a: calls.append(1))
        self.assertEqual(calls, [])

    def test_skips_task_done_today_or_locked(self):
        for done in (["kings_path_patrol"], ["kings_path_patrol_locked"]):
            bot = FakeBot(done=done)
            calls = []
            policy.run_event_task(bot, {"kings_path_patrol": ON}, key="kings_path_patrol",
                                  run_task=lambda *a: calls.append(1))
            self.assertEqual(calls, [], done)

    def test_records_done_when_task_finishes(self):
        bot = FakeBot()

        def run_task(b, task, state):
            mark_done(b, "kings_path_patrol")

        policy.run_event_task(bot, {"kings_path_patrol": ON}, key="kings_path_patrol", run_task=run_task)
        self.assertIn("Event: xong kings_path_patrol", bot.logs)
        self.assertIn("kings_path_patrol", bot.done)

    def test_records_target_reached_and_locked(self):
        settings = {"kings_path_patrol": {"value": 30, "day": 2}}
        bot = FakeBot()
        policy.run_event_task(bot, settings, key="kings_path_patrol",
                              run_task=lambda b, task, state: mark_target_reached(b, "kings_path_patrol"))
        self.assertEqual(set(bot.done), {"kings_path_patrol", "kings_path_patrol_complete_30",
                                         "kings_path_patrol_reached_30"})
        bot = FakeBot()
        policy.run_event_task(bot, settings, key="kings_path_patrol",
                              run_task=lambda b, task, state: mark_locked(b, "kings_path_patrol"))
        self.assertEqual(set(bot.done), {"kings_path_patrol_locked"})

    def test_raised_target_runs_again(self):
        """Xong vì đạt mục tiêu 30; tăng lên 60 ở tab UI -> chưa xong, chạy lại; giảm về 20 -> vẫn xong."""
        bot = FakeBot()
        policy.run_event_task(bot, {"kings_path_patrol": {"value": 30}}, key="kings_path_patrol",
                              run_task=lambda b, task, state: mark_target_reached(b, "kings_path_patrol"))
        self.assertTrue(policy.is_done_today(bot, {"kings_path_patrol": {"value": 20}}, "kings_path_patrol"))
        self.assertFalse(policy.is_done_today(bot, {"kings_path_patrol": {"value": 60}}, "kings_path_patrol"))

    def test_claim_step(self):
        bot = FakeBot()
        with mock.patch.object(policy, "maybe_claim") as claim:
            DEFS["gather_troops_claim"].run(bot, {})
        claim.assert_called_once()
        args = claim.call_args.args
        self.assertEqual(args[1], "gather_troops")
        self.assertIn("gather_troops_ground_troop", args[4])


if __name__ == "__main__":
    unittest.main()
