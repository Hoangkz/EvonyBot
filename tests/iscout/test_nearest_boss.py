"""Attack Boss nguồn IsCout: bấm vòng boss gần giữa nhất; không thấy / không ra Attack thì tính là đã đánh (không cần giả lập)."""
import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

from bot.activities.attack_boss.constants import (ATTACK_MENU_POLL, ATTACK_MENU_WAIT, BOSS_NEAR, BOSS_POLL, BOSS_WAIT, DROP, RETAP_AFTER, RETRY,
                                                  RING_MAX_DIST)
from bot.activities.attack_boss.sources import BossOffer
from bot.common import boss_scan

run = importlib.import_module("bot.activities.attack_boss.run")      # `attack_boss.run` là hàm run của package, lấy module qua importlib
CENTER = boss_scan.CAMERA_PX


def fake_bot():
    return SimpleNamespace(sleep=lambda seconds: None, screenshot=lambda: None, log=lambda message: None, tap=lambda *args, **kwargs: None)


def boss_at(dx, dy):
    return {"pos": (CENTER[0] + dx, CENTER[1] + dy)}


class WaitBossTests(unittest.TestCase):
    def test_no_name_in_the_glow_means_boss_not_found_even_if_a_ring_is_seen(self):
        near = (CENTER[0] + 40, CENTER[1] - 30)
        with mock.patch.object(run, "_name_point", lambda screen: None),                 mock.patch.object(run, "glow_points", lambda screen: [near]),                 mock.patch.object(run, "find_bosses", lambda screen: [boss_at(BOSS_NEAR + 150, 0)]):
            self.assertIsNone(run._wait_boss(fake_bot(), nearest=True))      # không dự phòng bằng vòng sáng: không thấy tên = coi như đã đánh
            self.assertIsNone(run._wait_boss(fake_bot()))        # nguồn khác: boss phải gần giữa màn hình

    def test_name_line_is_tapped(self):
        with mock.patch.object(run, "_name_point", lambda screen: (195, 357)), mock.patch.object(run, "glow_points", lambda screen: [(192, 376)]):
            self.assertEqual(run._wait_boss(fake_bot(), nearest=True), (195, 357))      # có dòng tên: bấm trên tên

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

    def test_checks_one_round_only_without_going_back_to_the_first_troop(self):
        tapped = []
        bot = SimpleNamespace(find_all=lambda *args, **kwargs: [], log=lambda message: None, find=lambda *args, **kwargs: None)
        bot.tap_percent = lambda x, y: tapped.append(round((x - run.PRESET_X0) / run.PRESET_DX) + 1)
        helper = SimpleNamespace(troops=[1, 2, 3], _poll_screen=lambda name, fn, **kwargs: (None, fn(None)))
        with mock.patch.object(run, "_preset_active", lambda image, troop: True):
            self.assertIsNone(run._pick_troop(bot, helper, None, None))
        self.assertEqual(tapped, [1, 2, 3])          # đội 1 -> 2 -> 3 rồi dừng, không xoay vòng lần hai

    def test_troop_whose_preset_never_lights_up_is_skipped_once(self):
        tapped = []
        bot = SimpleNamespace(find_all=lambda *args, **kwargs: [], log=lambda message: None, find=lambda *args, **kwargs: (1, 1))
        bot.tap_percent = lambda x, y: tapped.append(round((x - run.PRESET_X0) / run.PRESET_DX) + 1)
        helper = SimpleNamespace(troops=[1, 2], _poll_screen=lambda name, fn, **kwargs: (None, fn(None)))
        with mock.patch.object(run, "_preset_active", lambda image, troop: troop == 2):
            self.assertEqual(run._pick_troop(bot, helper, None, None), 2)
        self.assertEqual(tapped, [1, 2])

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


