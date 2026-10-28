"""Attack Boss nguồn IsCout: bấm vòng boss gần giữa nhất; không thấy / không ra Attack thì tính là đã đánh (không cần giả lập)."""
import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

from bot.activities.attack_boss.constants import (ATTACK_MENU_POLL, ATTACK_MENU_WAIT, BOSS_NEAR, BOSS_POLL, BOSS_WAIT, DROP, GLOW_TAP_DX, GLOW_TAP_DY, RETRY)
from bot.activities.attack_boss.sources import BossOffer
from bot.common import boss_scan

run = importlib.import_module("bot.activities.attack_boss.run")      # `attack_boss.run` là hàm run của package, lấy module qua importlib
CENTER = boss_scan.CAMERA_PX


def fake_bot():
    return SimpleNamespace(sleep=lambda seconds: None, screenshot=lambda: None, log=lambda message: None, tap=lambda *args, **kwargs: None)


def boss_at(dx, dy):
    return {"pos": (CENTER[0] + dx, CENTER[1] + dy)}


class WaitBossTests(unittest.TestCase):
    def test_nearest_ring_is_tapped_even_when_far_from_center(self):
        far = BOSS_NEAR + 100
        rings = [(CENTER[0] + far + 50, CENTER[1]), (CENTER[0], CENTER[1] + far)]      # tâm vòng màu: x giữa, y giữa y nhỏ nhất và lớn nhất
        with mock.patch.object(run, "glow_points", lambda screen: rings), \
                mock.patch.object(run, "find_bosses", lambda screen: [boss_at(far + 50, 0), boss_at(0, far)]):
            self.assertEqual(run._wait_boss(fake_bot(), nearest=True), (CENTER[0] + GLOW_TAP_DX, CENTER[1] + far + GLOW_TAP_DY))
            self.assertIsNone(run._wait_boss(fake_bot()))        # nguồn khác: boss phải gần giữa màn hình

    def test_default_taps_the_center_when_boss_is_near(self):
        with mock.patch.object(run, "find_bosses", lambda screen: [boss_at(10, 10)]):
            self.assertEqual(run._wait_boss(fake_bot()), CENTER)

    def test_no_ring_at_all_returns_none(self):
        with mock.patch.object(run, "glow_points", lambda screen: []):
            self.assertIsNone(run._wait_boss(fake_bot(), nearest=True))


class HomeTests(unittest.TestCase):
    def test_home_is_read_after_pressing_go_home_and_remembered(self):
        pressed = []
        bot = SimpleNamespace(log=lambda message: None, screenshot=lambda: None)
        with mock.patch.object(run, "ensure_world", lambda bot: True),                 mock.patch.object(run.arc_sweep, "go_home", lambda bot: pressed.append(1) or True),                 mock.patch.object(run.arc_sweep, "valid_camera", lambda camera: camera),                 mock.patch.object(run, "read_camera", lambda screen: (562, 93)):
            self.assertEqual(run.home_coords(bot), (562, 93))
            self.assertEqual(run.home_coords(bot), (562, 93))
        self.assertEqual(pressed, [1])         # nút về thành bấm một lần, lần sau dùng toạ độ đã nhớ
        self.assertEqual(bot.attack_home, (562, 93))


class AttackTests(unittest.TestCase):
    def attack_with_no_attack_menu(self, source):
        with (mock.patch.object(run, "ensure_world", lambda bot: True),
              mock.patch.object(run, "_on_spot", lambda bot, offer: True),
              mock.patch.object(run, "_wait_boss", lambda bot, nearest=False: (400, 300)),
              mock.patch.object(run, "_tap_attack", lambda bot, pos: False),
              mock.patch.object(boss_scan, "tap_menu_item", lambda bot, pos, icon: False)):
            return run.attack(fake_bot(), {"source": source}, BossOffer(556, 66, "Rùa Nham thạch", 1, uid="a"))

    def test_iscout_boss_without_attack_menu_counts_as_attacked(self):
        self.assertEqual(self.attack_with_no_attack_menu("api"), DROP)

    def test_other_sources_still_retry_without_attack_menu(self):
        self.assertEqual(self.attack_with_no_attack_menu("alliance_chat"), RETRY)


