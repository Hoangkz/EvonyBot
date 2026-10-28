"""Attack Boss nguồn IsCout: bấm vòng boss gần giữa nhất; không thấy / không ra Attack thì tính là đã đánh (không cần giả lập)."""
import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

from bot.activities.attack_boss.constants import (ATTACK_MENU_POLL, ATTACK_MENU_WAIT, BOSS_NEAR, BOSS_POLL, BOSS_WAIT, DROP, RETAP_AFTER, RETRY,
                                                  RING_BELOW, RING_MAX_DIST, TAP_MAX_Y)
from bot.activities.attack_boss.sources import BossOffer
from bot.common import boss_scan

run = importlib.import_module("bot.activities.attack_boss.run")      # `attack_boss.run` là hàm run của package, lấy module qua importlib
CENTER = boss_scan.CAMERA_PX


def fake_bot():
    return SimpleNamespace(sleep=lambda seconds: None, screenshot=lambda: None, log=lambda message: None, tap=lambda *args, **kwargs: None)


def boss_at(dx, dy):
    return {"pos": (CENTER[0] + dx, CENTER[1] + dy)}


class WaitBossTests(unittest.TestCase):
    def test_nearest_ring_within_reach_is_tapped_and_far_rings_are_ignored(self):
        near = (CENTER[0] + 40, CENTER[1] - 30)
        far = (CENTER[0] + RING_MAX_DIST + 60, CENTER[1])         # boss khác ở xa (đo thật 160-190 px)
        with mock.patch.object(run, "_name_point", lambda screen: None), \
                mock.patch.object(run, "glow_points", lambda screen: [far, near]), \
                mock.patch.object(run, "find_bosses", lambda screen: [boss_at(BOSS_NEAR + 150, 0)]):
            self.assertEqual(run._wait_boss(fake_bot(), nearest=True), (near[0], near[1] + RING_BELOW))      # điểm đo là đáy vòng sáng: bấm thấp hơn RING_BELOW
            self.assertIsNone(run._wait_boss(fake_bot()))        # nguồn khác: boss phải gần giữa màn hình
        with mock.patch.object(run, "_name_point", lambda screen: None), mock.patch.object(run, "glow_points", lambda screen: [far]):
            self.assertIsNone(run._wait_boss(fake_bot(), nearest=True))      # chỉ có boss khác: coi như không thấy boss đích

    def test_name_line_is_tapped_before_the_ring(self):
        with mock.patch.object(run, "_name_point", lambda screen: (195, 357)), mock.patch.object(run, "glow_points", lambda screen: [(192, 376)]):
            self.assertEqual(run._wait_boss(fake_bot(), nearest=True), (195, 357))      # có dòng tên: bấm trên tên, không bấm theo vòng sáng

    def test_default_taps_the_center_when_boss_is_near(self):
        with mock.patch.object(run, "find_bosses", lambda screen: [boss_at(10, 10)]):
            self.assertEqual(run._wait_boss(fake_bot()), CENTER)

    def test_no_ring_at_all_returns_none(self):
        with mock.patch.object(run, "_name_point", lambda screen: None), mock.patch.object(run, "glow_points", lambda screen: []):
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
              mock.patch.object(run, "_tap_attack", lambda bot, pos, relocate=None: False),
              mock.patch.object(boss_scan, "tap_menu_item", lambda bot, pos, icon: False)):
            return run.attack(fake_bot(), {"source": source}, BossOffer(556, 66, "Rùa Nham thạch", 1, uid="a"))

    def test_iscout_boss_without_attack_menu_counts_as_attacked(self):
        self.assertEqual(self.attack_with_no_attack_menu("api"), DROP)

    def test_other_sources_still_retry_without_attack_menu(self):
        self.assertEqual(self.attack_with_no_attack_menu("alliance_chat"), RETRY)


class LatestCoordsTests(unittest.TestCase):
    """Toạ độ mới nhất của boss ngay trước khi tới."""

    def attack(self, latest, spots):
        gone = []
        with (mock.patch.object(run, "ensure_world", lambda bot: True),
              mock.patch.object(run, "_on_spot", lambda bot, offer: spots.append(offer.coords) or True),
              mock.patch.object(run, "_wait_boss", lambda bot, nearest=False: None),
              mock.patch.object(boss_scan, "ensure_map", lambda bot: gone.append(1))):
            return run.attack(fake_bot(), {"source": "api"}, BossOffer(556, 66, "Rùa Nham thạch", 1, uid="a"), latest=latest), gone

    def test_goes_to_the_current_coords_not_the_ones_received_earlier(self):
        spots = []
        result, _ = self.attack(lambda bot, offer: BossOffer(570, 80, "Rùa Nham thạch", 1, uid="a"), spots)
        self.assertEqual(spots, [(570, 80)])
        self.assertEqual(result, DROP)           # (ở đây không thấy vòng màu: bỏ) nhưng đã đi tới toạ độ mới

    def test_boss_that_is_gone_is_dropped_without_travelling(self):
        spots = []
        result, _ = self.attack(lambda bot, offer: None, spots)
        self.assertEqual(result, DROP)
        self.assertEqual(spots, [])              # không đi tới toạ độ nào


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