class NameLineTests(unittest.TestCase):
    """Ảnh thật (giả lập 21923): tên "1 Lava Turtle" bị huy hiệu cấp tách thành hai mảnh hẹp; điểm bấm nằm cao hơn mép trên tên một chút."""

    def test_tap_point_is_middle_of_the_name_and_a_little_above_it(self):
        import os

        import cv2
        from bot.activities.attack_boss.constants import NAME_TAP_ABOVE
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "lava_turtle_world.png"))
        x, y = run._name_point(shot)
        self.assertLessEqual(abs(x - 201), 3)                       # giữa chữ tên (đo trên ảnh thật: x 168-234; huy hiệu cấp vàng bên trái không tính)
        self.assertEqual(y, 361 - NAME_TAP_ABOVE)                   # mép trên dòng tên y = 361, bấm cao hơn NAME_TAP_ABOVE px

    def test_name_stuck_to_the_ring_below_it_is_still_found(self):
        """Ảnh thật (Peryton): chữ "(Boss) Peryton" ở y 361-368 nằm sát vòng sáng cam ngay dưới (y 372-384) và cạnh nhãn quái thường "Murderous Warrior" (y 427-433)."""
        import os

        import cv2
        from bot.activities.attack_boss.constants import NAME_TAP_ABOVE
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "peryton_world.png"))
        x, y = run._name_point(shot)
        self.assertLessEqual(abs(x - 204), 4)                       # giữa chữ (x 162-246), không phải nhãn "Murderous Warrior" (x 67-129)
        self.assertEqual(y, 361 - NAME_TAP_ABOVE)                   # cao hơn mép trên tên 4 px

    def test_griffin_with_other_labels_around_it(self):
        """Ảnh thật (Griffin): quanh có nhãn quái thường "Murderous Warrior", nhãn thành phố, và một boss khác bị cắt ở mép trái (vòng cam ở x 16): chỉ chọn boss gần giữa."""
        import os

        import cv2
        from bot.activities.attack_boss.constants import NAME_TAP_ABOVE
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "griffin_world.png"))
        x, y = run._name_point(shot)
        self.assertLessEqual(abs(x - 204), 4)                       # giữa chữ "(Boss) Gnffin" (x 167-242)
        self.assertEqual(y, 361 - NAME_TAP_ABOVE)

    def test_real_screens(self):
        """Ảnh thật: (tên ảnh, điểm bấm mong đợi). Điểm bấm = giữa chữ tên theo x, mép trên chữ tên - NAME_TAP_ABOVE theo y."""
        import os

        import cv2
        here = os.path.join(os.path.dirname(__file__), "screens")
        cases = [
            ("centaur_world.png", (204, 357)),                          # (Boss) Centaur ở giữa
            ("yasha_world.png", (204, 357)),                            # (Boss) Yasha ở giữa; con cá cam ở (262, 317) là vòng cam xa hơn nên bị bỏ qua
            ("skeleton_dragon_lava_turtle_world.png", (261, 351)),      # hai boss gần nhau, bảng March đang mở: lấy boss có vòng sáng gần tâm nhất (Skeleton Dragon)
        ]
        for name, (x, y) in cases:
            with self.subTest(name):
                shot = cv2.imread(os.path.join(here, name))
                self.assertIsNotNone(shot, name)
                found = run._name_point(shot)
                self.assertIsNotNone(found)
                self.assertLessEqual(abs(found[0] - x), 4)
                self.assertLessEqual(abs(found[1] - y), 2)

    def test_viking_summoned_is_not_an_iscout_boss_so_no_ring_and_no_boss_is_found(self):
        """Viking tự gọi ("Viking(Asking for help)") không phải boss / boss sự kiện của iScout (hub chỉ nhận boss_monster và event_monster) và có luồng riêng:
        trên ảnh thật này bước tìm vòng sáng không ra gì, không có vùng cam, không có điểm bấm, và _wait_boss (nearest) chờ hết BOSS_WAIT giây rồi trả None (không thấy boss)."""
        import os

        import cv2
        from bot.ocr.find_bosses import glow_points, glow_regions
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "viking_asking_for_help_world.png"))
        self.assertEqual(glow_points(shot), [])
        self.assertEqual(glow_regions(shot), [])
        self.assertIsNone(run._name_point(shot))
        naps = []
        bot = SimpleNamespace(sleep=naps.append, screenshot=lambda: shot)
        self.assertIsNone(run._wait_boss(bot, nearest=True))
        self.assertEqual(naps, [BOSS_POLL] * round(BOSS_WAIT / BOSS_POLL))

    def test_orange_ring_pixels_are_not_text(self):
        import os

        import cv2
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "peryton_world.png"))
        _, y = run._name_point(shot)
        self.assertLess(y, 372)                                     # không bấm xuống vùng vòng sáng / dưới tên

    def test_far_glow_is_ignored(self):
        import os

        import cv2
        shot = cv2.imread(os.path.join(os.path.dirname(__file__), "screens", "lava_turtle_world.png"))
        far = (CENTER[0] + RING_MAX_DIST + 60, CENTER[1])         # boss khác ở xa (đo thật 160-190 px)
        with mock.patch.object(run, "glow_points", lambda screen, masked=None: [far]):
            self.assertIsNone(run._name_point(shot))

    def test_no_name_when_there_is_no_glow(self):
        import numpy as np
        self.assertIsNone(run._name_point(np.zeros((704, 396, 3), np.uint8)))


