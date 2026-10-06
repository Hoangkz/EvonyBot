"""Hợp đồng an toàn của luồng Join -> March -> xác nhận Joined.

File này cố ý gom các quy tắc quan trọng của thiết kế không dùng ``pending`` để
người sửa code về sau đọc tên test là hiểu hành vi bắt buộc:

* tọa độ đích thật luôn được OCR trên màn March;
* không đọc được tọa độ thì Back, tuyệt đối không March;
* PvP War chỉ chứng minh đã về danh sách, chưa chứng minh đã tham gia;
* chỉ hàng Joined có đúng tọa độ đích mới được ghi vào BossMemory;
* sau khi bổ sung thể lực phải OCR lại màn March, không tái sử dụng tọa độ cũ.
"""

import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from bot.activities.join_monster_war.boss_memory import BossMemory, JOINED
from bot.activities.join_monster_war.constants import (
    BOSS_MONSTER,
    JOINED_BUTTON,
    MARCH,
    PVP_WAR,
)
from bot.activities.join_monster_war.run import _Boss


run_module = importlib.import_module("bot.activities.join_monster_war.run")
SCREEN = np.zeros((704, 396, 3), dtype=np.uint8)
MARCH_SCREEN = np.ones((704, 396, 3), dtype=np.uint8)


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


class MarchTargetContractTests(unittest.TestCase):
    """Các test này là contract; thay đổi flow phải cập nhật cả test lẫn FLOW.md."""

    def setUp(self):
        patcher = mock.patch.object(run_module, "delay", lambda *_args, **_kwargs: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_march_screen_coordinate_is_the_source_of_truth(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (200, 250) if template == BOSS_MONSTER
            else (300, 680) if template == MARCH
            else None
        )
        boss = _Boss(bot, {})
        boss._read_march_target_coords = mock.Mock(return_value=(767, 811))
        boss._pick_troop = mock.Mock(return_value=1)
        boss._press_march = mock.Mock()

        boss._march(MARCH_SCREEN, (300, 680))

        boss._press_march.assert_called_once_with((767, 811), (300, 680), MARCH_SCREEN)

    def test_unreadable_march_coordinate_backs_out_before_troop_or_march(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (200, 250) if template == BOSS_MONSTER else None
        )
        boss = _Boss(bot, {})
        boss._read_march_target_coords = mock.Mock(return_value=None)
        boss._pick_troop = mock.Mock()
        boss._press_march = mock.Mock()

        boss._march(MARCH_SCREEN, (300, 680))

        bot.back.assert_called_once()
        boss._pick_troop.assert_not_called()
        boss._press_march.assert_not_called()

    def test_pvp_war_without_matching_joined_row_is_not_success(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (300, 680) if template == MARCH
            else (200, 118) if template == PVP_WAR
            else None
        )
        boss = _Boss(bot, {})
        boss._joined_target_visible = mock.Mock(return_value=False)

        boss._press_march((767, 811), (300, 680), MARCH_SCREEN)

        self.assertIsNone(boss.memory.status((767, 811)))
        self.assertIn("chưa thấy Joined đúng boss", bot.record.call_args.args[0])

    def test_pvp_war_without_a_readable_target_is_not_success(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (300, 680) if template == MARCH
            else (200, 118) if template == PVP_WAR
            else None
        )
        boss = _Boss(bot, {})
        boss._joined_target_visible = mock.Mock(return_value=True)

        boss._press_march(None, (300, 680), MARCH_SCREEN)

        boss._joined_target_visible.assert_not_called()
        self.assertIn("chưa thấy Joined đúng boss None", bot.record.call_args.args[0])

    def test_matching_joined_row_marks_actual_march_coordinate(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (300, 680) if template == MARCH
            else (200, 118) if template == PVP_WAR
            else None
        )
        boss = _Boss(bot, {})
        boss._joined_target_visible = mock.Mock(return_value=True)

        boss._press_march((767, 811), (300, 680), MARCH_SCREEN)

        self.assertEqual(boss.memory.status((767, 811)), JOINED)
        boss._joined_target_visible.assert_called_once_with(SCREEN, (767, 811))

    def test_joined_confirmation_checks_every_visible_joined_row_by_coordinate(self):
        bot = fake_bot()
        bot.find_all.return_value = [(319, 300), (319, 420)]
        boss = _Boss(bot, {})
        boss._read_card_coords = mock.Mock(side_effect=[(111, 222), (767, 811)])

        self.assertTrue(boss._joined_target_visible(SCREEN, (767, 811)))

        bot.find_all.assert_called_once_with(
            JOINED_BUTTON,
            screen=SCREEN,
            center=False,
            region=run_module.REGIONS[JOINED_BUTTON],
        )

    def test_wrong_joined_coordinates_do_not_confirm_success(self):
        bot = fake_bot()
        bot.find_all.return_value = [(319, 300), (319, 420)]
        boss = _Boss(bot, {})
        boss._read_card_coords = mock.Mock(side_effect=[(111, 222), (333, 444)])

        self.assertFalse(boss._joined_target_visible(SCREEN, (767, 811)))

    def test_stamina_refill_rereads_march_target_before_retry(self):
        bot = fake_bot()
        boss = _Boss(bot, {"use_stamina": "100"})
        boss._poll_screen = mock.Mock(side_effect=[
            (SCREEN, [(290, 360)]),       # màn Use Item
            (SCREEN, (300, 500)),         # popup số lượng
            (SCREEN, True),               # popup đã đóng
            (MARCH_SCREEN, (300, 680)),   # đã Back về March
        ])
        boss._read_march_target_coords = mock.Mock(return_value=(767, 811))
        boss._press_march = mock.Mock()

        boss._use_stamina()

        boss._read_march_target_coords.assert_called_once_with(MARCH_SCREEN)
        boss._press_march.assert_called_once_with((767, 811), (300, 680), MARCH_SCREEN)

    def test_unreadable_list_card_does_not_block_the_next_valid_card(self):
        bot = fake_bot()
        bot.template_size.return_value = (10, 10)
        boss = _Boss(bot, {})
        boss._join_buttons = mock.Mock(return_value=([(319, 300), (319, 420)], []))
        boss._read_card_coords = mock.Mock(side_effect=[None, (767, 811)])
        boss._boss_is_wanted = mock.Mock(return_value=True)
        boss._join_text_is_red = mock.Mock(return_value=False)
        boss._stable_join_target = mock.Mock(return_value=(319, 420))

        self.assertTrue(boss._join(SCREEN))

        self.assertEqual(boss.screen_blacklist, [(319, 300)])
        bot.report_boss.assert_called_once_with((767, 811))
        bot.tap.assert_called_once_with(324, 425)

    def test_runtime_has_no_pending_target_state(self):
        boss = _Boss(fake_bot(), {})

        self.assertNotIn("pending", vars(boss))
        self.assertFalse(any(name.startswith("pending") for name in vars(boss)))


if __name__ == "__main__":
    unittest.main()
