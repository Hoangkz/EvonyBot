"""
Hàm run riêng của các nhiệm vụ Event do worker gọi thẳng (luật xong / đạt mục tiêu / khoá và
nhận thưởng nằm cuối bot/activities/event/run.py; bảng nhiệm vụ: bot/worker/priority.py).
"""
import importlib
import unittest
from unittest import mock

from bot.activities.event.common import mark_done, mark_locked, mark_target_reached
from bot.worker.tasks import REGISTRY

event = importlib.import_module("bot.activities.event.run")
job = importlib.import_module("bot.activities.event.run")
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
    """Nhiệm vụ Event tự lưu kết quả vào DB (event/run.py: event_job); worker chỉ kiểm tra `done` rồi mới gọi `run`."""

    @staticmethod
    def run_patrol(bot, settings, fake):
        """Chạy event_job của King's Path Patrol với hàm làm việc giả `fake(bot, cấu hình riêng, state)`."""
        with (mock.patch.dict(job._KEY_OF, {fake: "kings_path_patrol"}),
              mock.patch.object(job, "to_city")):
            job.event_job("kings_path", fake)["run"](bot, settings)

    def test_run_event_task_runs_only_that_task(self):
        """Job của nhiệm vụ Event chạy đúng 1 nhiệm vụ, với cấu hình riêng của nó."""
        bot = FakeBot()
        calls = []
        self.run_patrol(bot, {"kings_path_patrol": ON}, lambda b, task, state: calls.append(task))
        self.assertEqual(calls, [ON])

    def test_complete_done_today_or_locked_count_as_done(self):
        """Xong hẳn / xong hôm nay / Day khoá: worker thấy `done` đúng nên bỏ qua, không gọi run."""
        done = DEFS["kings_path_patrol"].done
        settings = {"kings_path_patrol": ON}
        for marks in (["kings_path_patrol_complete"], ["kings_path_patrol"], ["kings_path_patrol_locked"]):
            self.assertTrue(done(FakeBot(done=marks), settings), marks)
        self.assertFalse(done(FakeBot(), settings))

    def test_records_done_when_task_finishes(self):
        bot = FakeBot()
        self.run_patrol(bot, {"kings_path_patrol": ON}, lambda b, task, state: mark_done(b, "kings_path_patrol"))
        self.assertIn("Event: xong kings_path_patrol", bot.logs)
        self.assertIn("kings_path_patrol", bot.done)

    def test_reused_event_navigator_can_report_the_own_worker_group(self):
        bot = FakeBot()
        fake = lambda b, task, state: mark_done(b, "revelry_carnival")
        with (mock.patch.dict(job._KEY_OF, {fake: "revelry_carnival"}),
              mock.patch.object(job, "to_city")):
            job.event_job("revelry_carnival", fake,
                          completion_label="Gift Claims")["run"](bot, {})

        self.assertIn("Gift Claims: xong revelry_carnival", bot.logs)
        self.assertNotIn("Event: xong revelry_carnival", bot.logs)

    def test_records_target_reached_and_locked(self):
        settings = {"kings_path_patrol": {"value": 30, "day": 2}}
        bot = FakeBot()
        self.run_patrol(bot, settings, lambda b, task, state: mark_target_reached(b, "kings_path_patrol"))
        self.assertEqual(set(bot.done), {"kings_path_patrol", "kings_path_patrol_complete_30",
                                         "kings_path_patrol_reached_30"})
        bot = FakeBot()
        self.run_patrol(bot, settings, lambda b, task, state: mark_locked(b, "kings_path_patrol"))
        self.assertEqual(set(bot.done), {"kings_path_patrol_locked"})

    def test_raised_target_is_not_done_lowering_it_is_done_again(self):
        """Xong vì đạt mục tiêu 30; tăng lên 60 ở tab -> chưa xong; giảm về 20 hoặc 30 -> xong lại (đọc DB mỗi lần)."""
        bot = FakeBot()
        self.run_patrol(bot, {"kings_path_patrol": {"value": 30}},
                        lambda b, task, state: mark_target_reached(b, "kings_path_patrol"))
        done = DEFS["kings_path_patrol"].done
        self.assertTrue(done(bot, {"kings_path_patrol": {"value": 20}}))
        self.assertFalse(done(bot, {"kings_path_patrol": {"value": 60}}))
        self.assertTrue(done(bot, {"kings_path_patrol": {"value": 30}}))

    def test_error_is_saved_to_the_db(self):
        bot = FakeBot()

        def boom(b, task, state):
            raise ValueError("hỏng")

        with self.assertRaises(ValueError):
            self.run_patrol(bot, {"kings_path_patrol": ON}, boom)
        self.assertIn("kings_path_patrol_error", bot.done)

    def test_claim_runs_only_when_a_task_is_done_and_not_claimed_yet(self):
        with mock.patch.object(job, "claim_event") as claim:
            DEFS["gather_troops_claim"].run(FakeBot(), {})                                 # chưa nhiệm vụ nào xong
            claim.assert_not_called()
            bot = FakeBot(done=["gather_troops_ground_troop"])
            DEFS["gather_troops_claim"].run(bot, {})
            claim.assert_called_once()
            self.assertEqual(claim.call_args.args[1], "gather_troops")
            self.assertIn("gather_troops_claimed_1", bot.done)                             # nhận xong: tự lưu vào DB
            claim.reset_mock()
            DEFS["gather_troops_claim"].run(bot, {})                                       # đã nhận ứng với 1 nhiệm vụ xong
            claim.assert_not_called()
            self.assertTrue(DEFS["gather_troops_claim"].done(bot, {"gather_troops_ground_troop": ON}))


if __name__ == "__main__":
    unittest.main()