class StaminaTests(unittest.TestCase):
    """Hết thể lực ở màn March: ô Use Stamina được chọn thì dùng vật phẩm y như Join Monster War rồi March lại một lần; không thì bỏ qua boss."""

    def march_with_popup(self, use_stamina, refill_result="ok", popup_forever=False):
        state = {"refilled": False, "refills": 0, "ensure_map": 0}

        def find(template, screen=None, region=None, threshold=0.8, **kwargs):
            if template == run.NOT_ENOUGH_STAMINA:
                return (200, 400) if popup_forever or not state["refilled"] else None
            return (200, 670) if template == run.MARCH_BUTTON else None

        def refill(bot, helper, confirm):
            state["refills"] += 1
            state["refilled"] = True
            return refill_result
        records = []
        bot = SimpleNamespace(sleep=lambda seconds: None, screenshot=lambda: "shot", log=lambda message: None, record=records.append,
                              tap=lambda *args, **kwargs: None, find=find, back=lambda *args, **kwargs: None)
        with (mock.patch.object(run, "_Boss", lambda b, s: SimpleNamespace(troops=[1], use_stamina=use_stamina)),
              mock.patch.object(run, "_pick_troop", lambda *args: 1),
              mock.patch.object(run.lanes, "no_lanes", lambda b, s: False),
              mock.patch.object(run.stamina, "refill", refill),
              mock.patch.object(boss_scan, "on_map", lambda b, shot=None: state["refilled"] and not popup_forever),
              mock.patch.object(boss_scan, "ensure_map", lambda b: state.__setitem__("ensure_map", state["ensure_map"] + 1))):
            result = run._march(bot, {}, None)
        return result, state, records, bot

    def test_stamina_item_is_used_then_march_runs_again(self):
        result, state, _, bot = self.march_with_popup("ALL")
        self.assertTrue(result)
        self.assertFalse(getattr(bot, "attack_no_stamina", False))
        self.assertEqual(state["refills"], 1)

    def test_no_stamina_setting_skips_the_boss_without_using_items(self):
        result, state, records, bot = self.march_with_popup("No")
        self.assertFalse(result)
        self.assertTrue(bot.attack_no_stamina)       # attack trả STAMINA: run bỏ các boss còn lại, tăng tốc, nghỉ
        self.assertEqual(state["refills"], 0)
        self.assertEqual(state["ensure_map"], 1)
        self.assertTrue(any("không dùng vật phẩm" in message for message in records))

    def test_refill_failure_only_skips_the_boss(self):
        result, state, _, bot = self.march_with_popup("100", refill_result="failed")      # lỗi khác (màn không mở / không đóng): chưa phải hết thể lực
        self.assertFalse(result)
        self.assertEqual(state["refills"], 1)
        self.assertEqual(state["ensure_map"], 1)
        self.assertFalse(getattr(bot, "attack_no_stamina", False))

    def test_no_stamina_items_left_flags_out_of_stamina(self):
        result, state, _, bot = self.march_with_popup("ALL", refill_result="empty")
        self.assertFalse(result)
        self.assertTrue(bot.attack_no_stamina)

    def test_items_are_used_only_once_per_march(self):
        result, state, records, bot = self.march_with_popup("ALL", popup_forever=True)       # dùng rồi mà popup vẫn hiện: không lặp vô hạn
        self.assertFalse(result)
        self.assertTrue(bot.attack_no_stamina)
        self.assertEqual(state["refills"], 1)
        self.assertTrue(any("đã dùng vật phẩm mà vẫn thiếu" in message for message in records))


