import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

from bot.activities import gift_claims
from bot.activities.gift_claims import (empire_depot, limited_offer, login_gifts,
                                        super_value_return, valuable_event)
from bot.activities.gift_claims import lobby
from bot.activities.gift_claims.screens import GiftScreen, TITLE_TEMPLATES, identify


ROOT = Path(__file__).parents[2]
IMAGES = ROOT / "Images"


class CvBot:
    def _template(self, name):
        image = cv2.imread(str(IMAGES / name))
        if image is None:
            raise FileNotFoundError(name)
        return image

    @staticmethod
    def find(template, threshold=0.8, screen=None, center=True, region=None):
        if region is not None:
            height, width = screen.shape[:2]
            x0, y0, x1, y1 = region
            left, top = int(width * x0 / 100), int(height * y0 / 100)
            area = screen[top:int(height * y1 / 100), left:int(width * x1 / 100)]
        else:
            area, left, top = screen, 0, 0
        result = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(result)
        if score < threshold:
            return None
        return left + x + template.shape[1] // 2, top + y + template.shape[0] // 2


class FixedGiftFlowTests(unittest.TestCase):
    def setUp(self):
        self.bot = CvBot()

    def test_every_fixed_inner_title_is_identified(self):
        for expected, name in TITLE_TEMPLATES.items():
            with self.subTest(screen=expected.value):
                template = cv2.imread(str(IMAGES / "GiftClaims" / f"{name}.png"))
                screen = np.zeros((704, 396, 3), dtype=np.uint8)
                height, width = template.shape[:2]
                screen[5:5 + height, 40:40 + width] = template
                self.assertEqual(expected, identify(self.bot, screen))

    def test_unknown_inner_screen_is_not_guessed(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        self.assertIsNone(identify(self.bot, screen))

    def test_lobby_waits_for_delayed_fixed_inner_title(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "red_dots", return_value=[(60, 520)]),
              mock.patch.object(lobby, "identify",
                                side_effect=(None, None,
                                             GiftScreen.VALUABLE_EVENT)) as identify_screen):
            result = lobby.open_next(bot, lobby.BOTTOM, [])

        self.assertEqual(GiftScreen.VALUABLE_EVENT, result)
        self.assertEqual(identify_screen.call_count, 3)
        # One lobby-settle pause plus two title-loading retries.
        self.assertEqual(bot.sleep.call_count, 3)

    def test_lobby_uses_two_red_dot_boundaries(self):
        self.assertEqual((lobby.BOTTOM, lobby.RIGHT), lobby.BOUNDARIES)
        self.assertEqual(100, lobby.REGIONS[lobby.RIGHT][2])

    def test_red_dot_detector_separates_bottom_then_right(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        cv2.circle(screen, (60, 530), 10, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (380, 200), 10, (0, 40, 190), thickness=-1)
        self.assertEqual([(60, 530)], lobby.red_dots(screen, lobby.BOTTOM))
        self.assertEqual([(380, 200)], lobby.red_dots(screen, lobby.RIGHT))

    def test_valuable_event_has_one_standard_spec_per_child_module(self):
        expected = {
            "gift_limited_offer", "gift_speedup_sprint", "gift_super_blazon_sale",
            "gift_sulis_wishing", "gift_super_value_weekly_card",
            "gift_successive_purchase_benefits",
        }
        self.assertEqual(expected, valuable_event.KEYS)
        self.assertTrue(all(spec.tab.split("/", 1)[0] for spec in valuable_event.SPECS))

    def test_super_value_return_has_one_standard_spec_per_child_module(self):
        expected = {
            "gift_empire_depot", "gift_lucky_raffle", "gift_city_growth_plan",
            "gift_login_gifts",
        }
        self.assertEqual(expected, super_value_return.KEYS)
        self.assertTrue(all(spec.tab.split("/", 1)[0] for spec in super_value_return.SPECS))
        specs = {spec.task.key: spec for spec in super_value_return.SPECS}
        self.assertFalse(specs[login_gifts.KEY].requires_dot)
        self.assertTrue(specs[empire_depot.KEY].requires_dot)

    def test_login_gifts_includes_sparkling_sixth_day_row(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_page(_bot, name, *_args, **_kwargs):
            return (40, 140) if name == login_gifts.PAGE else None

        with mock.patch.object(login_gifts, "find", side_effect=find_page):
            self.assertTrue(login_gifts.claim_opened(bot))

        self.assertIn(mock.call(34, 92, delay=0.7), bot.tap_percent.call_args_list)
        bot.swipe_percent.assert_called_once()

    def test_each_child_module_owns_its_image_folder(self):
        folders = {
            spec.task.key: spec.tab.split("/", 1)[0]
            for spec in (*valuable_event.SPECS, *super_value_return.SPECS)
        }
        for key, folder in folders.items():
            with self.subTest(task=key):
                self.assertTrue((IMAGES / "GiftClaims" / folder).is_dir())
                self.assertTrue(any((IMAGES / "GiftClaims" / folder).glob("*.png")))

    def test_dispatch_uses_identified_inner_screen_name(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        super_result = {empire_depot.KEY: "cleared"}
        valuable_result = {limited_offer.KEY: "no_dot"}
        with (mock.patch.object(gift_claims, "TASKS",
                                (empire_depot.TASK, limited_offer.TASK)),
              mock.patch.object(lobby, "open_next",
                                side_effect=(GiftScreen.SUPER_VALUE_RETURN,
                                             GiftScreen.VALUABLE_EVENT,
                                             None, None)),
              mock.patch.object(super_value_return, "run_opened",
                                return_value=(super_result, True)) as run_super,
              mock.patch.object(valuable_event, "run_opened",
                                return_value=(valuable_result, True)) as run_valuable):
            gift_claims.run(bot)

        run_super.assert_called_once_with(bot, {empire_depot.KEY})
        run_valuable.assert_called_once_with(bot, {limited_offer.KEY})
        self.assertEqual(bot.mark_daily_done.call_count, 2)

    def test_unknown_inner_screen_does_not_stop_lobby_scan(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        with (mock.patch.object(gift_claims, "TASKS", (limited_offer.TASK,)),
              mock.patch.object(lobby, "open_next",
                                side_effect=(GiftScreen.UNKNOWN,
                                             GiftScreen.VALUABLE_EVENT,
                                             None, None)),
              mock.patch.object(gift_claims, "return_home") as return_home,
              mock.patch.object(valuable_event, "run_opened",
                                return_value=({limited_offer.KEY: "no_dot"}, True)) as run):
            gift_claims.run(bot)

        return_home.assert_called_once_with(bot)
        run.assert_called_once_with(bot, {limited_offer.KEY})

    def test_parent_is_not_done_while_an_inner_red_dot_remains(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        with (mock.patch.object(gift_claims, "TASKS", (empire_depot.TASK,)),
              mock.patch.object(lobby, "open_next",
                                side_effect=(GiftScreen.SUPER_VALUE_RETURN,
                                             None, None)),
              mock.patch.object(super_value_return, "run_opened",
                                return_value=({empire_depot.KEY: "remaining"},
                                              False))):
            gift_claims.run(bot)

        bot.mark_daily_done.assert_not_called()


if __name__ == "__main__":
    unittest.main()
