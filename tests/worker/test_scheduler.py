"""
Bộ chọn nhiệm vụ (bot/worker/scheduler.py, tasks.py) và vòng lặp nhiệm vụ của BotWorker
(bot/worker/TODO.md mục 1: Bubble > Join Boss > nhiệm vụ; mỗi vòng 1 lượt Join Boss + 1 nhiệm vụ;
không còn nhiệm vụ tới lượt thì thread vẫn sống).
"""
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from bot.context import BotContext
from bot.context.errors import StopRequested
from bot.worker import bot_worker
from bot.worker.bot_worker import BOSS_IDLE, JOIN_BOSS, BotWorker
from bot.worker.scheduler import Scheduler
from bot.worker.server_clock import ServerClock
from bot.worker.tasks import DEFAULT_PRIORITY, Task, build_tasks, group_priority, load_priorities

DAY1, DAY2 = datetime(2026, 10, 3, 9), datetime(2026, 10, 4, 9)


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.reset = [DAY1]
        self.make = lambda tasks: Scheduler(tasks, lambda: self.reset[0])

    def run_one(self, scheduler):
        task = scheduler.pick()
        scheduler.started(task)
        scheduler.finished(task)
        return task.key

    def test_higher_priority_first(self):
        s = self.make([Task("low", "low", 1), Task("high", "high", 9), Task("mid", "mid", 5)])
        self.assertEqual([self.run_one(s) for _ in range(3)], ["high", "mid", "low"])
        self.assertIsNone(s.pick())

    def test_same_priority_rotates(self):
        """Cùng ưu tiên: nhiệm vụ lâu chưa được bắt đầu nhất đi trước (nhiệm vụ bị ngắt xuống cuối)."""
        a, b, c = Task("a", "a", 1), Task("b", "b", 1), Task("c", "c", 1)
        s = self.make([a, b, c])
        self.assertEqual(s.pick(), a)
        s.started(a)                    # a bị ngắt, chưa xong
        self.assertEqual(s.pick(), b)
        s.started(b)
        self.assertEqual(s.pick(), c)
        s.started(c)
        self.assertEqual(s.pick(), a)   # quay vòng lại

    def test_done_task_due_again_after_reset(self):
        s = self.make([Task("a", "a", 1)])
        self.assertEqual(self.run_one(s), "a")
        self.assertIsNone(s.pick())
        self.reset[0] = DAY2           # qua mốc reset server
        self.assertEqual(self.run_one(s), "a")

    def test_done_uses_reset_at_start(self):
        """Bắt đầu trước mốc reset, xong sau mốc: vẫn làm lại trong ngày mới (tính theo lúc bắt đầu)."""
        s = self.make([Task("a", "a", 1)])
        task = s.pick()
        s.started(task)
        self.reset[0] = DAY2
        s.finished(task)
        self.assertEqual(s.pick(), task)


class TasksTests(unittest.TestCase):
    def test_priorities_from_file(self):
        path = Path(tempfile.mkdtemp()) / "p.json"
        path.write_text(json.dumps({
            "_doc": "x",
            "Event": [{"key": "a", "priority": 5}, {"key": "b", "priority": 7, "note": "n"}],
            "Open Gift Box": [{"key": "open_gift_box", "priority": 3}],
        }), encoding="utf-8")
        priorities = load_priorities(path)
        self.assertEqual(priorities, {"Event": {"a": 5, "b": 7}, "Open Gift Box": {"open_gift_box": 3}})
        self.assertEqual(group_priority(priorities, "Event"), 7)
        self.assertEqual(group_priority(priorities, "Unknown"), DEFAULT_PRIORITY)
        tasks = build_tasks([JOIN_BOSS, "Open Gift Box", "Event"], {JOIN_BOSS}, priorities)
        self.assertEqual([(t.key, t.priority) for t in tasks], [("Open Gift Box", 3), ("Event", 7)])

    def test_missing_file_uses_default(self):
        self.assertEqual(load_priorities(Path(tempfile.mkdtemp()) / "none.json"), {})

    def test_real_priority_file_loads(self):
        self.assertIn("Crazy Eggs", load_priorities())


