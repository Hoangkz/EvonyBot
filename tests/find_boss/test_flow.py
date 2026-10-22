"""Flow tests cho Find Boss: bot giả (chưa có ảnh chụp thành -> thế giới nên không dùng chuỗi ảnh, xem FLOW.md), scan_bosses giả.

Kiểm tra: ra bản đồ thế giới, truyền đúng góc / bán kính / share, chỉ boss được tích tính là active, bỏ Viking,
bỏ qua khi chưa tích boss; chia góc của nút Auto; dòng trong bảng nhiệm vụ của worker.
"""
import importlib
import unittest
from unittest import mock

from bot.activities.find_boss import JOB
run_module = importlib.import_module("bot.activities.find_boss.run")
run = run_module.run
from bot.activities.find_boss.angles import split_angles
from bot.activities.find_boss.constants import TO_WORLD_TAP, TO_WORLD_WAIT
from bot.activities.find_boss.run import HOME_ICON
from bot.ocr import find_bosses

BOSS = {"category_key": "special_and_recurring_event_bosses", "name": "Ymir", "levels": [3]}
VIKING = {"category_key": "mythical_and_elite_bosses", "name": "Viking", "levels": []}


class FakeBot:
    """Ở thành cho tới khi bấm nút góc dưới phải thì sang thế giới (thấy HOME_ICON)."""
    def __init__(self, on_world=False):
        self.on_world, self.taps, self.logs, self.done = on_world, [], [], []

    def screenshot(self):
        return "screen"

    def find(self, path, **kw):
        return (10, 10) if path == HOME_ICON and self.on_world else None

    def tap_percent(self, x, y, delay=0, count=1):
        self.taps.append((x, y, delay))
        self.on_world = True

    def mark_daily_done(self, key):
        self.done.append(key)

    def log(self, message):
        self.logs.append(message)

    record = log


def patched(found=(), selection_seen=None):
    """Mock scan_bosses/ensure_map; `selection_seen` receives the active list."""
    def scan(bot, start, end, radius, share=True, **kw):
        scan.args = (start, end, radius, share)
        if selection_seen is not None:
            find_bosses._state().pop("catalog", None)
            selection_seen.extend(f"{e[0]}:{sorted(lv for lv, (_, on) in e[1].items() if on)}:{e[2]}" for e in find_bosses._catalog()[0] if e[0] in ("Ymir", "Viking", "Zombie"))
        return list(found)
    return (scan, mock.patch.object(run_module, "scan_bosses", scan),
            mock.patch.object(run_module, "ensure_map", return_value=True))


class FindBossFlowTests(unittest.TestCase):
    def run_with(self, settings, bot=None, found=(), seen=None):
        bot = bot or FakeBot()
        scan, *patches = patched(found, seen)
        with patches[0], patches[1] as ensure_map:
            run(bot, settings)
        return bot, scan, ensure_map

    def test_goes_to_world_and_scans_with_settings(self):
        bot, scan, city = self.run_with({"start_deg": 90, "end_deg": 180, "radius": 120, "share": False, "selected_bosses": [BOSS]},
                                        found=[{"name": "Ymir", "level": 3, "x": 1, "y": 2}])
        self.assertEqual(bot.taps, [(*TO_WORLD_TAP, TO_WORLD_WAIT)])
        self.assertEqual(scan.args, (90, 180, 120, False))
        self.assertEqual(bot.done, [])

    def test_already_on_world_does_not_tap(self):
        bot, *_ = self.run_with({"selected_bosses": [BOSS]}, bot=FakeBot(on_world=True))
        self.assertEqual(bot.taps, [])

    def test_defaults_full_circle_share(self):
        _, scan, _ = self.run_with({"selected_bosses": [BOSS]})
        self.assertEqual(scan.args, (0, 360, 300, True))

    def test_no_boss_ticked_skips_scan(self):
        scan, *patches = patched()
        bot = FakeBot()
        with patches[0], patches[1]:
            run(bot, {"selected_bosses": [VIKING]})        # Viking bị bỏ -> không còn boss nào
        self.assertFalse(hasattr(scan, "args"))
        self.assertEqual(bot.done, [])

    def test_only_ticked_boss_levels_are_active_and_viking_excluded(self):
        seen = []
        self.run_with({"selected_bosses": [BOSS, VIKING]}, seen=seen)
        self.assertCountEqual(seen, ["Ymir:[3]:False", "Viking:[]:False", "Zombie:[]:False"])
        find_bosses.set_selection(None)

    def test_cannot_reach_world_does_not_scan(self):
        bot = FakeBot()
        bot.tap_percent = lambda *a, **k: None            # bấm không ra thế giới
        scan, *patches = patched()
        with patches[0], patches[1], mock.patch.object(run_module, "go_home"), mock.patch.object(run_module, "delay"):
            run(bot, {"selected_bosses": [BOSS]})
        self.assertFalse(hasattr(scan, "args"))
        self.assertEqual(bot.done, [])