class AttackMenuTests(unittest.TestCase):
    def bot(self, appears_on_poll=None):
        events = {"naps": [], "taps": [], "polls": 0, "logs": []}

        def screenshot():
            events["polls"] += 1
            return events["polls"]

        def tap(*args, **kwargs):
            events["taps"].append(args)
        bot = SimpleNamespace(sleep=events["naps"].append, screenshot=screenshot, tap=tap, log=events["logs"].append)
        find = lambda b, screen, icon: (150, 250) if appears_on_poll is not None and screen >= appears_on_poll else None
        return bot, events, find

    def test_attack_button_is_looked_for_every_second_and_tapped_when_found(self):
        bot, events, find = self.bot(appears_on_poll=3)
        with mock.patch.object(boss_scan, "find_menu_item", find):
            self.assertTrue(run._tap_attack(bot, (200, 340)))
        self.assertEqual(events["naps"], [ATTACK_MENU_POLL] * 3)
        self.assertEqual(events["taps"], [(200, 340), (150, 250)])       # bấm vào boss, rồi bấm nút Attack

    def test_no_attack_button_for_eight_seconds_gives_up(self):
        bot, events, find = self.bot()
        closed = []
        with mock.patch.object(boss_scan, "find_menu_item", find), mock.patch.object(boss_scan, "ensure_map", closed.append):
            self.assertFalse(run._tap_attack(bot, (200, 340)))
        self.assertEqual(events["naps"], [ATTACK_MENU_POLL] * round(ATTACK_MENU_WAIT / ATTACK_MENU_POLL))
        self.assertEqual((ATTACK_MENU_POLL, ATTACK_MENU_WAIT, sum(events["naps"])), (1, 8, 8))
        self.assertEqual(len(closed), 1)                                  # về bản đồ sạch


class PickTroopTests(unittest.TestCase):
    """Attack Boss chỉ dùng các đội người dùng đã tích, không thử đội khác khi đội đã tích không có tướng."""

    def pick(self, chosen, with_general=()):
        tapped = []
        bot = SimpleNamespace(find_all=lambda *args, **kwargs: [], log=lambda message: None)
        bot.tap_percent = lambda x, y: tapped.append(round((x - run.PRESET_X0) / run.PRESET_DX) + 1)
        bot.find = lambda *args, **kwargs: (1, 1) if tapped and tapped[-1] in with_general else None
        helper = SimpleNamespace(troops=chosen, _poll_screen=lambda name, fn, **kwargs: (None, fn(None)))
        with mock.patch.object(run, "_preset_active", lambda image, troop: True):
            return run._pick_troop(bot, helper, None, None), sorted(set(tapped))

    def test_only_troop_1_chosen_and_no_general_never_taps_troop_2(self):
        picked, tapped = self.pick([1])
        self.assertIsNone(picked)
        self.assertEqual(tapped, [1])

    def test_only_troop_1_chosen_with_general_picks_it(self):
        self.assertEqual(self.pick([1], with_general=(1,)), (1, [1]))

    def test_tries_the_next_chosen_troop_but_not_the_others(self):
        picked, tapped = self.pick([1, 2], with_general=(2,))
        self.assertEqual(picked, 2)
        self.assertEqual(tapped, [1, 2])
        picked, tapped = self.pick([1, 2])
        self.assertIsNone(picked)
        self.assertEqual(tapped, [1, 2])         # không đụng tới đội 3, 4...


class TapOffsetTests(unittest.TestCase):
    def test_tap_is_10px_left_and_10px_above_the_measured_point(self):
        self.assertEqual((GLOW_TAP_DX, GLOW_TAP_DY), (-10, -10))
        with mock.patch.object(run, "glow_points", lambda screen: [(191, 375)]):
            self.assertEqual(run._wait_boss(fake_bot(), nearest=True), (181, 365))


class RingPollTests(unittest.TestCase):
    def test_rings_are_searched_once_per_second_for_boss_wait_seconds(self):
        naps = []
        bot = SimpleNamespace(sleep=naps.append, screenshot=lambda: None)
        with mock.patch.object(run, "glow_points", lambda screen: []):
            self.assertIsNone(run._wait_boss(bot, nearest=True))
        self.assertEqual(naps, [BOSS_POLL] * round(BOSS_WAIT / BOSS_POLL))
        self.assertEqual(BOSS_POLL, 1)
        self.assertEqual(sum(naps), BOSS_WAIT)       # tổng thời gian chờ vẫn 8 giây như trước


