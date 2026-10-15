"""
Danh sách nhiệm vụ (tasks.py build_tasks, bảng priority.py) và vòng lặp nhiệm vụ
của BotWorker (bot/worker/TODO.md mục 1: Bubble > Join Boss > nhiệm vụ; mỗi vòng 1 lượt Join Boss + 1 nhiệm vụ;
không còn nhiệm vụ tới lượt thì thread vẫn sống). Worker gọi thẳng `run` riêng của từng nhiệm vụ.
"""
import time
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import mock

from bot.worker.tasks import DEFAULT_PRIORITY, REGISTRY, Task, build_tasks
from bot.context import BotContext
from bot.context.errors import StopRequested
from bot.worker import bot_worker, guards
from bot.worker.bot_worker import BOSS_IDLE, JOIN_BOSS, BotWorker
from bot.worker.server_clock import ServerClock

def _fake_registry(*specs):
    """[(key, group, enabled, once)] hoặc [(key, group, enabled, once, priority, must_finish)] -> Task giả."""
    tasks = []
    for key, group, enabled, once, *rest in specs:
        priority, must_finish = (rest + [DEFAULT_PRIORITY, False])[:2] if rest else (DEFAULT_PRIORITY, False)
        tasks.append(Task(key, group, priority, must_finish=must_finish, once=once, run=lambda bot, s: None,
                          enabled=(lambda s, e=enabled: e(s) if callable(e) else e)))
    return tasks


class BuildTasksTests(unittest.TestCase):
    def test_only_selected_groups_and_enabled_tasks(self):
        """Chỉ nhiệm vụ có group được chọn và đã được tích; activity chỉ để chia loại."""
        registry = _fake_registry(("a", "G1", True, False, 5), ("b", "G1", False, False, 9), ("c", "G2", True, False, 7))
        tasks = build_tasks(["G1"], set(), settings={}, registry=registry)
        self.assertEqual([(t.key, t.group, t.priority) for t in tasks], [("a", "G1", 5)])

    def test_enabled_receives_group_settings(self):
        registry = _fake_registry(("a", "G1", lambda s: s.get("x"), False))
        tasks = build_tasks(["G1"], set(), settings={"G1": {"x": True}}, registry=registry)
        self.assertEqual([t.key for t in tasks], ["a"])
        self.assertEqual(tasks[0].priority, DEFAULT_PRIORITY)
        self.assertEqual(build_tasks(["G1"], set(), settings={"G1": {"x": False}}, registry=registry), [])

    def test_skip_group(self):
        registry = _fake_registry(("a", "G1", True, False))
        self.assertEqual(build_tasks(["G1"], {"G1"}, registry=registry), [])

    def test_negative_priority_not_in_task_list(self):
        """Ưu tiên < 0 không được đưa vào danh sách nhiệm vụ; 0 trở lên thì có."""
        registry = _fake_registry(("zero", "G", True, False, 0), ("neg", "G", True, False, -1),
                                  ("pos", "G", True, False, 5))
        tasks = build_tasks(["G"], set(), registry=registry)
        self.assertEqual([t.key for t in tasks], ["zero", "pos"])

    def test_flags_and_run_carried_to_task(self):
        registry = _fake_registry(("a", "G", True, True, 3, True))
        tasks = build_tasks(["G"], set(), registry=registry)
        self.assertTrue(tasks[0].once)
        self.assertTrue(tasks[0].must_finish)
        self.assertIs(tasks[0].run, registry[0].run)


