import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

from bot.activities import gift_claims
from bot.activities.gift_claims import (back_to_territory, empire_depot,
                                        event_center, limited_offer, login_gifts,
                                        super_value_return, valuable_event)
from bot.activities.gift_claims import common, lobby
from bot.activities.gift_claims.screens import GiftScreen, TITLE_TEMPLATES, identify
from bot.context.errors import YieldToBoss


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

    def test_lobby_skips_facebook_follow_us_before_opening_next_dot(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        attempted = []
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "red_dots",
                                return_value=[(380, 200), (380, 235),
                                              (380, 275)]),
              mock.patch.object(lobby, "find_all", return_value=[(360, 215)]),
              mock.patch.object(lobby, "identify",
                                return_value=GiftScreen.EVENT_CENTER)):
            result = lobby.open_next(bot, lobby.RIGHT, attempted)

        self.assertEqual(GiftScreen.EVENT_CENTER, result)
        self.assertEqual([(380, 200), (380, 235), (380, 275)], attempted)
        bot.tap.assert_called_once_with(355, 291, delay=1)

    def test_red_dot_detector_separates_bottom_then_right(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        cv2.circle(screen, (60, 530), 10, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (380, 200), 10, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (295, 40), 10, (0, 40, 190), thickness=-1)
        self.assertEqual([(60, 530)], lobby.red_dots(screen, lobby.BOTTOM))
        self.assertEqual([(380, 200)], lobby.red_dots(screen, lobby.RIGHT))

    def test_right_rail_merges_artwork_fragment_with_real_badge(self):
        points = [(361, 142), (382, 137), (382, 275)]
        self.assertEqual([(382, 137), (382, 275)],
                         lobby._dedupe_right_dots(points, 1.0))

    def test_valuable_event_has_one_standard_spec_per_child_module(self):
        expected = {
            "gift_general_vault",
            "gift_refining_stone_sprint", "gift_strategic_stockpile",
            "gift_limited_offer", "gift_speedup_sprint", "gift_super_blazon_sale",
            "gift_sulis_wishing", "gift_super_value_weekly_card",
            "gift_successive_purchase_benefits",
        }
        self.assertEqual(expected, valuable_event.KEYS)
        self.assertTrue(all(spec.tab.split("/", 1)[0] for spec in valuable_event.SPECS))

    def test_carousel_dot_belongs_only_to_nearest_tab(self):
        left, right = valuable_event.SPECS[:2]
        owner = valuable_event._owner_for_dot(
            (96, 70), [(left, (50, 70)), (right, (100, 70))])
        self.assertIs(right, owner[0])

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

        with (mock.patch.object(login_gifts, "find", side_effect=find_page),
              mock.patch.object(login_gifts, "find_all", return_value=[]),
              mock.patch.object(login_gifts, "_tap_reward", return_value=False) as tap):
            self.assertEqual(0, login_gifts.claim_opened(bot))

        self.assertTrue(any(abs(call.args[1][1] - round(704 * 0.92)) <= 1
                            for call in tap.call_args_list))
        bot.swipe_percent.assert_called_once()

    def test_login_gift_confirms_and_closes_congratulations(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_popup(_bot, name, *_args, **_kwargs):
            return (198, 319) if name == login_gifts.CONGRATULATIONS else None

        with mock.patch.object(login_gifts, "find", side_effect=find_popup):
            self.assertTrue(login_gifts._tap_reward(bot, (123, 470)))

        bot.tap.assert_called_once_with(123, 470, delay=1)
        bot.back.assert_called_once_with(delay=0.8)

    def test_back_to_territory_claims_congratulations_day(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(back_to_territory, "claim_fixed_controls",
                                return_value=common.ClaimReport()),
              mock.patch.object(back_to_territory, "_claim_visible_login_rewards",
                                return_value=common.ClaimReport()),
              mock.patch.object(back_to_territory, "_inner_dots", return_value=[]),
              mock.patch.object(back_to_territory, "find", return_value=(198, 25)),
              mock.patch.object(back_to_territory, "claim_sparkle",
                                side_effect=(common.ClaimReport(1, 1),
                                             common.ClaimReport(1, 1),
                                             common.ClaimReport())) as sparkle):
            self.assertEqual(2, back_to_territory.claim_opened(bot))

        self.assertEqual(3, sparkle.call_count)

    def test_back_to_territory_detects_red_tabs_below_carousel(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        cv2.circle(screen, (78, 333), 5, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (254, 380), 5, (0, 40, 190), thickness=-1)
        self.assertEqual([(78, 333), (254, 380)],
                         back_to_territory._inner_dots(screen))

    def test_back_to_territory_claims_multiple_identical_buttons(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(back_to_territory, "find_all",
                                side_effect=([(333, 477), (333, 584)],
                                             [(333, 584)], [])),
              mock.patch.object(back_to_territory, "close_congratulations",
                                side_effect=(True, True))):
            report = back_to_territory._claim_visible_login_rewards(bot)

        self.assertEqual(common.ClaimReport(2, 2), report)
        self.assertEqual(2, bot.tap.call_count)

    def test_event_center_remaining_red_is_not_marked_done(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        with (mock.patch.object(lobby, "open_next",
                                side_effect=(GiftScreen.EVENT_CENTER, None, None)),
              mock.patch.object(event_center, "run_opened", return_value=False)):
            with self.assertRaises(YieldToBoss):
                gift_claims.run(bot)

        bot.mark_daily_done.assert_not_called()

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
        with (mock.patch.object(lobby, "open_next",
                                side_effect=(GiftScreen.SUPER_VALUE_RETURN,
                                             GiftScreen.VALUABLE_EVENT,
                                             None, None)),
              mock.patch.object(super_value_return, "run_opened",
                                return_value=(super_result, True)) as run_super,
              mock.patch.object(valuable_event, "run_opened",
                                return_value=(valuable_result, True)) as run_valuable):
            gift_claims.run(bot)

        run_super.assert_called_once()
        run_valuable.assert_called_once()
        bot.mark_daily_done.assert_called_once_with(gift_claims.KEY)

    def test_unknown_inner_screen_is_not_saved_as_complete(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        with (mock.patch.object(lobby, "open_next",
                                side_effect=(GiftScreen.UNKNOWN,
                                             GiftScreen.VALUABLE_EVENT,
                                             None, None, None, None)),
              mock.patch.object(gift_claims, "return_home") as return_home,
              mock.patch.object(valuable_event, "run_opened",
                                return_value=({limited_offer.KEY: "no_dot"}, True)) as run):
            with self.assertRaises(YieldToBoss):
                gift_claims.run(bot)
            gift_claims.run(bot)

        return_home.assert_called_once_with(bot)
        run.assert_called_once()
        bot.mark_daily_done.assert_called_once_with(gift_claims.KEY)

    def test_parent_with_remaining_red_marker_yields_without_db_done(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        with (mock.patch.object(lobby, "open_next",
                                side_effect=(GiftScreen.SUPER_VALUE_RETURN,
                                             None, None)),
              mock.patch.object(super_value_return, "run_opened",
                                return_value=({empire_depot.KEY: "remaining"},
                                              False))):
            with self.assertRaises(YieldToBoss):
                gift_claims.run(bot)

        bot.mark_daily_done.assert_not_called()

    def test_parent_disappearing_on_complete_rescan_clears_stale_blocker(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        with (mock.patch.object(lobby, "open_next",
                                side_effect=(GiftScreen.BACK_TO_TERRITORY,
                                             None, None, None, None)),
              mock.patch.object(back_to_territory, "run_opened",
                                return_value=False),
              mock.patch.object(gift_claims, "return_home")):
            with self.assertRaises(YieldToBoss):
                gift_claims.run(bot)
            self.assertTrue(gift_claims.run(bot))

        bot.mark_daily_done.assert_called_once_with(gift_claims.KEY)


if __name__ == "__main__":
    unittest.main()
