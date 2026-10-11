"""
Bộ chọn nhiệm vụ (bot/worker/scheduler.py, tasks.py), bảng nhiệm vụ (bot/activities/registry.py) và vòng lặp nhiệm vụ
của BotWorker (bot/worker/TODO.md mục 1: Bubble > Join Boss > nhiệm vụ; mỗi vòng 1 lượt Join Boss + 1 nhiệm vụ;
không còn nhiệm vụ tới lượt thì thread vẫn sống). Worker gọi thẳng `run` riêng của từng nhiệm vụ.
"""
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

from bot.worker.registry import REGISTRY, TaskDef
from bot.context import BotContext
from bot.context.errors import StopRequested
from bot.worker import bot_worker
from bot.worker.bot_worker import BOSS_IDLE, JOIN_BOSS, BotWorker
from bot.worker.scheduler import Scheduler
from bot.worker.server_clock import ServerClock
from bot.worker.tasks import DEFAULT_PRIORITY, Task, build_tasks, load_must_finish, load_priorities

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

    def test_once_task_not_due_after_reset(self):
        """Nhiệm vụ once (Black Market): xong rồi thì qua mốc reset cũng không tới lượt lại."""
        s = self.make([Task("a", "a", 1, once=True), Task("b", "b", 1)])
        self.assertEqual([self.run_one(s) for _ in range(2)], ["a", "b"])
        self.reset[0] = DAY2
        self.assertEqual(s.pick().key, "b")   # b làm lại, a thì không
        self.run_one(s)
        self.assertIsNone(s.pick())

    def test_once_task_interrupted_still_due(self):
        """Nhiệm vụ once bị ngắt giữa chừng (chưa xong) vẫn tới lượt để làm lại."""
        s = self.make([Task("a", "a", 1, once=True)])
        task = s.pick()
        s.started(task)
        self.reset[0] = DAY2
        self.assertEqual(s.pick(), task)

    def test_repeat_keeps_priority_when_due_again(self):
        """Crazy Eggs (repeat): hẹn chạy lại vẫn giữ ưu tiên 999, làm trước nhiệm vụ khác dù nhiệm vụ đó cũng tới lượt."""
        s = self.make([Task("eggs", "Daily Activities", 999, repeat=True), Task("other", "other", 5)])
        eggs = s.pick()
        s.started(eggs)
        s.finished(eggs, again_after=1)
        s._again_at["eggs"] = datetime(2000, 1, 1)   # đã tới giờ hẹn; other vẫn chưa làm hôm nay
        self.assertEqual(s.pick().key, "eggs")

    def test_non_repeat_again_goes_last(self):
        """Hẹn chạy lại thường (Alliance Donation ...): ưu tiên thấp nhất, sau mọi nhiệm vụ khác."""
        s = self.make([Task("daily", "Daily Activities", 999), Task("other", "other", 5)])
        daily = s.pick()
        s.started(daily)
        s.finished(daily, again_after=1)
        s._again_at["daily"] = datetime(2000, 1, 1)
        self.assertEqual(s.pick().key, "other")


def _fake_registry(*specs):
    """[(key, group, enabled, once)] -> TaskDef giả."""
    return [TaskDef(key, group, (lambda s, e=enabled: e(s) if callable(e) else e), lambda bot, s: None, once=once)
            for key, group, enabled, once in specs]


