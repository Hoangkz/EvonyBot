import unittest
from importlib import import_module
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

from bot.activities.gift_claims import common
from bot.activities.gift_claims.screens import GiftScreen

event_center = import_module("bot.activities.gift_claims.event_center.run")
garuda = import_module(
    "bot.activities.gift_claims.event_center.garuda_trial.run")

ROOT = Path(__file__).resolve().parents[2]
IMAGES = ROOT / "Images" / "GiftClaims" / "EventCenter" / "GarudaTrial"


class GarudaTrialTests(unittest.TestCase):
    def test_registered_as_an_activities_event(self):
        self.assertIn(garuda.POLICY, event_center.EVENT_POLICIES)
        self.assertEqual("activities",
                         event_center.POLICY_CATEGORIES[garuda.KEY])
        self.assertIs(event_center.EXACT_HANDLERS[GiftScreen.GARUDA_TRIAL],
                      garuda.claim_opened)
        self.assertTrue(any(row[4] == garuda.KEY
                            for row in event_center.FORCED_ACTIVITY_ROWS))

    def test_selected_activities_tab_is_an_event_center_list_marker(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        selected = cv2.imread(str(
            ROOT / "Images" / "GiftClaims" / "EventCenter" /
            "tab_activities_on.png"))
        screen[70:70 + selected.shape[0],
               162:162 + selected.shape[1]] = selected
        bot = mock.Mock()
        bot._template.side_effect = lambda name: cv2.imread(
            str(ROOT / "Images" / name))
        bot.find.side_effect = lambda template, **kwargs: (
            (162 + template.shape[1] // 2, 70 + template.shape[0] // 2)
            if template.shape == selected.shape else None)

        self.assertTrue(event_center._event_center_list_open(bot, screen))

    def test_supplied_claim_states_have_distinct_colour_bands(self):
        active = cv2.imread(str(IMAGES / "button_claim_active.png"))
        inactive = cv2.imread(str(IMAGES / "button_claim_inactive.png"))
        claimed = cv2.imread(str(IMAGES / "status_claimed.png"))

        self.assertGreater(garuda._green_ratio(
            active, (active.shape[1] // 2, active.shape[0] // 2)), 0.80)
        self.assertLess(garuda._green_ratio(
            inactive, (inactive.shape[1] // 2, inactive.shape[0] // 2)), 0.05)
        self.assertLess(garuda._green_ratio(
            claimed, (claimed.shape[1] // 2, claimed.shape[0] // 2)), 0.05)

    def test_claimed_prefix_match_near_gray_claim_is_not_counted(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)

        def matches(_bot, template, *_args, **_kwargs):
            if template == garuda.INACTIVE_CLAIM:
                return [(331, 357)]
            if template == garuda.CLAIMED:
                # False Claimed match observed on live 21513: its centre is
                # shifted right inside the same ordinary gray Claim button.
                return [(339, 357)]
            return []

        with mock.patch.object(garuda, "find_all", side_effect=matches):
            active, inactive, claimed = garuda._claim_states(bot, screen)

        self.assertEqual([], active)
        self.assertEqual([(331, 357)], inactive)
        self.assertEqual([], claimed)

    def test_gray_claim_and_claimed_finish_after_two_swipes(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(garuda, "find", return_value=(120, 120)),
              mock.patch.object(
                  garuda, "_claim_states",
                  return_value=([], [(330, 250)], [(330, 350)]))):
            report, done = garuda.claim_opened(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        self.assertEqual(2, bot.swipe_percent.call_count)
        self.assertEqual([
            mock.call(*garuda.SCAN_SWIPE,
                      duration=garuda.SWIPE_DURATION_SECONDS,
                      delay=garuda.UI_SETTLE_SECONDS),
            mock.call(*garuda.SCAN_SWIPE,
                      duration=garuda.SWIPE_DURATION_SECONDS,
                      delay=garuda.UI_SETTLE_SECONDS),
        ], bot.swipe_percent.call_args_list)
        bot.tap.assert_called_once_with(120, 120,
                                        delay=garuda.UI_SETTLE_SECONDS)

    def test_scan_swipe_and_claim_search_stay_inside_marked_green_frame(self):
        left, top, right, bottom = garuda.CONTENT_REGION
        claim_left, claim_top, claim_right, claim_bottom = garuda.CLAIM_REGION
        start_x, start_y, end_x, end_y = garuda.SCAN_SWIPE

        self.assertTrue(left <= start_x <= right)
        self.assertTrue(left <= end_x <= right)
        self.assertTrue(top <= start_y <= bottom)
        self.assertTrue(top <= end_y <= bottom)
        self.assertGreaterEqual(claim_left, left)
        self.assertGreaterEqual(claim_top, top)
        self.assertLessEqual(claim_right, right)
        self.assertLessEqual(claim_bottom, bottom)

    def test_green_claim_is_taken_before_two_clean_swipes(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        states = iter([
            ([(330, 250)], [], []),  # first scan: actionable Claim
            ([], [], [(330, 250)]),  # verification: it became Claimed
            ([], [], [(330, 250)]),  # clean swipe 1
            ([], [], [(330, 250)]),  # clean swipe 2
        ])
        with (mock.patch.object(garuda, "find", return_value=(120, 120)),
              mock.patch.object(garuda, "_claim_states",
                                side_effect=lambda *_args: next(states)),
              mock.patch.object(garuda, "close_congratulations")):
            report, done = garuda.claim_opened(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        self.assertEqual(2, bot.swipe_percent.call_count)
        self.assertEqual([mock.call(120, 120, delay=garuda.UI_SETTLE_SECONDS),
                          mock.call(330, 250, delay=garuda.UI_SETTLE_SECONDS)],
                         bot.tap.call_args_list)

    def test_still_green_claim_is_retried_instead_of_pending(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        states = iter([
            ([(330, 250)], [], []),
            ([(330, 250)], [], []),  # still green after first tap
            ([(330, 250)], [], []),
            ([], [], [(330, 250)]),  # second tap succeeds
            ([], [], [(330, 250)]),
            ([], [], [(330, 250)]),
        ])
        with (mock.patch.object(garuda, "find", return_value=(120, 120)),
              mock.patch.object(garuda, "_claim_states",
                                side_effect=lambda *_args: next(states)),
              mock.patch.object(garuda, "close_congratulations")):
            report, done = garuda.claim_opened(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(2, 1), report)
        self.assertEqual(3, bot.tap.call_count)  # Treasure + Claim + retry

    def test_missing_treasure_is_exhausted_not_pending(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(garuda, "find", return_value=None):
            report, done = garuda.claim_opened(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        self.assertEqual(2, bot.sleep.call_count)
        bot.tap.assert_not_called()


if __name__ == "__main__":
    unittest.main()
