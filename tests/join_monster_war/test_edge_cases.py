"""Các nhánh an toàn hiếm gặp của Join Monster War không cần ảnh màn hình riêng."""

import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

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
from bot.activities.join_monster_war.run import MAX_MAP_COORD, _Boss, _near, _troops


run_module = importlib.import_module("bot.activities.join_monster_war.run")
SCREEN = np.zeros((704, 396, 3), dtype=np.uint8)


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

    def test_wrong_march_target_backs_out_without_marking_joined(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: None if template == BOSS_MONSTER else None
        boss = _Boss(bot, {"troop": ["Troop 1"]})
        boss.pending = (500, 600)

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
        boss._march_target_matches = mock.Mock(return_value=True)

        boss._press_march((500, 600), screen=SCREEN)

        bot.tap.assert_called_once()
        bot.back.assert_called_once()
        self.assertEqual(bot.screenshot.call_count, 5)
        self.assertIsNone(boss.memory.status((500, 600)))

    def test_closed_march_without_war_list_is_not_remembered(self):
        bot = fake_bot()

        def find(template, **kwargs):
            if template == MARCH:
                return (300, 680) if "screen" not in kwargs else None
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})
        boss._march_target_matches = mock.Mock(return_value=True)

        boss._press_march((500, 600), (300, 680), SCREEN)

        bot.back.assert_not_called()
        self.assertIsNone(boss.memory.status((500, 600)))
        self.assertIn("chưa quay lại danh sách War", bot.record.call_args.args[0])

    def test_returning_to_war_list_marks_joined_without_ocr(self):
        bot = fake_bot()

        def find(template, **kwargs):
            if template == MARCH:
                return (300, 680) if "screen" not in kwargs else None
            if template == run_module.PVP_WAR:
                return (200, 118)
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})
        boss._read_card_coords = mock.Mock(side_effect=AssertionError("không được OCR sau March"))
        boss._march_target_matches = mock.Mock(return_value=True)

        boss._press_march((500, 600), (300, 680), SCREEN)

        self.assertEqual(boss.memory.status((500, 600)), JOINED)
        boss._read_card_coords.assert_not_called()
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
        boss._march_target_matches = mock.Mock(return_value=True)

        boss._press_march((500, 600), (300, 680), SCREEN)

        self.assertEqual(boss.pending, (500, 600))
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
        self.assertEqual(boss.pending, (500, 600))

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

    def test_march_target_mismatch_backs_out_without_tapping_march(self):
        bot = fake_bot()
        bot.find.return_value = (300, 680)
        boss = _Boss(bot, {})
        boss._read_march_target_coords = mock.Mock(return_value=(111, 222))

        boss._press_march((500, 600), screen=SCREEN)

        bot.tap.assert_not_called()
        bot.back.assert_called_once()
        self.assertIsNone(boss.memory.status((500, 600)))
        self.assertIn("card đã đổi", bot.record.call_args.args[0])

    def test_march_target_uses_right_side_location(self):
        bot = fake_bot()
        bot.find_all.return_value = [(31, 266), (274, 266)]
        bot.template_size.return_value = (14, 14)
        boss = _Boss(bot, {})

        with mock.patch.object(run_module, "read_coords", return_value=(767, 811)):
            self.assertEqual(boss._read_march_target_coords(SCREEN), (767, 811))

        bot.crop.assert_called_once_with(SCREEN, 288, 266, 90, 18)

    def test_invalid_ocr_coordinates_are_rejected_and_logged(self):
        bot = fake_bot()
        bot.find.return_value = (2, 3)
        boss = _Boss(bot, {})

        with mock.patch.object(run_module, "read_coords", return_value=(MAX_MAP_COORD + 1, -1)):
            self.assertIsNone(boss._read_card_coords(SCREEN, 319, 331))

        self.assertIn("Bỏ tọa độ OCR không hợp lệ", bot.log.call_args.args[0])

    def test_missing_stamina_quantity_popup_clears_pending_join(self):
        bot = fake_bot()
        bot.find_all.return_value = [(290, 360)]
        bot.find.return_value = None
        boss = _Boss(bot, {"use_stamina": "100"})
        boss.pending = (500, 600)

        boss._use_stamina()

        bot.tap.assert_called_once_with(290, 360)
        bot.back.assert_called_once()
        self.assertIsNone(boss.pending)
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
        self.assertEqual(bot.screenshot.call_count, 6)
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
        boss._march_target_matches = mock.Mock(return_value=True)

        boss._press_march((500, 600), (300, 680), SCREEN)

        self.assertEqual(boss.memory.status((500, 600)), JOINED)
        self.assertIn("đã hành quân tới boss", bot.record.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