class BuildTasksTests(unittest.TestCase):
    def test_only_selected_groups_and_enabled_tasks(self):
        """Chỉ nhiệm vụ có group được chọn và đã được tích; activity chỉ để chia loại."""
        registry = _fake_registry(("a", "G1", True, False), ("b", "G1", False, False), ("c", "G2", True, False))
        priorities = {"G1": {"a": 5, "b": 9}, "G2": {"c": 7}}
        tasks = build_tasks(["G1"], set(), priorities, settings={}, registry=registry)
        self.assertEqual([(t.key, t.group, t.priority) for t in tasks], [("a", "G1", 5)])

    def test_enabled_receives_group_settings(self):
        registry = _fake_registry(("a", "G1", lambda s: s.get("x"), False))
        tasks = build_tasks(["G1"], set(), {}, settings={"G1": {"x": True}}, registry=registry)
        self.assertEqual([t.key for t in tasks], ["a"])
        self.assertEqual(tasks[0].priority, DEFAULT_PRIORITY)
        self.assertEqual(build_tasks(["G1"], set(), {}, settings={"G1": {"x": False}}, registry=registry), [])

    def test_skip_group(self):
        registry = _fake_registry(("a", "G1", True, False))
        self.assertEqual(build_tasks(["G1"], {"G1"}, {}, registry=registry), [])

    def test_negative_priority_not_in_task_list(self):
        """Ưu tiên < 0 không được đưa vào danh sách nhiệm vụ; 0 trở lên thì có."""
        registry = _fake_registry(("zero", "G", True, False), ("neg", "G", True, False), ("pos", "G", True, False))
        tasks = build_tasks(["G"], set(), {"G": {"zero": 0, "neg": -1, "pos": 5}}, registry=registry)
        self.assertEqual([t.key for t in tasks], ["zero", "pos"])

    def test_flags_and_run_carried_to_task(self):
        registry = _fake_registry(("a", "G", True, True))
        tasks = build_tasks(["G"], set(), {"G": {"a": 3}}, {"G": {"a"}}, registry=registry)
        self.assertTrue(tasks[0].once)
        self.assertTrue(tasks[0].must_finish)
        self.assertIs(tasks[0].run, registry[0].run)


class RealRegistryTests(unittest.TestCase):
    """Bảng nhiệm vụ thật (registry.py) + priority.py thật."""

    def build(self, activities, settings):
        return build_tasks(activities, {JOIN_BOSS}, load_priorities(), load_must_finish(), settings, REGISTRY)

    def test_keys_exist_in_priority_file(self):
        known = {t["key"] for group in load_priorities().values() for t in [{"key": k} for k in group]}
        missing = [d.key for d in REGISTRY if d.key not in known]
        self.assertEqual(missing, [], "nhiệm vụ trong registry thiếu độ ưu tiên ở priority.py")

    def test_unique_keys(self):
        keys = [d.key for d in REGISTRY]
        self.assertEqual(len(keys), len(set(keys)))

    def test_daily_sub_tasks_sorted_by_priority(self):
        settings = {"Daily Activities": {"General": {"crazy_eggs_hours": 2, "buy_stamina": True,
                                                      "stamina_quantity": 10},
                                         "Offering": True, "Gold Levy": True, "Patrol": True,
                                         "Alliance Donation": 4, "Alliance Help": 0}}
        tasks = self.build(["Daily Activities", "Open Gift Box"], settings)
        ordered = [t.key for t in sorted(tasks, key=lambda t: -t.priority)]
        self.assertEqual(ordered, ["crazy_eggs", "open_gift_box", "daily_buy_stamina", "daily_offering",
                                   "daily_gold_levy", "daily_alliance_donation", "daily_patrol", "daily_rewards"])
        by_key = {t.key: t for t in tasks}
        self.assertTrue(by_key["crazy_eggs"].repeat)
        self.assertTrue(by_key["daily_patrol"].must_finish)
        self.assertFalse(by_key["daily_offering"].must_finish)
        self.assertEqual(by_key["daily_offering"].group, "Daily Activities")
        self.assertNotIn("Daily Activities", by_key)

    def test_event_sub_tasks(self):
        settings = {"Event": {"gather_troops_ground_troop": {"enabled": True, "day": 1},
                              "kings_path_patrol": {"enabled": False}}}
        tasks = self.build(["Event"], settings)
        self.assertEqual([(t.key, t.priority) for t in sorted(tasks, key=lambda t: -t.priority)],
                         [("gather_troops_ground_troop", 552), ("gather_troops_claim", 500),
                          ("three_day_event", 498)])

    def test_battlefield_shop_excluded_black_market_once(self):
        tasks = self.build(["Battlefield Shop", "Black Market"], {})
        self.assertEqual([(t.key, t.once) for t in tasks], [("black_market_market", True)])

    def test_task_run_is_the_task_own_function(self):
        """Task.run là hàm riêng của nhiệm vụ, không phải hàm run của activity."""
        from bot.activities.event_center import crazy_eggs  # noqa: F401
        tasks = {t.key: t for t in self.build(["Open Gift Box", "Alliance Capacity"], {})}
        from bot.activities import ACTIVITIES
        self.assertIs(tasks["open_gift_box"].run, ACTIVITIES["Open Gift Box"])
        self.assertIs(tasks["alliance_capacity"].run, ACTIVITIES["Alliance Capacity"])

    def test_real_priority_file_loads(self):
        self.assertIn("Crazy Eggs", load_priorities())


