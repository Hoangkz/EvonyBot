"""Các nhánh an toàn hiếm gặp của Join Monster War không cần ảnh màn hình riêng."""

import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

from pathlib import Path

import cv2
import numpy as np

from bot.activities.join_monster_war.boss_memory import BossMemory, JOINED
from bot.activities.join_monster_war.constants import (
    BOSS_MONSTER,
    FAVORITE_OFF,
    FAVORITE_ON,
    GENERAL_SEARCH,
    JOINED_BUTTON,
    LOCATION,
    MAIN_GENERAL,
    MARCH,
    SELECT_GENERAL,
    STAMINA_ITEM_USE,
    STAMINA_USE,
    WAR_TICKED,
    WAR_UNTICK_TRIES,
)
from bot.activities.join_monster_war.run import (MAX_MAP_COORD, POLL_INTERVAL, STEP_TIMEOUT,
                                                 _Boss, _near, _troops)


run_module = importlib.import_module("bot.activities.join_monster_war.run")
SCREEN = np.zeros((704, 396, 3), dtype=np.uint8)
SCREENS = Path(__file__).parent / "screens"


def fake_bot():
    return SimpleNamespace(
        boss_memory=BossMemory(),
        find=mock.Mock(return_value=None),
        find_all=mock.Mock(return_value=[]),
        screenshot=mock.Mock(return_value=SCREEN),
        crop=mock.Mock(return_value=SCREEN),
        template_size=mock.Mock(return_value=(10, 10)),
        tap=mock.Mock(),
        tap_percent=mock.Mock(),
        back=mock.Mock(),
        log=mock.Mock(),
        record=mock.Mock(),
        report_boss=mock.Mock(),
    )


class JoinBossEdgeCaseTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(run_module, "delay", lambda *_args, **_kwargs: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_troop_config_ignores_bad_values_sorts_and_deduplicates(self):
        self.assertEqual(_troops(["Troop 3", "bad", "Troop 1", "Troop 3", None]), [1, 3])
        self.assertEqual(_troops("Troop 7"), [7])
        self.assertEqual(_troops(None), [1])

    def test_near_uses_strict_same_spot_boundary(self):
        self.assertTrue(_near((108, 108), [(100, 100)]))
        self.assertFalse(_near((110, 100), [(100, 100)]))

    def test_non_boss_march_screen_backs_out_without_marking_joined(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: None if template == BOSS_MONSTER else None
        boss = _Boss(bot, {"troop": ["Troop 1"]})

        boss._march(SCREEN, (300, 680))

        bot.back.assert_called_once()
        self.assertIsNone(boss.memory.status((500, 600)))

    def test_press_march_does_nothing_when_button_is_missing(self):
        bot = fake_bot()
        boss = _Boss(bot, {})

        boss._press_march((500, 600), screen=SCREEN)

        bot.tap.assert_not_called()
        bot.back.assert_not_called()
        self.assertIsNone(boss.memory.status((500, 600)))

    def test_press_march_still_visible_backs_out_without_marking_joined(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (300, 680) if template == MARCH else None
        boss = _Boss(bot, {})

        boss._press_march((500, 600), screen=SCREEN)

        bot.tap.assert_called_once()
        bot.back.assert_called_once()
        self.assertEqual(bot.screenshot.call_count, int(STEP_TIMEOUT / POLL_INTERVAL))
        self.assertIsNone(boss.memory.status((500, 600)))

    def test_closed_march_without_war_list_is_not_remembered(self):
        bot = fake_bot()

        def find(template, **kwargs):
            if template == MARCH:
                return (300, 680) if "screen" not in kwargs else None
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})

        boss._press_march((500, 600), (300, 680), SCREEN)

        bot.back.assert_not_called()
        self.assertIsNone(boss.memory.status((500, 600)))
        self.assertIn("chưa quay lại danh sách War", bot.record.call_args.args[0])

    def test_returning_to_war_list_marks_joined_after_coordinate_confirmation(self):
        bot = fake_bot()

        def find(template, **kwargs):
            if template == MARCH:
                return (300, 680) if "screen" not in kwargs else None
            if template == run_module.PVP_WAR:
                return (200, 118)
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})
        boss._joined_target_visible = mock.Mock(return_value=True)

        boss._press_march((500, 600), (300, 680), SCREEN)

        self.assertEqual(boss.memory.status((500, 600)), JOINED)
        boss._joined_target_visible.assert_called_with(SCREEN, (500, 600))
        self.assertIn("đã hành quân tới boss", bot.record.call_args.args[0])

    def test_stamina_popup_does_not_mark_joined_or_check_war_list(self):
        bot = fake_bot()

        def find(template, **kwargs):
            if template == MARCH:
                return (300, 680)
            if template == run_module.NOT_ENOUGH_STAMINA:
                return (200, 400)
            if template == run_module.PVP_WAR:
                raise AssertionError("popup thể lực phải được xử lý trước danh sách War")
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})

        boss._press_march((500, 600), (300, 680), SCREEN)

        self.assertIsNone(boss.memory.status((500, 600)))

    def test_join_tracks_same_boss_when_new_rally_moves_its_card(self):
        initial = np.zeros((704, 396, 3), dtype=np.uint8)
        fresh = np.ones((704, 396, 3), dtype=np.uint8)
        bot = fake_bot()
        bot.screenshot.return_value = fresh

        def find_all(template, **kwargs):
            screen = kwargs.get("screen")
            if template == JOINED_BUTTON:
                return []
            if template != run_module.JOIN:
                return []
            if screen is initial:
                return [(319, 300)]
            # Một rally mới chiếm vị trí cũ; boss mục tiêu đã bị đẩy xuống.
            return [(319, 300), (319, 420)]

        bot.find_all.side_effect = find_all
        boss = _Boss(bot, {})
        boss._boss_is_wanted = mock.Mock(return_value=True)
        boss._join_text_is_red = mock.Mock(return_value=False)

        def read_card_coords(screen, _x, y):
            if screen is initial:
                return (500, 600)
            return (111, 222) if y == 300 else (500, 600)

        boss._read_card_coords = mock.Mock(side_effect=read_card_coords)

        self.assertTrue(boss._join(initial))
        bot.tap.assert_called_once_with(324, 425)
        bot.report_boss.assert_called_once_with((500, 600))

    def test_join_aborts_when_target_disappears_before_tap(self):
        initial = np.zeros((704, 396, 3), dtype=np.uint8)
        fresh = np.ones((704, 396, 3), dtype=np.uint8)
        bot = fake_bot()
        bot.screenshot.return_value = fresh

        def find_all(template, **kwargs):
            screen = kwargs.get("screen")
            if template == JOINED_BUTTON:
                return []
            if template != run_module.JOIN:
                return []
            if screen is initial:
                return [(319, 300)]
            return [(319, 420)]

        bot.find_all.side_effect = find_all
        boss = _Boss(bot, {})
        boss._boss_is_wanted = mock.Mock(return_value=True)
        boss._join_text_is_red = mock.Mock(return_value=False)
        boss._read_card_coords = mock.Mock(
            side_effect=lambda screen, _x, _y: (500, 600) if screen is initial else (111, 222)
        )

        self.assertFalse(boss._join(initial))
        bot.tap.assert_not_called()
        bot.report_boss.assert_not_called()
        self.assertIs(boss.next_screen, fresh)
        self.assertIn("danh sách đã đổi", bot.log.call_args.args[0])

    def test_unreadable_card_coordinates_are_blacklisted_for_current_screen(self):
        bot = fake_bot()
        bot.find_all.side_effect = lambda template, **_kwargs: ([(319, 300)]
                                                                 if template == run_module.JOIN else [])
        boss = _Boss(bot, {})
        boss._read_card_coords = mock.Mock(return_value=None)

        # Mock để test không ghi ảnh thật vào logs/images của app.
        with mock.patch.object(run_module.boss_names, "log_march_coords_fail") as saved:
            self.assertFalse(boss._join(SCREEN))

        saved.assert_called_once_with(SCREEN, "list", "319_300")   # lưu ảnh tọa độ OCR lỗi
        self.assertEqual(boss.screen_blacklist, [(319, 300)])
        bot.tap.assert_not_called()
        bot.report_boss.assert_not_called()
        self.assertIn("Không đọc được tọa độ card", bot.log.call_args.args[0])

    def test_march_uses_actual_target_instead_of_list_target(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: ((200, 250) if template == BOSS_MONSTER
                                                            else (300, 680) if template == MARCH else None)
        boss = _Boss(bot, {})
        boss._read_march_target_coords = mock.Mock(return_value=(111, 222))
        boss._pick_troop = mock.Mock(return_value=1)
        boss._press_march = mock.Mock()

        boss._march(SCREEN, (300, 680))

        boss._press_march.assert_called_once_with((111, 222), (300, 680), SCREEN)
        bot.back.assert_not_called()

    def test_march_without_readable_target_backs_out(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: ((200, 250) if template == BOSS_MONSTER
                                                            else (300, 680) if template == MARCH else None)
        boss = _Boss(bot, {})
        boss._read_march_target_coords = mock.Mock(return_value=None)
        boss.card_label = "767_811_Cerberus_lv3_234.2M"

        # Mock để test không ghi ảnh thật vào logs/images của app.
        with mock.patch.object(run_module.boss_names, "log_march_coords_fail") as saved:
            boss._march(SCREEN, (300, 680))

        bot.back.assert_called_once()
        bot.tap.assert_not_called()
        self.assertIn("không đọc được tọa độ đích", bot.record.call_args.args[0])
        saved.assert_called_once_with(SCREEN, "march", "767_811_Cerberus_lv3_234.2M")

    def test_march_target_uses_right_side_location(self):
        bot = fake_bot()
        bot.find_all.return_value = [(31, 266), (274, 266)]
        bot.template_size.return_value = (14, 14)
        boss = _Boss(bot, {})

        with mock.patch.object(run_module, "_coords_after_server", return_value=(767, 811)):
            self.assertEqual(boss._read_march_target_coords(SCREEN), (767, 811))

        bot.crop.assert_called_once_with(SCREEN, 288, 266, 140, 18)

    def test_pvp_war_without_matching_joined_row_is_not_remembered(self):
        bot = fake_bot()

        def find(template, **_kwargs):
            if template == MARCH:
                return (300, 680)
            if template == run_module.PVP_WAR:
                return (200, 118)
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})
        boss._joined_target_visible = mock.Mock(return_value=False)

        boss._press_march((500, 600), (300, 680), SCREEN)

        self.assertIsNone(boss.memory.status((500, 600)))
        bot.back.assert_not_called()
        self.assertIn("chưa thấy Joined đúng boss", bot.record.call_args.args[0])

    def test_invalid_ocr_coordinates_are_rejected_and_logged(self):
        bot = fake_bot()
        bot.find.return_value = (2, 3)
        boss = _Boss(bot, {})

        with mock.patch.object(run_module, "read_coords", return_value=(MAX_MAP_COORD + 1, -1)):
            self.assertIsNone(boss._read_card_coords(SCREEN, 319, 331))

        self.assertIn("Bỏ tọa độ OCR không hợp lệ", bot.log.call_args.args[0])

    def test_missing_stamina_quantity_popup_does_not_remember_boss(self):
        bot = fake_bot()
        bot.find_all.return_value = [(290, 360)]
        bot.find.return_value = None
        boss = _Boss(bot, {"use_stamina": "100"})
        boss._use_stamina()

        bot.tap.assert_called_once_with(290, 360)
        bot.back.assert_called_once()
        self.assertIsNone(boss.memory.status((500, 600)))

    def test_war_checkbox_retry_limit_prevents_endless_tapping(self):
        bot = fake_bot()
        bot.find.return_value = (200, 118)
        boss = _Boss(bot, {})
        boss.war_taps = WAR_UNTICK_TRIES

        self.assertFalse(boss._untick_war(SCREEN))
        bot.find.assert_not_called()
        bot.tap.assert_not_called()

    def test_general_picker_failure_returns_false_without_marching(self):
        bot = fake_bot()

        def find(template, **_kwargs):
            if template == SELECT_GENERAL:
                return (65, 390)
            if template in (FAVORITE_ON, FAVORITE_OFF, GENERAL_SEARCH):
                return None
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {"select_general": True})

        self.assertFalse(boss._choose_general(MAIN_GENERAL))
        self.assertEqual(bot.screenshot.call_count, int(STEP_TIMEOUT / POLL_INTERVAL))
        self.assertIn("không mở được màn Select a General", bot.record.call_args.args[0])
        self.assertIsNone(boss.memory.status((500, 600)))

    def test_joined_memory_is_written_after_returning_to_war_list(self):
        bot = fake_bot()

        def find(template, **kwargs):
            if template == MARCH:
                return (300, 680) if "screen" not in kwargs else None
            if template == run_module.PVP_WAR:
                return (200, 118)
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})
        boss._joined_target_visible = mock.Mock(return_value=True)

        boss._press_march((500, 600), (300, 680), SCREEN)

        self.assertEqual(boss.memory.status((500, 600)), JOINED)
        self.assertIn("đã hành quân tới boss", bot.record.call_args.args[0])

    def test_power_below_war_row_is_read_without_scrolling(self):
        bot = fake_bot()
        bot.swipe_percent = mock.Mock()
        boss = _Boss(bot, {})

        with mock.patch.object(run_module, "read_power_text", return_value="85.6m"):
            self.assertEqual(boss._read_power(SCREEN, 319, 331, (1, 2)), "85.6m")   # lực ở y=151

        bot.swipe_percent.assert_not_called()
        self.assertFalse(boss.layout_changed)

    def test_power_hidden_under_war_row_scrolls_a_little_then_reads(self):
        bot = fake_bot()
        bot.swipe_percent = mock.Mock()
        boss = _Boss(bot, {})
        boss._find_card = mock.Mock(return_value=(319, 340))   # thẻ đã dịch xuống sau khi cuộn

        with mock.patch.object(run_module, "read_power_text", return_value="85.6m"):
            # Join ở y=290 -> thanh lực y=110, nằm trong hàng War (đáy 116 + 22 = 138).
            self.assertEqual(boss._read_power(SCREEN, 319, 290, (1, 2)), "85.6m")

        bot.swipe_percent.assert_called_once()
        self.assertTrue(boss.layout_changed)            # ảnh cũ không dùng được nữa
        self.assertIs(boss.next_screen, SCREEN)
        boss._find_card.assert_called_once_with(SCREEN, (1, 2), 290 + 48)

    def test_power_still_hidden_after_scroll_gives_no_power(self):
        bot = fake_bot()
        bot.swipe_percent = mock.Mock()
        boss = _Boss(bot, {})
        boss._find_card = mock.Mock(return_value=(319, 290))   # không dịch được (đã ở đầu danh sách)

        with mock.patch.object(run_module, "read_power_text") as read:
            self.assertIsNone(boss._read_power(SCREEN, 319, 290, (1, 2)))

        read.assert_not_called()

    def test_war_row_position_found_at_untick_moves_the_visible_limit(self):
        boss = _Boss(fake_bot(), {})
        self.assertEqual(boss._list_top(), 116 + 22)
        boss.war_y = 120
        self.assertEqual(boss._list_top(), 120 + 22)

    def test_unticked_monster_war_box_is_ticked(self):
        bot = fake_bot()          # find luôn None: không thấy dấu tích ở ô Monster War
        boss = _Boss(bot, {})
        boss._poll_screen = mock.Mock(return_value=(SCREEN, True))

        self.assertTrue(boss._tick_monster_war(SCREEN))

        bot.tap.assert_called_once_with(*run_module.MONSTER_WAR_TAP)
        self.assertIs(boss.next_screen, SCREEN)

    def test_ticked_monster_war_box_is_left_alone(self):
        bot = fake_bot()
        bot.find.return_value = (49, 118)
        boss = _Boss(bot, {})

        self.assertFalse(boss._tick_monster_war(SCREEN))

        bot.tap.assert_not_called()

    def test_monster_war_box_is_tapped_at_most_a_few_times(self):
        bot = fake_bot()
        boss = _Boss(bot, {})
        boss._poll_screen = mock.Mock(return_value=(SCREEN, False))

        taps = [boss._tick_monster_war(SCREEN) for _ in range(run_module.MONSTER_TICK_TRIES + 2)]

        self.assertEqual(taps, [True] * run_module.MONSTER_TICK_TRIES + [False] * 2)

    def test_preset_ring_marks_only_the_selected_troop(self):
        # Ảnh thật: ô I có vòng sáng cam, ô II-IV mở nhưng không chọn, V-VIII khoá.
        for name, selected in (("march_no_main_general.png", 1), ("march_ready.png", 2)):
            screen = cv2.imread(str(SCREENS / name))
            self.assertEqual([t for t in range(1, 9) if run_module._preset_active(screen, t)],
                             [selected], name)

    def test_stamina_item_type_is_the_best_matching_icon(self):
        # 10 và 25 cùng khung xanh lá (khớp chéo 0,951): phải lấy mẫu khớp cao nhất.
        from threading import Event
        from bot.context import BotContext
        ctx = BotContext(SimpleNamespace(serial="x"), Event(), None, lambda _: None)
        for amount in (10, 25, 50, 100):
            screen = cv2.imread(str(SCREENS / f"stamina_popup_item_{amount}.png"))
            self.assertEqual(run_module._item_stamina(ctx, screen), amount)
        self.assertIsNone(run_module._item_stamina(ctx, cv2.imread(str(SCREENS / "stamina_use_item_list.png"))))

    def test_locked_presets_are_all_counted(self):
        # Ổ khoá khớp chỉ 0,877-0,9 ở vài ô: ngưỡng mặc định 0,9 đếm thiếu (3 thay vì 4, 5 thay vì 6).
        from threading import Event
        from bot.context import BotContext
        ctx = BotContext(SimpleNamespace(serial="x"), Event(), None, lambda _: None)
        for name, locked in (("new_join_boss_flow/07_march_before_action.png", 4),
                             ("march_not_enough_stamina.png", 6)):
            screen = cv2.imread(str(SCREENS / name))
            found = ctx.find_all(run_module.PRESET_LOCKED, threshold=run_module.PRESET_LOCKED_THRESHOLD,
                                 screen=screen, region=run_module.REGIONS[run_module.PRESET_LOCKED])
            self.assertEqual(len(found), locked, name)

    def test_troop_is_judged_only_after_its_preset_lights_up(self):
        # Đội 1 bấm mà không sáng (game chưa đổi đội): không xét kính lúp của đội cũ, thử đội 2.
        bot = fake_bot()
        boss = _Boss(bot, {"troop": ["Troop 1", "Troop 2"]})
        results = iter([(SCREEN, False), (SCREEN, True), (SCREEN, (348, 388))])
        boss._poll_screen = mock.Mock(side_effect=lambda *_a, **_k: next(results))

        self.assertEqual(boss._pick_troop(SCREEN), 2)
        steps = [c.args[0] for c in boss._poll_screen.call_args_list]
        self.assertEqual(steps, ["activate_troop_1", "activate_troop_2", "select_troop_2"])
        self.assertEqual(boss._poll_screen.call_args_list[0].kwargs,
                         {"timeout": run_module.PRESET_ACTIVE_WAIT, "interval": 1})

    def test_no_preset_lights_up_leaves_no_troop_to_march_with(self):
        bot = fake_bot()
        boss = _Boss(bot, {"troop": ["Troop 1", "Troop 2"]})
        boss._poll_screen = mock.Mock(return_value=(SCREEN, False))

        self.assertIsNone(boss._pick_troop(SCREEN))
        self.assertIsNone(boss.last_troop)   # _march sẽ Back, không March


if __name__ == "__main__":
    unittest.main()