class RetapTests(unittest.TestCase):
    """Boss đang di chuyển: chưa thấy menu thì tìm lại vòng màu và bấm vào chỗ mới."""

    def run_tap(self, relocate, menu_on_poll=None):
        taps, polls = [], [0]
        bot = SimpleNamespace(sleep=lambda seconds: None, tap=lambda *args, **kwargs: taps.append(args), log=lambda message: None)
        bot.screenshot = lambda: polls.__setitem__(0, polls[0] + 1) or polls[0]
        find = lambda b, screen, icon: (150, 250) if menu_on_poll is not None and screen >= menu_on_poll else None
        with mock.patch.object(boss_scan, "find_menu_item", find), mock.patch.object(boss_scan, "ensure_map", lambda b: None):
            return run._tap_attack(bot, (190, 340), relocate=relocate), taps

    def test_taps_again_where_the_boss_moved_to(self):
        opened, taps = self.run_tap(lambda screen: (230, 330), menu_on_poll=4)
        self.assertTrue(opened)
        self.assertEqual(taps[0], (190, 340))
        self.assertIn((230, 330), taps)                        # bấm lại chỗ mới
        self.assertEqual(taps[-1], (150, 250))                 # rồi bấm nút Attack

    def test_does_not_retap_the_same_place_while_waiting_for_a_slow_menu(self):
        opened, taps = self.run_tap(lambda screen: (192, 342), menu_on_poll=5)      # lệch < RETAP_MOVE: boss đứng yên, chỉ do lag
        self.assertTrue(opened)
        self.assertEqual(taps, [(190, 340), (150, 250)])

    def test_waits_RETAP_AFTER_polls_before_looking_again(self):
        calls = []
        self.run_tap(lambda screen: calls.append(screen) or None, menu_on_poll=None)
        self.assertEqual(calls[0], RETAP_AFTER)


class RingPollTests(unittest.TestCase):
    def test_rings_are_searched_once_per_second_for_boss_wait_seconds(self):
        naps = []
        bot = SimpleNamespace(sleep=naps.append, screenshot=lambda: None)
        with mock.patch.object(run, "_name_point", lambda screen: None), mock.patch.object(run, "glow_points", lambda screen: []):
            self.assertIsNone(run._wait_boss(bot, nearest=True))
        self.assertEqual(naps, [BOSS_POLL] * round(BOSS_WAIT / BOSS_POLL))
        self.assertEqual(BOSS_POLL, 1)
        self.assertEqual(sum(naps), BOSS_WAIT)       # tổng thời gian chờ vẫn 8 giây như trước


class GlowCenterTests(unittest.TestCase):
    """Ảnh thật (giả lập 21923): Lava Turtle gần giữa màn hình, nhãn nằm dưới thân boss."""

    def test_glow_point_is_mean_x_and_bottom_of_the_glow(self):
        import os

        import cv2
        from bot.ocr.find_bosses import glow_points
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "lava_turtle_world.png"))
        points = glow_points(shot)
        self.assertEqual(len(points), 1)
        x, y = points[0]
        self.assertLessEqual(abs(x - 192), 3)       # trung bình x các điểm cam sáng (đo trên ảnh thật 21923)
        self.assertLessEqual(abs(y - 376), 3)       # đáy vòng sáng (y lớn nhất)
        self.assertEqual(TAP_MAX_Y, 352)
        self.assertEqual(run._ring_point(shot), (x, min(y + RING_BELOW, TAP_MAX_Y)))      # điểm bấm thật: đáy + 10, tối đa TAP_MAX_Y (352)


class NameLineTests(unittest.TestCase):
    """Ảnh thật (giả lập 21923): tên "1 Lava Turtle" bị huy hiệu cấp tách thành hai mảnh hẹp; điểm bấm nằm cao hơn mép trên tên một chút."""

    def test_tap_point_is_middle_of_the_name_and_a_little_above_it(self):
        import os

        import cv2
        from bot.activities.attack_boss.constants import NAME_TAP_ABOVE
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "lava_turtle_world.png"))
        x, y = run._name_point(shot)
        self.assertLessEqual(abs(x - 195), 3)                       # giữa dòng tên (đo trên ảnh thật: x 156-234)
        self.assertEqual(y, 361 - NAME_TAP_ABOVE)                   # mép trên dòng tên y = 361, bấm cao hơn NAME_TAP_ABOVE px

    def test_no_name_when_there_is_no_glow(self):
        import numpy as np
        self.assertIsNone(run._name_point(np.zeros((704, 396, 3), np.uint8)))


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
              mock.patch.object(run, "_tap_attack", lambda b, pos, relocate=None: True),
              mock.patch.object(run, "_wait_popup", lambda b: (None, (100, 100))),
              mock.patch.object(run, "read_popup", lambda screen: None),
              mock.patch.object(run, "_march", march),
              mock.patch.object(run.lanes, "consume_full", lambda b: False)):
            result = run.attack(bot, {"source": "api", "attack_type": "attack"}, BossOffer(556, 66, "Rùa Nham thạch", 1, uid="a"))
        self.assertEqual(result, DROP)
        self.assertFalse(bot.attack_low_odds)       # cờ chỉ dùng một lần


if __name__ == "__main__":
    unittest.main()