class WorkerLoopTests(unittest.TestCase):
    def make_worker(self, activities, priorities):
        worker = BotWorker("b", activities, {"Initialization": {"server": "1"}},
                           server_clock=ServerClock("known"))
        worker.ctx = BotContext(SimpleNamespace(serial="b"), worker._stop, None, worker.log)
        patcher = mock.patch.object(bot_worker, "load_priorities", return_value=priorities)
        patcher.start()
        self.addCleanup(patcher.stop)
        return worker

    def run_until_stop(self, worker, run_activity):
        """Chạy vòng lặp tới khi Stop: thoát ở điều kiện while hoặc qua StopRequested đều đúng."""
        worker._run_activity = run_activity
        try:
            worker._run_tasks()
        except StopRequested:
            pass
        self.assertTrue(worker._stop.is_set(), 'vòng lặp chỉ được dừng khi Stop')

    def test_one_task_per_boss_round_by_priority(self):
        """Mỗi vòng: 1 lượt Join Boss rồi đúng 1 nhiệm vụ (ưu tiên cao trước), xong là quay lại boss."""
        worker = self.make_worker([JOIN_BOSS, "low", "high"], {"low": {"x": 1}, "high": {"y": 9}})
        calls = []

        def run_activity(activity, settings):
            calls.append(activity)
            if activity == JOIN_BOSS and calls.count(JOIN_BOSS) == 3:
                worker._stop.set()
            return BOSS_IDLE if activity == JOIN_BOSS else None

        self.run_until_stop(worker, run_activity)
        self.assertEqual(calls, [JOIN_BOSS, "high", JOIN_BOSS, "low", JOIN_BOSS])

    def test_without_boss_thread_stays_alive(self):
        """Không chọn Join Boss: làm hết nhiệm vụ rồi vẫn chờ (không return) cho tới khi Stop."""
        worker = self.make_worker(["a", "b"], {})
        calls = []
        sleeps = []

        def run_activity(activity, settings):
            calls.append(activity)

        def sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) == 3:
                worker._stop.set()
            worker.ctx.check()

        worker.ctx.sleep = sleep
        self.run_until_stop(worker, run_activity)
        self.assertEqual(calls, ["a", "b"])
        self.assertEqual(sleeps, [bot_worker.IDLE_WAIT] * 3)
        self.assertIsNone(worker.ctx._deadline)   # gỡ deadline sau mỗi nhiệm vụ

    def test_no_time_limit_without_boss(self):
        """Không chọn Join Boss: không có giới hạn 120 giây, không bật ngắt bởi boss."""
        worker = self.make_worker(["a", "b"], {})
        calls = []

        def run_activity(activity, settings):
            calls.append((activity, worker.ctx._deadline, worker.ctx._boss_interrupt_enabled))
            if activity == "b":
                worker._stop.set()

        self.run_until_stop(worker, run_activity)
        self.assertEqual(calls, [("a", None, False), ("b", None, False)])

    def test_task_limited_to_120s_with_boss(self):
        """Có Join Boss: mỗi nhiệm vụ tối đa 120 giây; hết giờ thì làm lại đầu tiên ở vòng sau."""
        worker = self.make_worker([JOIN_BOSS, "a", "b"], {})
        calls = []

        def run_activity(activity, settings):
            calls.append(activity)
            if activity == JOIN_BOSS:
                return BOSS_IDLE
            self.assertIsNotNone(worker.ctx._deadline)
            self.assertTrue(worker.ctx._boss_interrupt_enabled)
            if calls.count("a") == 1:
                worker.ctx._deadline = 0   # giả lập đã hết 120 giây
                worker.ctx.check()
            if activity == "b":
                worker._stop.set()

        self.run_until_stop(worker, run_activity)
        self.assertEqual(calls, [JOIN_BOSS, "a", JOIN_BOSS, "a", JOIN_BOSS, "b"])

    def test_bubble_off_no_bubble_rule(self):
        """Không tích Bubble: không lo bubble trước nhiệm vụ, không hẹn ngắt vì bubble."""
        worker = self.make_worker(["a"], {})
        self.assertFalse(worker.bubble_enabled)

        def run_activity(activity, settings):
            self.assertIsNone(worker.ctx._bubble_due_at)
            worker._stop.set()

        with mock.patch.object(bot_worker, "keep_bubble") as keep:
            self.run_until_stop(worker, run_activity)
        keep.assert_not_called()

    def test_boss_stopped_still_runs_tasks(self):
        """Join Boss dừng hẳn (không phải IDLE): không gọi lại boss nữa, vẫn chạy các nhiệm vụ."""
        worker = self.make_worker([JOIN_BOSS, "a", "b"], {})
        calls = []

        def run_activity(activity, settings):
            calls.append(activity)
            if activity == "b":
                worker._stop.set()
            return None

        self.run_until_stop(worker, run_activity)
        self.assertEqual(calls, [JOIN_BOSS, "a", "b"])

    def test_only_boss_runs_boss_continuously(self):
        worker = self.make_worker([JOIN_BOSS], {})
        calls = []

        def run_activity(activity, settings):
            calls.append((activity, settings.get("exit_when_idle", False)))

        worker._run_activity = run_activity
        worker._run_tasks()
        self.assertEqual(calls, [(JOIN_BOSS, False)])


if __name__ == "__main__":
    unittest.main()
