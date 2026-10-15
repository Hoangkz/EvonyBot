"""Flow tests rebuilt from screenshots captured while running the current Join Boss code."""

import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities import join_monster_war
from bot.activities.join_monster_war.boss_memory import JOINED
from bot.activities.join_monster_war.constants import (
    IDLE,
    JOIN,
    JOIN_THRESHOLD,
    LISTBOSS,
    MARCH,
    PRESET_X0,
    PRESET_Y,
    REGIONS,
)
from bot.activities.join_monster_war.run import _Boss
from bot.context import BotContext
from tests.flow import Step, end, run_flow, swipe, tap, tap_at, tap_pct


SCREENS = Path(__file__).parent / "screens" / "new_join_boss_flow"

SETTINGS = {
    "troop": ["Troop 1"],
    "use_stamina": "No",
    "exit_when_idle": True,
    "selected_bosses": [
        {
            "category_key": "special_and_recurring_event_bosses",
            "name": "Cerberus",
            "levels": [1],
        }
    ],
}

DOWN = swipe(50, 65, 50, 40)
UP = swipe(50, 40, 50, 65)


class CurrentCodeJoinBossFlow(unittest.TestCase):
    def test_multiple_forbidden_cerberus_cards_do_not_block_allowed_boss(self):
        """Nhiều rally Cerberus bị cấm xen phía trên không được chặn boss hợp lệ."""
        points = [(319, 290), (319, 370), (319, 450), (319, 530)]

        class FakeBot:
            def __init__(self):
                from bot.activities.join_monster_war.boss_memory import BossMemory

                self.boss_memory = BossMemory()
                self.reported = []
                self.taps = []

            def template_size(self, _template):
                return 20, 14

            def find_all(self, template, **_kwargs):
                return list(points) if template == JOIN else []

            def crop(self, image, *_args):
                return image

            def find(self, *_args, **_kwargs):
                return None

            def screenshot(self):
                return np.zeros((704, 396, 3), dtype=np.uint8)

            def report_boss(self, coords):
                self.reported.append(coords)

            def tap(self, x, y):
                self.taps.append((x, y))

            def log(self, _message):
                pass

        bot = FakeBot()
        boss = _Boss(bot, SETTINGS)
        # Ba thẻ Cerberus bị cấm/không đúng cấp, thẻ thứ tư là boss được phép.
        boss._boss_is_wanted = mock.Mock(side_effect=[False, False, False, True, True])
        boss._join_text_is_red = mock.Mock(return_value=False)

        with mock.patch("bot.activities.join_monster_war.run.CAN_READ_COORDS", False):
            self.assertTrue(boss._join(np.zeros((704, 396, 3), dtype=np.uint8)))
        self.assertEqual(boss.screen_blacklist, points[:3])
        self.assertEqual(bot.taps, [(329, 537)])
        self.assertEqual(bot.reported, [None])

    def test_forbidden_and_expired_cerberus_cards_do_not_block_valid_boss(self):
        """Boss cấm và boss hết giờ xen kẽ vẫn phải tìm đến boss hợp lệ phía dưới."""
        points = [(319, 280), (319, 350), (319, 420), (319, 490), (319, 560)]

        class FakeBot:
            def __init__(self):
                from bot.activities.join_monster_war.boss_memory import BossMemory

                self.boss_memory = BossMemory()
                self.reported = []
                self.taps = []

            def template_size(self, _template):
                return 20, 14

            def find_all(self, template, **_kwargs):
                return list(points) if template == JOIN else []

            def crop(self, image, *_args):
                return image

            def find(self, *_args, **_kwargs):
                return None

            def screenshot(self):
                return np.zeros((704, 396, 3), dtype=np.uint8)

            def report_boss(self, coords):
                self.reported.append(coords)

            def tap(self, x, y):
                self.taps.append((x, y))

            def log(self, _message):
                pass

        bot = FakeBot()
        boss = _Boss(bot, SETTINGS)
        # 1 cấm, 2 đúng loại nhưng hết giờ, 3 cấm, 4 hết giờ, 5 hợp lệ.
        boss._boss_is_wanted = mock.Mock(side_effect=[False, True, False, True, True, True])
        boss._join_text_is_red = mock.Mock(side_effect=[True, True, False, False, False])

        with mock.patch("bot.activities.join_monster_war.run.CAN_READ_COORDS", False):
            self.assertTrue(boss._join(np.zeros((704, 396, 3), dtype=np.uint8)))
        self.assertEqual(boss.screen_blacklist, points[:4])
        self.assertEqual(bot.taps, [(329, 567)])
        self.assertEqual(bot.reported, [None])

    def test_live_main_flow_home_join_march_joined(self):
        flow = [
            Step("01_home_listboss.png", tap(LISTBOSS)),
            Step("06_valid_boss_before_join.png", tap(JOIN)),
            Step("07_march_before_action.png", tap_pct(PRESET_X0, PRESET_Y, tol=8)),
            Step("07_march_before_action.png", tap(MARCH)),
            Step("08_war_after_march_joined.png", end(IDLE)),
        ]
        device = run_flow(self, join_monster_war.run, SCREENS, flow, SETTINGS)
        self.assertEqual(device.reported, [(767, 811)])
        self.assertIn("Chọn đội quân 1", device.logs)
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status((767, 811)), JOINED)

    def test_live_expired_rallies_are_never_tapped(self):
        settings = {
            **SETTINGS,
            "selected_bosses": [
                {
                    "category_key": "special_and_recurring_event_bosses",
                    "name": "Cerberus",
                    "levels": [1],
                },
                {"category_key": "standard_bosses", "name": "Manticore", "levels": []},
            ],
        }
        flow = [
            *[Step("05_expired_rallies_list.png", DOWN) for _ in range(3)],
            *[Step("05_expired_rallies_list.png", UP) for _ in range(3)],
            Step("05_expired_rallies_list.png", end(IDLE)),
        ]
        device = run_flow(self, join_monster_war.run, SCREENS, flow, settings)
        self.assertEqual(device.reported, [])
        self.assertFalse(any(event[0] == "tap" for _, event in device.events))
        self.assertIn("thời gian đỏ, bỏ qua lần này", "\n".join(device.logs))

    def test_live_war_checkbox_is_unticked_before_scrolling(self):
        flow = [
            Step("04_war_checkbox_on.png", tap_at(201, 118, tol=8)),
            Step("03_war_joined_list.png", DOWN),
        ]
        device = run_flow(self, join_monster_war.run, SCREENS, flow, SETTINGS)
        self.assertIn("Bỏ tích ô War (chỉ giữ rally đánh boss)", device.logs)

    def test_live_joined_short_list_returns_idle(self):
        device = run_flow(
            self,
            join_monster_war.run,
            SCREENS,
            [Step("08_war_after_march_joined.png", end(IDLE))],
            SETTINGS,
        )
        self.assertEqual(device.reported, [])
        self.assertEqual(device.events, [])

    def test_live_timer_color_changes_from_red_to_available(self):
        checker = SimpleNamespace(
            bot=BotContext(SimpleNamespace(serial="current-code-flow"), threading.Event(), None, lambda _: None)
        )
        join_height = checker.bot.template_size(JOIN)[1]

        expired = cv2.imread(str(SCREENS / "05_expired_rallies_list.png"))
        available = cv2.imread(str(SCREENS / "06_valid_boss_before_join.png"))
        self.assertIsNotNone(expired)
        self.assertIsNotNone(available)

        expired_buttons = checker.bot.find_all(
            JOIN, JOIN_THRESHOLD, expired, center=False, region=REGIONS[JOIN]
        )
        available_buttons = checker.bot.find_all(
            JOIN, JOIN_THRESHOLD, available, center=False, region=REGIONS[JOIN]
        )
        self.assertTrue(expired_buttons)
        self.assertTrue(available_buttons)
        self.assertTrue(
            all(_Boss._join_text_is_red(checker, expired, x, y, join_height)
                for x, y in expired_buttons)
        )
        self.assertTrue(
            any(not _Boss._join_text_is_red(checker, available, x, y, join_height)
                for x, y in available_buttons)
        )


if __name__ == "__main__":
    unittest.main()
