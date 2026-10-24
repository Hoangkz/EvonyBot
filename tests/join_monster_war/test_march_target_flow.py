"""Hợp đồng an toàn của luồng Join -> March -> ghi nhớ boss.

File này cố ý gom các quy tắc quan trọng của thiết kế không dùng ``pending`` để
người sửa code về sau đọc tên test là hiểu hành vi bắt buộc:

* tọa độ đích thật luôn được OCR trên màn March;
* không đọc được tọa độ thì Back, tuyệt đối không March;
* bấm March rồi về danh sách War (PvP War) = đã tham gia: ghi tọa độ đích vào BossMemory
  (không tìm thẻ "Joined": danh sách đổi chậm làm bot không ghi nhớ, bấm Join lại mãi);
* bấm March rồi về màn thành chính (lỗi game) = chưa tham gia: không ghi nhớ;
* sau khi bổ sung thể lực chỉ bấm March lại với tọa độ đã đọc ở lần March trước:
  không OCR lại, không chọn đội / tướng lại.
"""

import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from bot.activities.join_monster_war.boss_memory import BossMemory, JOINED
from bot.activities.join_monster_war.constants import (
    ALLIANCE_ICON,
    BOSS_MONSTER,
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
        self.assertEqual(boss.march_coords, (767, 811))

    def test_unreadable_march_coordinate_backs_out_before_troop_or_march(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (200, 250) if template == BOSS_MONSTER else None
        )
        boss = _Boss(bot, {})
        boss._read_march_target_coords = mock.Mock(return_value=None)
        boss._pick_troop = mock.Mock()
        boss._press_march = mock.Mock()

        # Mock để test không ghi ảnh thật vào logs/images của app.
        with mock.patch.object(run_module.boss_names, "log_march_coords_fail"):
            boss._march(MARCH_SCREEN, (300, 680))

        bot.back.assert_called_once()
        boss._pick_troop.assert_not_called()
        boss._press_march.assert_not_called()

    def test_back_on_war_list_after_march_marks_the_march_coordinate(self):
        # Về danh sách War (tab PvP War) sau khi bấm March = đã Join: ghi nhớ tọa độ đọc trên màn March, không tìm thẻ "Joined".
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (300, 680) if template == MARCH
            else (200, 118) if template == PVP_WAR
            else None
        )
        boss = _Boss(bot, {})

        boss._press_march((767, 811), (300, 680), MARCH_SCREEN)

        self.assertEqual(boss.memory.status((767, 811)), JOINED)
        bot.find_all.assert_not_called()
        self.assertIn("đã hành quân tới boss (767, 811)", bot.record.call_args.args[0])

    def test_back_on_city_screen_after_march_is_not_joined(self):
        # Bấm March xong về thẳng màn thành chính (lỗi game): chưa Join, không ghi nhớ, không Back (vòng chính tự vào lại danh sách).
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (300, 680) if template == MARCH and "screen" not in _kwargs
            else (40, 600) if template == ALLIANCE_ICON
            else None
        )
        boss = _Boss(bot, {})

        boss._press_march((767, 811), (300, 680), MARCH_SCREEN)

        self.assertIsNone(boss.memory.status((767, 811)))
        bot.back.assert_not_called()
        self.assertIn("về màn thành chính (lỗi game), chưa Join boss (767, 811)", bot.record.call_args.args[0])

    def test_back_on_war_list_without_a_readable_target_is_not_remembered(self):
        bot = fake_bot()
        bot.find.side_effect = lambda template, **_kwargs: (
            (300, 680) if template == MARCH
            else (200, 118) if template == PVP_WAR
            else None
        )
        boss = _Boss(bot, {})

        boss._press_march(None, (300, 680), MARCH_SCREEN)

        self.assertIn("không có tọa độ boss, không ghi nhớ", bot.record.call_args.args[0])

    def test_stamina_refill_presses_march_again_without_ocr_or_troop_pick(self):
        bot = fake_bot()
        boss = _Boss(bot, {"use_stamina": "100"})
        boss._poll_screen = mock.Mock(side_effect=[
            (SCREEN, [(290, 360)]),       # màn Use Item
            (SCREEN, (300, 500)),         # popup số lượng
            (SCREEN, True),               # màn dùng thể lực đã đóng
        ])
        boss.march_coords = (767, 811)      # đã đọc ở lần March trước khi hết thể lực
        boss._read_march_target_coords = mock.Mock()
        boss._pick_troop = mock.Mock()
        boss._press_march = mock.Mock()

        boss._use_stamina()

        boss._read_march_target_coords.assert_not_called()
        boss._pick_troop.assert_not_called()
        boss._press_march.assert_called_once_with((767, 811), None, SCREEN)

    def test_stamina_popup_never_closing_backs_out_twice_without_march(self):
        bot = fake_bot()
        boss = _Boss(bot, {"use_stamina": "100"})
        boss.march_coords = (767, 811)
        boss._poll_screen = mock.Mock(side_effect=[
            (SCREEN, [(290, 360)]),       # màn Use Item
            (SCREEN, (300, 500)),         # popup số lượng
            (SCREEN, False),              # 10 s đầu: popup chưa đóng
            (SCREEN, False),              # 10 s sau: vẫn chưa đóng
        ])
        boss._press_march = mock.Mock()

        boss._use_stamina()

        self.assertEqual(bot.back.call_count, 4)    # 1 sau khi dùng + 1 giữa hai đợt chờ + 2 khi bỏ cuộc
        boss._press_march.assert_not_called()

    def test_unreadable_list_card_does_not_block_the_next_valid_card(self):
        bot = fake_bot()
        bot.template_size.return_value = (10, 10)
        boss = _Boss(bot, {})
        boss._join_buttons = mock.Mock(return_value=([(319, 300), (319, 420)], []))
        boss._read_card_coords = mock.Mock(side_effect=[None, (767, 811)])
        boss._boss_is_wanted = mock.Mock(return_value=True)
        boss._join_text_is_red = mock.Mock(return_value=False)
        boss._stable_join_target = mock.Mock(return_value=(319, 420))

        with mock.patch.object(run_module.boss_names, "log_march_coords_fail"):   # không ghi ảnh thật
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