class WorkerLoopTests(unittest.TestCase):
    def make_worker(self, activities, specs):
        """specs: [(key, priority, run)]; run(ctx, settings) chạy khi nhiệm vụ được chọn."""
        worker = BotWorker("b", activities, {"Initialization": {"server": "1"}},
                           server_clock=ServerClock("known"))
        worker.ctx = BotContext(SimpleNamespace(serial="b"), worker._stop, None, worker.log)
        tasks = [Task(key, "G", priority, run=run) for key, priority, run in specs]
        patcher = mock.patch.object(bot_worker, "build_tasks", return_value=tasks)
        patcher.start()
        self.addCleanup(patcher.stop)
        return worker

    def run_until_stop(self, worker, run_activity=None):
        """Chạy vòng lặp tới khi Stop: thoát ở điều kiện while hoặc qua StopRequested đều đúng."""
        if run_activity is not None:
            worker._run_activity = run_activity
        try:
            worker._run_tasks()
        except StopRequested:
            pass
        self.assertTrue(worker._stop.is_set(), 'vòng lặp chỉ được dừng khi Stop')

    def test_one_task_per_boss_round_by_priority(self):
        """Mỗi vòng: 1 lượt Join Boss rồi đúng 1 nhiệm vụ (ưu tiên cao trước), xong là quay lại boss."""
        calls = []
        worker = self.make_worker(
            [JOIN_BOSS, "G"],
            [("low", 1, lambda ctx, s: calls.append("low")), ("high", 9, lambda ctx, s: calls.append("high"))])

        def run_activity(activity, settings):
            calls.append(activity)
            if activity == JOIN_BOSS and calls.count(JOIN_BOSS) == 3:
                worker._stop.set()
            return BOSS_IDLE

        self.run_until_stop(worker, run_activity)
        self.assertEqual(calls, [JOIN_BOSS, "high", JOIN_BOSS, "low", JOIN_BOSS])

    def test_task_run_called_directly_with_group_settings(self):
        """Worker gọi thẳng run của nhiệm vụ với cấu hình tab của group, không đi qua ACTIVITIES."""
        got = []

        def run(ctx, settings):
            got.append((ctx, settings))
            worker._stop.set()

        worker = self.make_worker(["G"], [("a", 1, run)])
        worker.settings["G"] = {"x": 1}
        with mock.patch.object(bot_worker, "ACTIVITIES", {}):
            self.run_until_stop(worker)
        self.assertEqual(got, [(worker.ctx, {"x": 1})])

    def test_without_boss_thread_stays_alive(self):
        """Không chọn Join Boss: làm hết nhiệm vụ rồi vẫn chờ (không return) cho tới khi Stop."""
        calls = []
        sleeps = []
        worker = self.make_worker(["G"], [("a", 2, lambda c, s: calls.append("a")),
                                          ("b", 1, lambda c, s: calls.append("b"))])

        def sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) == 3:
                worker._stop.set()
            worker.ctx.check()

        worker.ctx.sleep = sleep
        self.run_until_stop(worker)
        self.assertEqual(calls, ["a", "b"])
        self.assertEqual(sleeps, [bot_worker.IDLE_WAIT] * 3)
        self.assertIsNone(worker.ctx._deadline)   # gỡ deadline sau mỗi nhiệm vụ

    def test_no_time_limit_without_boss(self):
        """Không chọn Join Boss: không có giới hạn 120 giây, không bật ngắt bởi boss."""
        calls = []

        def make(key):
            def run(ctx, settings):
                calls.append((key, ctx._deadline, ctx._boss_interrupt_enabled))
                if key == "b":
                    worker._stop.set()
            return run

        worker = self.make_worker(["G"], [("a", 2, make("a")), ("b", 1, make("b"))])
        self.run_until_stop(worker)
        self.assertEqual(calls, [("a", None, False), ("b", None, False)])

    def test_task_limited_to_120s_with_boss(self):
        """Có Join Boss: mỗi nhiệm vụ tối đa 120 giây; hết giờ thì làm lại đầu tiên ở vòng sau."""
        calls = []

        def run_a(ctx, settings):
            calls.append("a")
            self.assertIsNotNone(ctx._deadline)
            self.assertTrue(ctx._boss_interrupt_enabled)
            if calls.count("a") == 1:
                ctx._deadline = 0   # giả lập đã hết 120 giây
                ctx.check()

        def run_b(ctx, settings):
            calls.append("b")
            worker._stop.set()

        worker = self.make_worker([JOIN_BOSS, "G"], [("a", 2, run_a), ("b", 1, run_b)])

        def run_activity(activity, settings):
            calls.append(activity)
            return BOSS_IDLE

        self.run_until_stop(worker, run_activity)
        self.assertEqual(calls, [JOIN_BOSS, "a", JOIN_BOSS, "a", JOIN_BOSS, "b"])

    def test_bubble_off_no_bubble_rule(self):
        """Không tích Bubble: không lo bubble trước nhiệm vụ, không hẹn ngắt vì bubble."""
        def run(ctx, settings):
            self.assertIsNone(ctx._bubble_due_at)
            worker._stop.set()

        worker = self.make_worker(["G"], [("a", 1, run)])
        self.assertFalse(worker.bubble_enabled)
        with mock.patch.object(bot_worker, "keep_bubble") as keep:
            self.run_until_stop(worker)
        keep.assert_not_called()

    def test_boss_stopped_still_runs_tasks(self):
        """Join Boss dừng hẳn (không phải IDLE): không gọi lại boss nữa, vẫn chạy các nhiệm vụ."""
        calls = []

        def run_b(ctx, settings):
            calls.append("b")
            worker._stop.set()

        worker = self.make_worker([JOIN_BOSS, "G"], [("a", 2, lambda c, s: calls.append("a")), ("b", 1, run_b)])

        def run_activity(activity, settings):
            calls.append(activity)
            return None

        self.run_until_stop(worker, run_activity)
        self.assertEqual(calls, [JOIN_BOSS, "a", "b"])

    def test_only_boss_runs_boss_continuously(self):
        worker = self.make_worker([JOIN_BOSS], [])
        calls = []

        def run_activity(activity, settings):
            calls.append((activity, settings.get("exit_when_idle", False)))

        worker._run_activity = run_activity
        worker._run_tasks()
        self.assertEqual(calls, [(JOIN_BOSS, False)])

    def test_again_after_set_by_task_reschedules(self):
        """Nhiệm vụ gán ctx.again_after (VD Crazy Eggs chưa đủ 4 quả vỡ): bộ chọn hẹn chạy lại."""
        calls = []

        def run(ctx, settings):
            calls.append(1)
            ctx.again_after = 60
            worker._stop.set()

        worker = self.make_worker(["G"], [("a", 1, run)])
        with mock.patch.object(Scheduler, "finished", autospec=True) as finished:
            self.run_until_stop(worker)
        self.assertEqual(finished.call_args.kwargs["again_after"], 60)


if __name__ == "__main__":
    unittest.main()