class RefillTests(unittest.TestCase):
    """stamina.refill: Confirm -> vật phẩm đầu tiên -> số lượng -> Use -> Back, theo đúng thứ tự của Join Monster War."""

    def run_refill(self, use_stamina, steps):
        from bot.activities.attack_boss import stamina
        taps, percents, added, records, backs = [], [], [], [], []
        bot = SimpleNamespace(tap=lambda *args, **kwargs: taps.append(args), tap_percent=lambda *args, **kwargs: percents.append(args),
                              record=records.append, back=lambda *args, **kwargs: backs.append(1), sleep=lambda seconds: None)
        helper = SimpleNamespace(use_stamina=use_stamina, _poll_screen=lambda step, predicate, **kwargs: steps[step],
                                 _add_stamina=lambda shot, target: added.append(target))
        with mock.patch.object(stamina, "delay", lambda b, seconds: None):
            result = stamina.refill(bot, helper, (200, 400))
        return result, taps, percents, added, records, backs

    OPEN = {"attack_stamina_items": ("shot", [(290, 360), (290, 480)]), "attack_stamina_amount": ("shot", (281, 502)), "attack_stamina_closed": ("shot", True)}

    def test_all_taps_confirm_first_item_slider_end_and_use(self):
        result, taps, percents, added, _, backs = self.run_refill("ALL", self.OPEN)
        self.assertEqual(result, "ok")
        self.assertEqual(taps, [(200, 400), (290, 360), (281, 502)])      # Confirm, nút Use của vật phẩm trên cùng, nút Use của popup số lượng
        self.assertEqual(len(percents), 1)                                  # thanh trượt kéo tới cuối = dùng hết
        self.assertEqual(added, [])
        self.assertEqual(len(backs), 1)

    def test_multiple_adds_stamina_with_plus_button(self):
        result, _, percents, added, _, _ = self.run_refill("300", self.OPEN)
        self.assertEqual(result, "ok")
        self.assertEqual(added, [300])
        self.assertEqual(percents, [])

    def test_no_items_left_returns_false_and_records(self):
        steps = dict(self.OPEN, attack_stamina_items=("shot", []))
        result, taps, _, _, records, _ = self.run_refill("ALL", steps)
        self.assertEqual(result, "empty")
        self.assertEqual(taps, [(200, 400)])         # chỉ bấm Confirm, không có vật phẩm để Use
        self.assertTrue(any("hết vật phẩm thể lực" in message for message in records))

    def test_popup_that_never_closes_returns_false(self):
        steps = dict(self.OPEN, attack_stamina_closed=("shot", False))
        result, _, _, _, records, backs = self.run_refill("ALL", steps)
        self.assertEqual(result, "failed")
        self.assertGreaterEqual(len(backs), 2)
        self.assertTrue(any("chưa đóng" in message for message in records))


