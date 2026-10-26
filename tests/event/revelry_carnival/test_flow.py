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
        self.assertEqual(REWARD_REGION, (2, 66, 98, 98))


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
    @mock.patch.object(run, "_claim_rewards", return_value=True)
    @mock.patch.object(run, "_green_claims", return_value=[(330, 520)])
    @mock.patch.object(run, "_gray_claim_visible", return_value=False)
    @mock.patch.object(run, "_use_parade_masks")
    @mock.patch.object(run, "_wait", return_value=(100, 20))
    def test_green_claims_are_collected_before_touching_parade_mask(
            self, _wait, use_masks, _gray, _green, claim_rewards):
        bot = ResumeBot()
        bot.screenshot = mock.Mock(return_value=object())
        self.assertTrue(run._run_opened(bot))
        use_masks.assert_not_called()
        claim_rewards.assert_called_once_with(bot)

    @mock.patch.object(run, "_claim_rewards", return_value=True)
    @mock.patch.object(run, "_use_parade_masks", return_value=True)
    @mock.patch.object(run, "_green_claims", return_value=[])
    @mock.patch.object(run, "_gray_claim_visible", return_value=True)
    @mock.patch.object(run, "_wait", return_value=(100, 20))
    def test_successful_use_is_saved_before_reward_scan(
            self, _wait, _gray, _green, use_masks, claim_rewards):
        bot = ResumeBot()
        bot.screenshot = mock.Mock(return_value=object())
        self.assertTrue(run._run_opened(bot))
        self.assertIn(USE_DONE_KEY, bot.done)
        use_masks.assert_called_once_with(bot)
        claim_rewards.assert_called_once_with(bot)

    @mock.patch.object(run, "_claim_rewards", return_value=True)
    @mock.patch.object(run, "_use_parade_masks")
    @mock.patch.object(run, "_green_claims", return_value=[])
    @mock.patch.object(run, "_gray_claim_visible", return_value=True)
    @mock.patch.object(run, "_wait", return_value=(100, 20))
    def test_retry_resumes_at_claims_when_use_is_already_in_db(
            self, _wait, _gray, _green, use_masks, claim_rewards):
        bot = ResumeBot(done=[USE_DONE_KEY])
        bot.screenshot = mock.Mock(return_value=object())
        self.assertTrue(run._run_opened(bot))
        use_masks.assert_not_called()
        claim_rewards.assert_called_once_with(bot)

    @mock.patch.object(run, "_claim_rewards")
    @mock.patch.object(run, "_use_parade_masks", return_value=None)
    @mock.patch.object(run, "_green_claims", return_value=[])
    @mock.patch.object(run, "_gray_claim_visible", return_value=True)
    @mock.patch.object(run, "_wait", return_value=(100, 20))
    def test_how_to_get_still_scans_claims_before_done(
            self, _wait, _gray, _green, use_masks, claim_rewards):
        bot = ResumeBot()
        bot.screenshot = mock.Mock(return_value=object())
        claim_rewards.return_value = True
        self.assertTrue(run._run_opened(bot))
        use_masks.assert_called_once_with(bot)
        claim_rewards.assert_called_once_with(bot)
        self.assertIn(USE_DONE_KEY, bot.done)


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
        self.assertTrue(run._use_parade_masks(bot))
        select_max.assert_called_once_with(bot, None)
        self.assertEqual(wait.call_count, 2)  # Use, then Congratulations
        bot.back.assert_called_once()
        wait_after.assert_called_once_with(bot)


if __name__ == "__main__":
    unittest.main()