class GlowCenterTests(unittest.TestCase):
    """Ảnh thật (giả lập 21923): Lava Turtle gần giữa màn hình, nhãn nằm dưới thân boss."""

    def test_tap_point_is_mean_x_and_largest_y_of_the_glow(self):
        import os

        import cv2
        from bot.ocr.find_bosses import glow_points
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "lava_turtle_world.png"))
        points = glow_points(shot)
        self.assertEqual(len(points), 1)
        x, y = points[0]
        self.assertLessEqual(abs(x - 192), 3)       # trung bình x các điểm cam sáng
        self.assertLessEqual(abs(y - 376), 3)       # y lớn nhất (đo trên ảnh thật 21923)


class LowOddsTests(unittest.TestCase):
    """Hộp "tỷ lệ thắng cực thấp, vẫn gửi quân?" sau khi bấm March: Cancel và tính boss là đã đánh."""

    def test_template_matches_the_real_box_and_not_the_plain_march_screen(self):
        import os

        import cv2
        from bot.activities.attack_boss.constants import LOW_ODDS, LOW_ODDS_THRESHOLD
        here = os.path.dirname(__file__)
        template = cv2.imread(os.path.join(os.path.dirname(os.path.dirname(here)), "Images", LOW_ODDS))
        score = lambda name: cv2.minMaxLoc(cv2.matchTemplate(cv2.imread(os.path.join(here, "screens", name)), template, cv2.TM_CCOEFF_NORMED))[1]
        self.assertGreaterEqual(score("march_low_odds.png"), LOW_ODDS_THRESHOLD)
        self.assertLess(score("march_screen.png"), LOW_ODDS_THRESHOLD)

    def test_march_cancels_the_box_and_flags_the_boss(self):
        taps = []
        bot = SimpleNamespace(sleep=lambda seconds: None, screenshot=lambda: "shot", log=lambda message: None, record=lambda message: None,
                              tap=lambda *args, **kwargs: taps.append(args))

        def find(template, screen=None, region=None, threshold=0.8, **kwargs):
            if template == run.LOW_ODDS:
                return (198, 337)
            return (200, 670) if template == run.MARCH_BUTTON else None
        bot.find = find
        with (mock.patch.object(run, "_Boss", lambda b, s: SimpleNamespace(troops=[1])),
              mock.patch.object(run, "_pick_troop", lambda *args: 1),
              mock.patch.object(run.lanes, "no_lanes", lambda b, s: False),
              mock.patch.object(boss_scan, "ensure_map", lambda b: None)):
            self.assertFalse(run._march(bot, {}, None))
        self.assertTrue(bot.attack_low_odds)
        self.assertIn((198 + run.LOW_ODDS_CANCEL[0], 337 + run.LOW_ODDS_CANCEL[1]), taps)

    def test_attack_drops_the_boss_when_march_hit_the_box(self):
        bot = fake_bot()

        def march(b, settings, region):
            b.attack_low_odds = True
            return False
        with (mock.patch.object(run, "ensure_world", lambda b: True),
              mock.patch.object(run, "_on_spot", lambda b, offer: True),
              mock.patch.object(run, "_wait_boss", lambda b, nearest=False: (400, 300)),
              mock.patch.object(run, "_tap_attack", lambda b, pos: True),
              mock.patch.object(run, "_wait_popup", lambda b: (None, (100, 100))),
              mock.patch.object(run, "read_popup", lambda screen: None),
              mock.patch.object(run, "_march", march),
              mock.patch.object(run.lanes, "consume_full", lambda b: False)):
            result = run.attack(bot, {"source": "api", "attack_type": "attack"}, BossOffer(556, 66, "Rùa Nham thạch", 1, uid="a"))
        self.assertEqual(result, DROP)
        self.assertFalse(bot.attack_low_odds)       # cờ chỉ dùng một lần


if __name__ == "__main__":
    unittest.main()