class OutOfStaminaTests(unittest.TestCase):
    """Hết thể lực mà không dùng được: attack trả STAMINA, run bỏ các boss còn lại (KHÔNG tính là đã đánh), tăng tốc (nếu có chọn) rồi nghỉ 20 phút."""

    def attack_result(self, flagged):
        bot = fake_bot()

        def march(b, settings, region):
            b.attack_no_stamina = flagged
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
        return result, bot

    def test_attack_returns_stamina_once_and_clears_the_flag(self):
        result, bot = self.attack_result(True)
        self.assertEqual(result, run.STAMINA)
        self.assertFalse(bot.attack_no_stamina)

    def test_attack_keeps_retry_when_stamina_is_fine(self):
        self.assertEqual(self.attack_result(False)[0], RETRY)

    def test_out_of_stamina_drops_the_list_speeds_up_and_rests_20_minutes(self):
        calls = []
        pending = {(1, 2): "a", (3, 4): "b"}
        source = SimpleNamespace(drop_all=lambda offers: calls.append(("drop_all", sorted(offers))))
        bot = SimpleNamespace(record=lambda message: calls.append("record"))
        with (mock.patch.object(run, "speed_up_if_full", lambda b, settings, troops, force=False: calls.append(("speed", troops, force))),
              mock.patch.object(run, "delay", lambda b, seconds: calls.append(("delay", seconds)))):
            run.out_of_stamina(bot, {}, source, pending, 3)
        self.assertEqual(pending, {})
        self.assertEqual(calls, [("drop_all", ["a", "b"]), "record", ("speed", 3, True), ("delay", 20 * 60)])      # nguồn nhận danh sách boss bị bỏ để quên chúng      # tăng tốc ngay (không đọc số đường), rồi mới nghỉ

    def test_dropped_bosses_are_not_marked_as_attacked(self):
        from bot.activities.attack_boss.sources import ApiSource
        source = ApiSource("a@b.c", "x")
        source.batch = {"a": (1, 2), "b": None, "c": (5, 6)}
        source.done = {"z": 1.0}
        source.drop_all()
        self.assertEqual(source.batch, {})
        self.assertEqual(source.done, {"z": 1.0})            # bỏ khỏi danh sách chưa đánh KHÔNG có nghĩa là đã đánh: boss còn sống được nhận lại sau khi nghỉ

    def test_whisper_forgets_dropped_bosses_so_they_are_found_again_after_the_rest(self):
        from bot.activities.attack_boss.sources import PlayerChatSource
        source = PlayerChatSource("Someone")
        source.crops = {1: ("old", (1, 1)), 2: ("dropped", (2, 2)), 3: ("dropped too", (3, 3))}      # 1: đã đánh xong (giữ ảnh), 2 và 3: chưa đánh
        source.inside = True
        source.drop_all([BossOffer(ident=2), BossOffer(ident=3)])
        self.assertEqual(list(source.crops), [1])             # tin của boss 2, 3 lại là tin "chưa cắt": lần poll sau khi nghỉ nhận lại; boss 1 vẫn không bị đánh trùng
        self.assertFalse(source.inside)

    def test_alliance_chat_source_needs_no_memory_to_find_bosses_again(self):
        from bot.activities.attack_boss.sources import AllianceChatSource
        self.assertFalse(hasattr(AllianceChatSource(), "drop_all"))        # đọc lại chat mỗi lần poll, không nhớ boss nào

    def test_retry_keeps_the_boss_unmarked_and_attacks_it_again(self):
        """Không đội nào có tướng (attack trả RETRY): boss KHÔNG được tính là đã đánh (không finished, không attack_memory), ở lại danh sách chờ và bị đánh lại ở vòng sau."""
        class Done(Exception):
            pass
        boss = BossOffer(1, 1, "a", 1, uid="a")
        results, finished, polls, marked = iter([run.RETRY, run.MARCHED]), [], [], []

        def poll(b):
            polls.append(1)
            if len(polls) >= 3:
                raise Done()
            return [boss] if len(polls) == 1 else []

        attacked = []

        def attack(b, settings, offer, go=None, own=None, latest=None):
            attacked.append(offer.uid)
            if len(attacked) == 1:
                self.assertIsNone(b.attack_memory.status((1, 1)))       # sau lần RETRY đầu vẫn chưa tính là đã đánh
            return next(results)
        source = SimpleNamespace(poll=poll, drop_all=lambda dropped: None, finished=finished.append)
        bot = SimpleNamespace(attack_memory=None, screenshot=lambda: None, log=lambda message: None, record=lambda message: None, sleep=lambda seconds: None)
        with (mock.patch.object(run, "make_source", lambda settings: source),
              mock.patch.object(run, "eggs_due", lambda b, hours: False),
              mock.patch.object(run.viking, "summon_due", lambda b, settings, screen: False),
              mock.patch.object(run, "ensure_world", lambda b: True),
              mock.patch.object(run, "home_coords", lambda b: None),
              mock.patch.object(run, "attack", attack),
              mock.patch.object(run, "speed_up_if_full", lambda *args, **kwargs: None)):
            with self.assertRaises(Done):
                run.run(bot, {"source": "api"})
        self.assertEqual(attacked, ["a", "a"])                          # cùng một boss được đánh lại
        self.assertEqual([offer.uid for offer in finished], ["a"])      # chỉ xong (finished) sau lần hành quân thành công, không phải sau lần RETRY

    def test_run_stops_attacking_the_rest_of_the_list_without_marking_them(self):
        class Rest(Exception):
            pass
        attacked, rested, finished = [], [], []
        offers = [BossOffer(1, 1, "a", 1, uid="a"), BossOffer(2, 2, "b", 1, uid="b"), BossOffer(3, 3, "c", 1, uid="c")]
        source = SimpleNamespace(poll=lambda b: offers, drop_all=lambda dropped: None, finished=finished.append)

        def attack(b, settings, offer, go=None, own=None, latest=None):
            attacked.append(offer.uid)
            return run.STAMINA if offer.uid == "b" else run.MARCHED

        def out_of_stamina(b, settings, src, pending, troops):
            rested.append(sorted(pending))
            raise Rest()
        bot = SimpleNamespace(attack_memory=None, screenshot=lambda: None, log=lambda message: None, record=lambda message: None, sleep=lambda seconds: None)
        with (mock.patch.object(run, "make_source", lambda settings: source),
              mock.patch.object(run, "eggs_due", lambda b, hours: False),
              mock.patch.object(run.viking, "summon_due", lambda b, settings, screen: False),
              mock.patch.object(run, "ensure_world", lambda b: True),
              mock.patch.object(run, "home_coords", lambda b: None),
              mock.patch.object(run, "attack", attack),
              mock.patch.object(run, "speed_up_if_full", lambda *args, **kwargs: None),
              mock.patch.object(run, "out_of_stamina", out_of_stamina)):
            with self.assertRaises(Rest):
                run.run(bot, {"source": "api"})
        self.assertEqual(attacked, ["a", "b"])           # boss c chưa đánh: không đánh sau khi hết thể lực
        self.assertEqual(rested, [[(2, 2), (3, 3)]])     # lúc nghỉ b và c còn trong danh sách chờ (out_of_stamina xoá)
        self.assertEqual([offer.uid for offer in finished], ["a"])      # chỉ boss a (đã hành quân) là xong; b và c không bị tính là đã đánh
        self.assertIsNone(bot.attack_memory.status((2, 2)))
        self.assertIsNone(bot.attack_memory.status((3, 3)))


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

    def test_no_troop_with_general_backs_out_to_a_clean_map(self):
        backs, cleaned = [], []
        bot = SimpleNamespace(sleep=lambda seconds: None, screenshot=lambda: "shot", log=lambda message: None, record=lambda message: None,
                              tap=lambda *args, **kwargs: None, back=lambda *args, **kwargs: backs.append(1),
                              find=lambda template, **kwargs: (200, 670) if template == run.MARCH_BUTTON else None)
        with (mock.patch.object(run, "_Boss", lambda b, s: SimpleNamespace(troops=[1, 2, 3])),
              mock.patch.object(run, "_pick_troop", lambda *args: None),
              mock.patch.object(boss_scan, "ensure_map", cleaned.append)):
            self.assertFalse(run._march(bot, {}, None))
        self.assertEqual(len(backs), 1)          # Back một lần
        self.assertEqual(len(cleaned), 1)        # rồi về bản đồ sạch

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
