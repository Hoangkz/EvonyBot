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
    PARADE_MASK_EMPTY_MARKER,
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
        self.assertEqual(REWARD_REGION, (4, 70, 96, 95))

    def test_all_reward_swipe_endpoints_stay_inside_green_frame(self):
        from bot.activities.event.revelry_carnival.constants import (
            RETURN_TOP_SWIPE, RETURN_TOP_SWIPE_FALLBACKS,
            SCAN_SWIPE, SCAN_SWIPE_FALLBACKS)
        x0, y0, x1, y1 = REWARD_REGION
        for gesture in (SCAN_SWIPE, RETURN_TOP_SWIPE,
                        *SCAN_SWIPE_FALLBACKS,
                        *RETURN_TOP_SWIPE_FALLBACKS):
            with self.subTest(gesture=gesture):
                self.assertTrue(x0 < gesture[0] < x1)
                self.assertTrue(y0 < gesture[1] < y1)
                self.assertTrue(x0 < gesture[2] < x1)
                self.assertTrue(y0 < gesture[3] < y1)

    def test_vertical_movement_is_not_mistaken_for_a_static_reward_frame(self):
        before = np.zeros((704, 396, 3), dtype=np.uint8)
        # Distinct horizontal rows inside the exact green reward rectangle.
        top = round(704 * REWARD_REGION[1] / 100)
        bottom = round(704 * REWARD_REGION[3] / 100)
        for y in range(top, bottom, 18):
            before[y:y + 9, 8:388] = (30 + (y % 190), 70, 150)
        after = before.copy()
        after[top:bottom, 8:388] = np.roll(
            before[top:bottom, 8:388], 24, axis=0)

        self.assertFalse(run._same_reward_position(before, after))

    def test_animated_rewards_do_not_move_the_static_level_strip(self):
        before = np.zeros((704, 396, 3), dtype=np.uint8)
        height, width = before.shape[:2]
        x0, y0, x1, y1 = run.REWARD_STATIC_REGION
        left, top = round(width * x0 / 100), round(height * y0 / 100)
        right, bottom = round(width * x1 / 100), round(height * y1 / 100)
        # Simulate the unchanging LV labels/borders while the reward artwork
        # and locks on the right keep animating.
        before[top:bottom, left:right] = np.indices(
            (bottom - top, right - left))[0, ..., None] * (1, 2, 3)
        after = before.copy()
        after[top:bottom, right:min(width, right + 180)] = 255

        self.assertTrue(run._same_reward_position(before, after))

    def test_every_visible_green_claim_is_tapped_before_the_next_swipe(self):
        bot = mock.Mock()
        first = (315, 530)
        second = (315, 640)
        with (mock.patch.object(run, "_green_claims",
                                side_effect=([first, second], [second], [])),
              mock.patch.object(run, "_close_congratulations_once",
                                return_value=False)):
            claimed, stuck = run._claim_current_view(bot)

        self.assertTrue(claimed)
        self.assertFalse(stuck)
        self.assertEqual([mock.call(*first, delay=run.STEP_DELAY),
                          mock.call(*second, delay=run.STEP_DELAY)],
                         bot.tap.call_args_list)
        bot.swipe_percent.assert_not_called()

    def test_stationary_centre_swipe_tries_green_frame_fallback_before_edge(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(run, "_reward_static_similarity",
                               side_effect=(0.95, 0.42)):
            moved = run._scroll_reward_frame(
                bot, "xuống", run.SCAN_SWIPE, run.SCAN_SWIPE_FALLBACKS)

        self.assertTrue(moved)
        self.assertEqual(
            [mock.call(*run.SCAN_SWIPE,
                       duration=run.SLOW_SWIPE_DURATION, delay=run.STEP_DELAY),
             mock.call(*run.SCAN_SWIPE_FALLBACKS[0],
                       duration=run.SLOW_SWIPE_DURATION, delay=run.STEP_DELAY)],
            bot.swipe_percent.call_args_list)

    @mock.patch.object(run, "_scan_full_list", return_value=(False, False, True))
    @mock.patch.object(run, "_swipe_to_top")
    def test_first_reward_sweep_checks_opened_view_without_swiping_up(
            self, swipe_to_top, scan_full_list):
        bot = mock.Mock()

        self.assertTrue(run._claim_rewards(bot))

        scan_full_list.assert_called_once_with(bot)
        swipe_to_top.assert_not_called()

    @mock.patch.object(run, "_scan_full_list",
                       side_effect=((True, False, True), (False, False, True)))
    @mock.patch.object(run, "_swipe_to_top", return_value=True)
    def test_repeat_sweep_returns_to_top_only_after_a_claim_was_found(
            self, swipe_to_top, scan_full_list):
        bot = mock.Mock()

        self.assertTrue(run._claim_rewards(bot))

        self.assertEqual(2, scan_full_list.call_count)
        swipe_to_top.assert_called_once_with(bot)

    @mock.patch.object(run, "_scroll_reward_frame", return_value=True)
    @mock.patch.object(run, "_claim_current_view",
                       side_effect=((False, False), (False, False)))
    def test_two_empty_views_go_to_parade_mask_check_without_extra_scrolls(
            self, claim_current_view, scroll_reward_frame):
        bot = mock.Mock()

        saw_claim, stuck, ready_for_mask = run._scan_full_list(bot)

        self.assertEqual((False, False, True),
                         (saw_claim, stuck, ready_for_mask))
        self.assertEqual(2, claim_current_view.call_count)
        scroll_reward_frame.assert_called_once_with(
            bot, "xuống", run.SCAN_SWIPE, run.SCAN_SWIPE_FALLBACKS)


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
    def test_empty_mask_marker_is_an_internal_post_tap_done_result(self):
        bot = mock.Mock()
        bot.screenshot.return_value = object()

        def find(template, **_kwargs):
            return (100, 100) if template == PARADE_MASK_EMPTY_MARKER else None

        bot.find.side_effect = find
        self.assertEqual(("done", (100, 100)), run._wait_mask_result(bot))

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
        bot.tap.assert_called_once_with(
            100, 400, delay=run.PARADE_MASK_OPEN_DELAY)


class DirectPopupTests(unittest.TestCase):
    class PopupBot:
        def __init__(self):
            self.back = mock.Mock()
            self.record = mock.Mock()

    @mock.patch.object(run, "run_task")
    @mock.patch.object(run, "_run_opened", return_value=False)
    def test_popup_marker_does_not_directly_mark_done(self, run_opened, run_task):
        bot = self.PopupBot()
        state = mock.Mock()
        run.run(bot, {}, state)
        handler = run_task.call_args.args[4]

        self.assertEqual(run.STOP,
                         handler(run.ON_PARADE_MASK_DONE, None, object()))
        bot.back.assert_called_once_with(delay=run.STEP_DELAY)
        run_opened.assert_called_once_with(bot)
        self.assertNotIn("_task_results", bot.__dict__)

    @mock.patch.object(run, "run_task")
    @mock.patch.object(run, "_run_opened", return_value=True)
    def test_popup_marker_marks_done_only_after_verified_flow(
            self, run_opened, run_task):
        bot = self.PopupBot()
        state = mock.Mock()
        run.run(bot, {}, state)
        handler = run_task.call_args.args[4]

        handler(run.ON_HOW_TO_GET, None, object())

        run_opened.assert_called_once_with(bot)
        self.assertEqual(run.KEY, bot._task_results[-1].key)
        self.assertTrue(bot._task_results[-1].done)


if __name__ == "__main__":
    unittest.main()
