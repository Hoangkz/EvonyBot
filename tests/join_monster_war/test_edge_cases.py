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
        boss.pending_joined_count = 2

        boss._march(SCREEN, (300, 680))

        bot.back.assert_called_once()
        self.assertIsNone(boss.memory.status((500, 600)))
        self.assertEqual(boss.pending_joined_count, 0)

    def test_press_march_does_nothing_when_button_is_missing(self):
        bot = fake_bot()
        boss = _Boss(bot, {})

        boss._press_march((500, 600))

        bot.tap.assert_not_called()
        bot.back.assert_not_called()
        self.assertIsNone(boss.memory.status((500, 600)))

    def test_press_march_still_visible_backs_out_without_marking_joined(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (300, 680) if template == MARCH else None
        boss = _Boss(bot, {})

        boss._press_march((500, 600))

        bot.tap.assert_called_once()
        bot.back.assert_called_once()
        self.assertEqual(bot.screenshot.call_count, 5)
        self.assertIsNone(boss.memory.status((500, 600)))

    def test_closed_march_without_joined_confirmation_is_not_remembered(self):
        bot = fake_bot()
        march_lookups = iter([(300, 680), None])

        def find(template, **_kwargs):
            if template == MARCH:
                return next(march_lookups, None)
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})
        boss.pending_joined_count = 1
        boss._joined_rally_present = mock.Mock(return_value=False)

        boss._press_march((500, 600))

        bot.back.assert_not_called()
        self.assertIsNone(boss.memory.status((500, 600)))
        self.assertEqual(boss.pending_joined_count, 0)
        self.assertIn("chưa xác nhận được Joined", bot.record.call_args.args[0])

    def test_same_joined_count_confirms_only_matching_boss_coordinates(self):
        bot = fake_bot()
        bot.find_all.return_value = [(319, 331)]
        boss = _Boss(bot, {})
        boss.pending_joined_count = 1
        boss._read_card_coords = mock.Mock(return_value=(500, 600))

        self.assertTrue(boss._joined_rally_present(SCREEN, (500, 600)))
        self.assertFalse(boss._joined_rally_present(SCREEN, None))
        bot.find_all.assert_called_with(
            JOINED_BUTTON, screen=SCREEN, center=False,
            region=run_module.REGIONS[JOINED_BUTTON],
        )

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
        boss.pending_joined_count = 2

        boss._use_stamina()

        bot.tap.assert_called_once_with(290, 360)
        bot.back.assert_called_once()
        self.assertIsNone(boss.pending)
        self.assertEqual(boss.pending_joined_count, 0)
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

    def test_joined_memory_is_only_written_after_positive_confirmation(self):
        bot = fake_bot()
        march_lookups = iter([(300, 680), None])

        def find(template, **_kwargs):
            if template == MARCH:
                return next(march_lookups, None)
            return None

        bot.find.side_effect = find
        boss = _Boss(bot, {})
        boss._joined_rally_present = mock.Mock(return_value=True)

        boss._press_march((500, 600))

        self.assertEqual(boss.memory.status((500, 600)), JOINED)
        self.assertIn("đã tham gia boss", bot.record.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
