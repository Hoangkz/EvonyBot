import unittest
import importlib
from unittest import mock

import cv2
import numpy as np

from bot.activities.event.revelry_carnival.constants import (
    CLAIM_GRAY,
    CLAIM_GREEN,
    CONGRATULATIONS,
    PARADE_MASK,
    PARADE_MASK_DONE,
    PLUS,
    REWARD_REGION,
    USE_DONE_KEY,
)
from bot.context.templates import TEMPLATE_DIR, read_image

run = importlib.import_module("bot.activities.event.revelry_carnival.run")


class ImageBot:
    def __init__(self):
        self.logs = []

    def _template(self, name):
        return read_image(TEMPLATE_DIR / name)

    @staticmethod
    def crop(screen, x, y, width, height):
        return screen[max(0, y):max(0, y) + height,
                      max(0, x):max(0, x) + width]

    def log(self, message):
        self.logs.append(message)


class ClaimColourTests(unittest.TestCase):
    def setUp(self):
        self.bot = ImageBot()
        self.green = self.bot._template(CLAIM_GREEN)
        self.gray = self.bot._template(CLAIM_GRAY)

    def test_green_and_gray_are_classified_by_colour(self):
        green_center = (self.green.shape[1] // 2, self.green.shape[0] // 2)
        gray_center = (self.gray.shape[1] // 2, self.gray.shape[0] // 2)
        self.assertTrue(run._green_claim(self.bot, self.green, green_center))
        self.assertFalse(run._green_claim(self.bot, self.gray, gray_center))

    def test_gray_claim_is_not_returned_as_green_candidate(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        y = 520
        gx, qx = 50, 270
        gh, gw = self.green.shape[:2]
        qh, qw = self.gray.shape[:2]
        screen[y:y + gh, gx:gx + gw] = self.green
        screen[y:y + qh, qx:qx + qw] = self.gray
        claims = run._green_claims(self.bot, screen)
        self.assertEqual(len(claims), 1)
        self.assertLess(abs(claims[0][0] - (gx + gw // 2)), 2)

    def test_reward_region_matches_user_marked_green_frame(self):
        self.assertEqual(REWARD_REGION, (2, 67, 98, 98))

    def test_all_reward_swipe_endpoints_stay_inside_green_frame(self):
        from bot.activities.event.revelry_carnival.constants import (
            RETURN_TOP_SWIPE, SCAN_SWIPE)
        x0, y0, x1, y1 = REWARD_REGION
        for gesture in (SCAN_SWIPE, RETURN_TOP_SWIPE):
            with self.subTest(gesture=gesture):
                self.assertTrue(x0 < gesture[0] < x1)
                self.assertTrue(y0 < gesture[1] < y1)
                self.assertTrue(x0 < gesture[2] < x1)
                self.assertTrue(y0 < gesture[3] < y1)

    def test_vertical_movement_is_not_mistaken_for_a_static_reward_frame(self):
        before = np.zeros((704, 396, 3), dtype=np.uint8)
        # Distinct horizontal rows inside the exact green reward rectangle.
        top, bottom = round(704 * 67 / 100), round(704 * 98 / 100)
        for y in range(top, bottom, 18):
            before[y:y + 9, 8:388] = (30 + (y % 190), 70, 150)
        after = before.copy()
        after[top:bottom, 8:388] = np.roll(
            before[top:bottom, 8:388], 24, axis=0)

        self.assertFalse(run._same_reward_position(before, after))


class ResumeBot:
    def __init__(self, done=()):
        self.done = set(done)
        self.logs = []

    def is_daily_done(self, key):
        return key in self.done

    def mark_daily_done(self, key):
        self.done.add(key)

    def log(self, message):
        self.logs.append(message)

    record = log


class ResumeTests(unittest.TestCase):
    @mock.patch.object(run, "_check_parade_mask_done")
    @mock.patch.object(run, "_use_parade_masks")
    @mock.patch.object(run, "_claim_rewards", return_value=False)
    @mock.patch.object(run, "_wait", return_value=(100, 20))
    def test_incomplete_first_reward_sweep_never_touches_parade_mask(
            self, _wait, claim_rewards, use_masks, check_done):
        bot = ResumeBot()
        bot.screenshot = mock.Mock(return_value=object())

        self.assertFalse(run._run_opened(bot))
        claim_rewards.assert_called_once_with(bot)
        use_masks.assert_not_called()
        check_done.assert_not_called()

    @mock.patch.object(run, "_check_parade_mask_done")
    @mock.patch.object(run, "_use_parade_masks", return_value="done")
    @mock.patch.object(run, "_claim_rewards", return_value=True)
    @mock.patch.object(run, "_wait", return_value=(100, 20))
    def test_terminal_marker_after_first_mask_tap_is_done(
            self, _wait, claim_rewards, use_masks, check_done):
        bot = ResumeBot()
        bot.screenshot = mock.Mock(return_value=object())

        self.assertTrue(run._run_opened(bot))
        claim_rewards.assert_called_once_with(bot)
        use_masks.assert_called_once_with(bot)
        check_done.assert_not_called()
        self.assertNotIn(USE_DONE_KEY, bot.done)

    @mock.patch.object(run, "_check_parade_mask_done", return_value=True)
    @mock.patch.object(run, "_use_parade_masks", return_value="used")
    @mock.patch.object(run, "_claim_rewards", return_value=True)
    @mock.patch.object(run, "_wait", return_value=(100, 20))
    def test_used_masks_then_clean_rewards_requires_second_mask_done_check(
            self, _wait, claim_rewards, use_masks, check_done):
        bot = ResumeBot()
        bot.screenshot = mock.Mock(return_value=object())

        self.assertTrue(run._run_opened(bot))
        self.assertEqual(2, claim_rewards.call_count)
        use_masks.assert_called_once_with(bot)
        check_done.assert_called_once_with(bot)
        self.assertIn(USE_DONE_KEY, bot.done)

    @mock.patch.object(run, "_check_parade_mask_done", return_value=True)
    @mock.patch.object(run, "_use_parade_masks")
    @mock.patch.object(run, "_claim_rewards", return_value=True)
    @mock.patch.object(run, "_wait", return_value=(100, 20))
    def test_resume_after_mask_use_scans_rewards_then_checks_marker(
            self, _wait, claim_rewards, use_masks, check_done):
        bot = ResumeBot(done=[USE_DONE_KEY])
        bot.screenshot = mock.Mock(return_value=object())

        self.assertTrue(run._run_opened(bot))
        claim_rewards.assert_called_once_with(bot)
        use_masks.assert_not_called()
        check_done.assert_called_once_with(bot)


class ParadeMaskFlowTests(unittest.TestCase):
    @mock.patch.object(run, "_wait_after_congratulations", return_value=True)
    @mock.patch.object(run, "_wait", return_value=(100, 500))
    @mock.patch.object(run, "_select_max", return_value=True)
    @mock.patch.object(run, "_wait_mask_result", return_value=(None, None))
    def test_no_how_to_get_and_no_plus_still_continues_max_use(
            self, wait_mask_result, select_max, wait, wait_after):
        bot = mock.Mock()
        bot.screenshot.return_value = object()

        def find(template, **kwargs):
            if template == PARADE_MASK:
                return 100, 400
            if template in (PLUS, CONGRATULATIONS):
                return None
            return None

        bot.find.side_effect = find
        self.assertEqual("used", run._use_parade_masks(bot))
        select_max.assert_called_once_with(bot, None)
        self.assertEqual(wait.call_count, 2)  # Use, then Congratulations
        bot.back.assert_called_once()
        wait_after.assert_called_once_with(bot)

    @mock.patch.object(run, "_wait_mask_result", return_value=("done", (100, 100)))
    def test_post_tap_done_marker_ends_mask_flow_without_using(self, wait_result):
        bot = mock.Mock()
        bot.screenshot.return_value = object()
        bot.find.side_effect = lambda template, **_kwargs: (
            (100, 400) if template == PARADE_MASK else None)

        self.assertEqual("done", run._use_parade_masks(bot))
        bot.tap.assert_called_once_with(100, 400, delay=run.STEP_DELAY)


if __name__ == "__main__":
    unittest.main()