class RealRegistryTests(unittest.TestCase):
    """Bảng nhiệm vụ thật (priority.py)."""

    def build(self, activities, settings):
        return build_tasks(activities, {JOIN_BOSS}, settings)

    def test_every_task_has_a_priority_and_a_run_in_the_table(self):
        from bot.worker.priority import DATA
        rows = {e["key"]: e for g, v in DATA.items() if isinstance(v, list) for e in v}
        for task in REGISTRY:
            self.assertIn("priority", rows[task.key], task.key)
            self.assertTrue(callable(rows[task.key]["run"]) or isinstance(rows[task.key]["run"], dict), task.key)

    def test_unique_keys(self):
        keys = [d.key for d in REGISTRY]
        self.assertEqual(len(keys), len(set(keys)))

    def test_daily_sub_tasks_sorted_by_priority(self):
        settings = {"Daily Activities": {"General": {"crazy_eggs_hours": 2, "buy_stamina": True,
                                                      "stamina_quantity": 10},
                                         "Offering": True, "Gold Levy": True, "Patrol": True,
                                         "Alliance Donation": 4, "Alliance Help": 0}}
        tasks = self.build(["Daily Activities", "Open Gift Box"], settings)
        ordered = [t.key for t in tasks]   # build_tasks đã xếp theo độ ưu tiên
        self.assertEqual(ordered, ["crazy_eggs", "open_gift_box", "daily_buy_general", "daily_offering",
                                   "daily_gold_levy", "daily_alliance_donation", "daily_patrol", "daily_rewards",
                                   "daily_gift_claims"])
        by_key = {t.key: t for t in tasks}
        self.assertIsNotNone(by_key["crazy_eggs"].due)   # việc theo giờ: tới giờ mới đẩy lên đầu danh sách
        self.assertTrue(by_key["daily_patrol"].must_finish)
        self.assertTrue(by_key["daily_offering"].must_finish)   # mọi việc Daily: làm tới xong, không giới hạn 120 giây
        self.assertEqual(by_key["daily_offering"].group, "Daily Activities")
        self.assertNotIn("Daily Activities", by_key)

    def test_event_sub_tasks(self):
        settings = {"Event": {"gather_troops_ground_troop": {"enabled": True, "day": 1},
                              "kings_path_patrol": {"enabled": False}}}
        tasks = self.build(["Event"], settings)
        self.assertEqual([(t.key, t.priority) for t in tasks],
                         [("gather_troops_ground_troop", 552), ("gather_troops_claim", 500),
                          ("three_day_event", 498)])

    def test_alliance_capacity_runs_once_and_saves_nothing(self):
        """Alliance Capacity chỉ làm 1 lần (once) và xong thì không lưu gì vào DB (done = None: xong khi chạy hết một lượt)."""
        task = {t.key: t for t in REGISTRY}["alliance_capacity"]
        self.assertTrue(task.once)
        self.assertIsNone(task.done)
        self.assertIsNone(task.due)

    def test_battlefield_shop_excluded_black_market_once(self):
        tasks = self.build(["Battlefield Shop", "Black Market"], {})
        self.assertEqual([(t.key, t.once) for t in tasks], [("black_market_market", True)])

    def test_task_run_is_the_task_own_function(self):
        """Task.run là hàm riêng của nhiệm vụ, không phải hàm run của activity."""
        from bot.activities.event_center import crazy_eggs  # noqa: F401
        tasks = {t.key: t for t in self.build(["Open Gift Box", "Alliance Capacity"], {})}
        from bot.activities import ACTIVITIES
        self.assertIs(tasks["open_gift_box"].run, ACTIVITIES["Open Gift Box"])   # nhiệm vụ tự lưu "xong hôm nay"
        self.assertIs(tasks["alliance_capacity"].run, ACTIVITIES["Alliance Capacity"])

    def test_every_row_with_run_is_a_task(self):
        from bot.worker.priority import DATA
        rows = [e for g, v in DATA.items() if isinstance(v, list) for e in v]
        self.assertEqual(len(REGISTRY), sum(1 for e in rows if "run" in e))
        self.assertTrue(all("handler" in e for e in rows if e["key"] == "join_monster_war"))   # không vào danh sách

    def test_event_catalog_matches_priority_rows(self):
        """Mọi nhiệm vụ Event trong danh mục EVENTS có một dòng `run` ở priority.py."""
        from bot.activities.event.run import EVENTS
        keys = {d.key for d in REGISTRY}
        wanted = {k for *_, ts in EVENTS for k, _ in ts}
        self.assertEqual(sorted(wanted - keys), [])

    def test_real_priority_file_loads(self):
        from bot.worker.priority import DATA
        self.assertIn("Crazy Eggs", DATA)