class SwipeWatchTests(unittest.TestCase):
    """arc_sweep: cứ 3 cú kéo gọi bot.swipe_watch; báo đã rời bản đồ thì recover + về gốc + kéo lại tới ô đang dở."""

    def setUp(self):
        from bot.common import arc_sweep
        patch = mock.patch.object(arc_sweep, "WATCH_EVERY", 3)      # các test dưới tính theo chu kỳ 3 cú (giá trị thật là 1)
        patch.start()
        self.addCleanup(patch.stop)

    def make_bot(self, watch_results):
        from bot.common import arc_sweep
        bot = mock.Mock()
        bot.swipe_count = 0
        bot.swipe_recover = mock.Mock()
        results = iter(watch_results)
        bot.swipe_watch = mock.Mock(side_effect=lambda b: next(results, False))
        return arc_sweep, bot

    def test_watch_called_every_third_swipe(self):
        arc_sweep, bot = self.make_bot([False, False])
        path = [(0, 0)] + [(0, 100 * k) for k in range(1, 8)]          # 7 cú kéo
        with mock.patch.object(arc_sweep, "_swipe", return_value=(True, None)):
            arc_sweep._walk(bot, path, None, set(), None, None)
        self.assertEqual(bot.swipe_watch.call_count, 2)                # sau cú 3 và cú 6

    def walk_after_leaving(self, camera):
        """Cú kéo thứ 3 báo đã rời bản đồ; `camera` = toạ độ camera đọc được sau khi quay lại. Trả (số cú kéo, bot, go_home giả)."""
        arc_sweep, bot = self.make_bot([True])
        path = [(0, 0)] + [(0, 100 * k) for k in range(1, 5)]
        swipes = []
        with mock.patch.object(arc_sweep, "_swipe", side_effect=lambda *a, **k: (swipes.append(a[1:3]), (True, None))[1]),                 mock.patch.object(arc_sweep, "go_home") as home, mock.patch.object(arc_sweep, "_camera", return_value=camera):
            arc_sweep._walk(bot, path, (600, 600), set(), None, None)
        return len(swipes), bot, home

    def test_camera_still_in_place_continues_without_going_home(self):
        """Join Boss xong, Back về bản đồ thế giới, camera vẫn ở ô đang dở: kéo tiếp luôn, không bấm về thành, không kéo lại."""
        from bot.common.arc_sweep import px_to_world
        u, v = px_to_world(0, 300)                                       # ô thứ 3 của đường
        count, bot, home = self.walk_after_leaving((round(600 + u), round(600 + v)))
        bot.swipe_recover.assert_called_once()
        home.assert_not_called()
        self.assertEqual(count, 4)                                       # đúng 4 cú của đường, không cú kéo lại

    def test_camera_moved_away_goes_home_and_replays(self):
        count, bot, home = self.walk_after_leaving((100, 100))
        home.assert_called_once()
        self.assertEqual(count, 4 + 3)                                   # thêm 3 cú kéo lại tới ô thứ 3


class AutoAnglesTests(unittest.TestCase):
    def test_one_account_full_circle(self):
        self.assertEqual(split_angles(1), [(0, 360)])

    def test_two_accounts_half_each(self):
        self.assertEqual(split_angles(2), [(0, 180), (180, 360)])

    def test_slices_are_contiguous_multiples_of_15(self):
        for n in range(1, 24):
            slices = split_angles(n)
            self.assertEqual(slices[0][0], 0)
            self.assertEqual(slices[-1][1], 360)
            for (_, end), (start, _) in zip(slices, slices[1:]):
                self.assertEqual(end, start)
            self.assertTrue(all(a % 15 == 0 and b % 15 == 0 and a < b for a, b in slices))

    def test_more_accounts_than_slices_reuse_slices(self):
        slices = split_angles(30)
        self.assertEqual(len(slices), 30)
        self.assertTrue(all(b - a == 15 for a, b in slices))


class WorkerRowTests(unittest.TestCase):
    def test_row_enabled_only_with_a_boss_ticked_and_runs_without_interval(self):
        self.assertFalse(JOB["enabled"]({"selected_bosses": []}))
        self.assertFalse(JOB["enabled"]({"selected_bosses": [VIKING]}))
        self.assertTrue(JOB["enabled"]({"selected_bosses": [BOSS]}))
        from bot.worker.tasks import REGISTRY
        task = next(t for t in REGISTRY if t.key == "find_boss")
        self.assertEqual(task.group, "Find Boss")
        self.assertIsNone(task.due)             # không có ô Every: quét liên tục khi rảnh
        self.assertTrue(task.idle_only)


if __name__ == "__main__":
    unittest.main()