class WorkerLoopTests(unittest.TestCase):
    def make_worker(self, activities, specs):
        """specs: [(key, priority, run)]; run(ctx, settings) chạy khi nhiệm vụ được chọn."""
        worker = BotWorker("b", activities, {"Initialization": {"server": "1"}},
                           server_clock=ServerClock("known"))
        worker.ctx = BotContext(SimpleNamespace(serial="b"), worker._stop, None, worker.log)
        worker.ctx.shell = mock.Mock()   # đóng game ở mốc reset server: không chạm thiết bị thật
        wait = mock.patch.object(guards, "RESTART_WAIT", 0)
        wait.start()
        self.addCleanup(wait.stop)
        tasks = sorted((Task(key, "G", priority, run=run) for key, priority, run in specs), key=lambda t: -t.priority)
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
        """Có Join Boss: mỗi nhiệm vụ tối đa 120 giây; hết giờ thì sau Join Boss làm tiếp chính nhiệm vụ đó."""
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
        self.assertFalse(worker.guards.bubble.enabled)
        with mock.patch.object(guards, "keep_bubble") as keep:
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

    def with_flags(self, worker, done=None, due=None):
        """Gắn `done` / `due` cho nhiệm vụ của worker: done[key] / due[key] là dict cờ có thể đổi trong lúc chạy."""
        for task in worker_tasks():
            if done is not None:
                task.done = lambda ctx, s, key=task.key: done[key]
            if due is not None and task.key in due:
                task.due = lambda ctx, s, key=task.key: due[key]

    def test_not_done_task_goes_to_the_end(self):
        """Nhiệm vụ chưa xong chuyển xuống cuối danh sách, làm việc khác trước rồi mới quay lại."""
        calls, done = [], {"a": False, "b": False}

        def run_a(ctx, s):
            calls.append("a")
            done["a"] = calls.count("a") == 2   # lần đầu chưa xong, lần hai xong

        def run_b(ctx, s):
            calls.append("b")
            done["b"] = True

        worker = self.make_worker(["G"], [("a", 2, run_a), ("b", 1, run_b)])
        self.with_flags(worker, done=done)

        def sleep(seconds):
            worker._stop.set()
            worker.ctx.check()

        worker.ctx.sleep = sleep
        self.run_until_stop(worker)
        self.assertEqual(calls, ["a", "b", "a"])

    def test_done_tasks_are_dropped_each_loop(self):
        """Nhiệm vụ đã xong hôm nay (theo DB) bị loại khỏi danh sách, không chạy."""
        calls = []

        def run_todo(ctx, s):
            calls.append("todo")
            worker._stop.set()

        worker = self.make_worker(["G"], [("done", 9, lambda c, s: calls.append("done")), ("todo", 1, run_todo)])
        self.with_flags(worker, done={"done": True, "todo": False})
        self.run_until_stop(worker)
        self.assertEqual(calls, ["todo"])

    def test_done_task_comes_back_when_the_db_says_not_done_any_more(self):
        """Mỗi vòng đọc lại DB: nhiệm vụ đã xong mà giữa ngày đổi mục tiêu ở tab (thành chưa xong) thì được làm lại ngay."""
        calls, done = [], {"a": True, "b": False}

        def run_b(ctx, s):
            calls.append("b")
            done["b"] = True
            done["a"] = False      # giả lập đổi mục tiêu ở tab: a thành chưa xong

        def run_a(ctx, s):
            calls.append("a")
            done["a"] = True
            worker._stop.set()

        worker = self.make_worker(["G"], [("a", 9, run_a), ("b", 1, run_b)])
        self.with_flags(worker, done=done)
        self.run_until_stop(worker)
        self.assertEqual(calls, ["b", "a"])

    def test_done_before_the_reset_time_is_not_done_after_it(self):
        """Xong lúc 12:00, qua mốc reset 14:00 cùng ngày thì không còn tính là xong (is_daily_done so với mốc reset)."""
        from bot.daily_reset import done_today
        done_at = datetime(2026, 10, 11, 12, 0).isoformat()
        self.assertTrue(done_today(done_at, "14:00", datetime(2026, 10, 11, 13, 59)))
        self.assertFalse(done_today(done_at, "14:00", datetime(2026, 10, 11, 14, 0)))
        self.assertFalse(done_today(done_at, "14:00", datetime(2026, 10, 12, 9, 0)))

    def test_all_not_done_pauses_before_next_pass(self):
        """Cả danh sách đều chưa xong: nghỉ IDLE_WAIT sau mỗi lượt qua hết danh sách, không chạy liên tục."""
        calls, sleeps = [], []
        worker = self.make_worker(["G"], [("a", 2, lambda c, s: calls.append("a")),
                                          ("b", 1, lambda c, s: calls.append("b"))])
        self.with_flags(worker, done={"a": False, "b": False})

        def sleep(seconds):
            sleeps.append((seconds, list(calls)))
            if len(sleeps) == 2:
                worker._stop.set()
            worker.ctx.check()

        worker.ctx.sleep = sleep
        self.run_until_stop(worker)
        self.assertEqual(sleeps, [(bot_worker.IDLE_WAIT, ["a", "b"]), (bot_worker.IDLE_WAIT, ["a", "b", "a", "b"])])

    def test_new_day_puts_done_tasks_back(self):
        """Sang ngày mới (qua mốc reset server): nhiệm vụ đã xong được đưa lại vào danh sách."""
        calls, done = [], {"a": False}
        day = [datetime(2026, 10, 3, 9)]

        def run_a(ctx, s):
            calls.append("a")
            if len(calls) == 1:
                done["a"] = True          # xong hôm nay
            else:
                worker._stop.set()

        worker = self.make_worker(["G"], [("a", 1, run_a)])
        self.with_flags(worker, done=done)

        def sleep(seconds):
            if len(calls) == 1:           # đang nghỉ vì danh sách rỗng: sang ngày mới, chưa xong lại
                day[0] += timedelta(days=1)
                done["a"] = False
            worker.ctx.check()

        worker.ctx.sleep = sleep
        with mock.patch.object(bot_worker, "last_reset", side_effect=lambda server_time: day[0]):
            self.run_until_stop(worker)
        self.assertEqual(calls, ["a", "a"])

    def test_game_is_closed_at_the_reset_time(self):
        """Tới mốc reset server: tắt game bật lại (am force-stop) đúng một lần, giữa hai nhiệm vụ."""
        calls, done = [], {"a": False}
        day = [datetime(2026, 10, 3, 9)]

        def run_a(ctx, s):
            calls.append("a")
            done["a"] = len(calls) == 1
            if len(calls) == 2:
                worker._stop.set()

        worker = self.make_worker(["G"], [("a", 1, run_a)])
        self.with_flags(worker, done=done)

        def sleep(seconds):
            if len(calls) == 1:
                day[0] += timedelta(days=1)       # đang nghỉ vì xong hết: sang ngày mới
                done["a"] = False
            worker.ctx.check()

        worker.ctx.sleep = sleep
        with mock.patch.object(bot_worker, "last_reset", side_effect=lambda server_time: day[0]):
            self.run_until_stop(worker)
        self.assertEqual(calls, ["a", "a"])
        shell = [c.args[0] for c in worker.ctx.shell.call_args_list]
        self.assertEqual(len(shell), 1)
        self.assertIn("force-stop", shell[0])

    def test_reset_time_interrupts_even_a_must_finish_task(self):
        """Tới đúng mốc reset server: ngắt cả nhiệm vụ must_finish (Bubble / Auto Times Out thì bị hoãn), tắt game bật lại, rồi làm
        lại việc đang dở từ đầu."""
        calls = []

        def run_a(ctx, s):
            calls.append("a")
            if len(calls) == 1:
                ctx._reset_due_at = time.monotonic() - 1     # giả lập vừa tới 14:00 giữa lúc đang làm
                worker.guards.reset_handled = datetime.min   # mốc reset mới này chưa xử lý
            ctx.check()                                      # lần đầu ném ResetDue
            worker._stop.set()

        worker = self.make_worker(["G"], [("a", 1, run_a)])
        for task in worker_tasks():
            task.must_finish = True
        self.run_until_stop(worker)
        self.assertEqual(calls, ["a", "a"])                  # làm lại từ đầu sau khi game mở lại
        shell = [c.args[0] for c in worker.ctx.shell.call_args_list]
        self.assertEqual(len(shell), 1)
        self.assertIn("force-stop", shell[0])

    def test_reset_time_is_armed_for_the_next_reset(self):
        """Mỗi lần gọi qua guards.call, ctx được hẹn ngắt đúng mốc reset kế tiếp (hôm nay hoặc ngày mai)."""
        worker = self.make_worker(["G"], [])
        before = time.monotonic()
        worker.guards.call(None, lambda: None)
        waiting = worker.ctx._reset_due_at - before
        self.assertGreater(waiting, 0)
        self.assertLessEqual(waiting, 24 * 3600 + 5)

    def test_game_is_not_closed_when_the_day_does_not_change(self):
        calls = []
        worker = self.make_worker(["G"], [("a", 1, lambda c, s: (calls.append("a"), worker._stop.set()))])
        self.run_until_stop(worker)
        worker.ctx.shell.assert_not_called()

    def test_once_task_not_put_back_on_new_day(self):
        """Nhiệm vụ `once` xong rồi thì sang ngày mới cũng không đưa lại (chỉ chạy lại khi Start lại)."""
        calls, sleeps = [], []
        day = [datetime(2026, 10, 3, 9)]
        worker = self.make_worker(["G"], [("a", 1, lambda c, s: calls.append("a"))])
        for task in worker_tasks():
            task.once = True

        def sleep(seconds):
            sleeps.append(seconds)
            day[0] += timedelta(days=1)
            if len(sleeps) == 3:
                worker._stop.set()
            worker.ctx.check()

        worker.ctx.sleep = sleep
        with mock.patch.object(bot_worker, "last_reset", side_effect=lambda server_time: day[0]):
            self.run_until_stop(worker)
        self.assertEqual(calls, ["a"])

    def test_gives_up_after_max_attempts_per_day(self):
        """Chạy hết một lượt mà vẫn chưa xong: tối đa MAX_ATTEMPTS lần mỗi ngày, rồi bỏ qua tới ngày mới."""
        calls, sleeps = [], []
        day = [datetime(2026, 10, 3, 9)]
        worker = self.make_worker(["G"], [("a", 1, lambda c, s: calls.append("a"))])
        self.with_flags(worker, done={"a": False})

        def sleep(seconds):
            sleeps.append(len(calls))
            if len(calls) > bot_worker.MAX_ATTEMPTS:
                worker._stop.set()                    # đã thử lại sau khi sang ngày mới
            elif len(sleeps) == bot_worker.MAX_ATTEMPTS + 3:
                day[0] += timedelta(days=1)           # bỏ cuộc rồi, sang ngày mới: được thử lại
            worker.ctx.check()

        worker.ctx.sleep = sleep
        with mock.patch.object(bot_worker, "last_reset", side_effect=lambda server_time: day[0]):
            self.run_until_stop(worker)
        self.assertEqual(calls.count("a"), bot_worker.MAX_ATTEMPTS + 1)   # 6 lần hôm trước + 1 lần sau khi sang ngày

    def test_interrupted_run_is_not_an_attempt(self):
        """Bị ngắt giữa chừng (không phải chạy hết một lượt) thì không tính là một lần thử."""
        calls = []

        def run_a(ctx, s):
            calls.append("a")
            if len(calls) <= bot_worker.MAX_ATTEMPTS + 2:
                ctx._deadline = 0
                ctx.check()                   # TimedOut
            worker._stop.set()

        worker = self.make_worker([JOIN_BOSS, "G"], [("a", 1, run_a)])
        self.with_flags(worker, done={"a": False})
        self.run_until_stop(worker, lambda activity, settings: BOSS_IDLE)
        self.assertEqual(len(calls), bot_worker.MAX_ATTEMPTS + 3)

    def test_timed_task_runs_as_soon_as_it_is_due(self):
        """Việc theo giờ: mỗi vòng chỉ so giờ; chưa tới giờ thì bỏ qua, tới giờ thì làm ngay trước các việc còn lại."""
        calls, due, done = [], {"t": False}, {"x": False, "y": False, "t": False}

        def run_x(ctx, s):
            calls.append("x")
            done["x"] = True
            due["t"] = True    # tới giờ

        def run_y(ctx, s):
            calls.append("y")
            done["y"] = True

        def run_t(ctx, s):
            calls.append("t")
            done["t"] = True
            worker._stop.set()

        worker = self.make_worker(["G"], [("x", 9, run_x), ("y", 5, run_y), ("t", 1, run_t)])
        self.with_flags(worker, done=done, due=due)
        self.run_until_stop(worker)
        self.assertEqual(calls, ["x", "t"])   # t tới giờ nên làm ngay, trước y


def worker_tasks():
    """Danh sách Task mà make_worker đã patch cho build_tasks."""
    return bot_worker.build_tasks()


if __name__ == "__main__":
    unittest.main()
