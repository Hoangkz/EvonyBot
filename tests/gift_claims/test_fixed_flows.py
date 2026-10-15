import unittest
from importlib import import_module
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

from bot.activities import gift_claims
from bot.activities.gift_claims import common, lobby
from bot.activities.gift_claims.screens import GiftScreen, TITLE_TEMPLATES, identify
from bot.context.errors import YieldToBoss

event_center = import_module("bot.activities.gift_claims.event_center.run")
valuable_event = import_module("bot.activities.gift_claims.valuable_event.run")
valuable_named_flow = import_module(
    "bot.activities.gift_claims.valuable_event.named_flow.run")
back_to_territory = import_module(
    "bot.activities.gift_claims.valuable_event.back_to_territory.run")
empire_depot = import_module("bot.activities.gift_claims.valuable_event.empire_depot.run")
limited_offer = import_module("bot.activities.gift_claims.valuable_event.limited_offer.run")
login_gifts = import_module("bot.activities.gift_claims.valuable_event.login_gifts.run")
super_value_return = import_module(
    "bot.activities.gift_claims.valuable_event.super_value_return.run")


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

    def test_zone_two_prioritizes_event_center_badge(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        attempted = []

        def find_all_named(_bot, name, *_args, **_kwargs):
            if name == "EventCenter/launcher_side":
                return [(350, 270)]
            return []

        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "red_dots",
                                return_value=[(380, 180), (380, 275)]),
              mock.patch.object(lobby, "find_all", side_effect=find_all_named),
              mock.patch.object(lobby, "identify",
                                return_value=GiftScreen.EVENT_CENTER)):
            result = lobby.open_next(bot, lobby.RIGHT, attempted)

        self.assertEqual(GiftScreen.EVENT_CENTER, result)
        self.assertEqual((380, 275), attempted[0])
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
            "gift_resource_consumption_sprint",
            "gift_ancient_dynasty_treasury",
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

    def test_valuable_known_controls_are_checked_before_each_sparkle(self):
        bot = mock.Mock()
        order = []

        def fixed(*_args, **_kwargs):
            order.append("fixed")
            return common.ClaimReport()

        def sparkle(*_args, **_kwargs):
            order.append("sparkle")
            return common.ClaimReport()

        with (mock.patch.object(valuable_named_flow, "claim_fixed_controls",
                                side_effect=fixed) as fixed_claims,
              mock.patch.object(valuable_named_flow, "claim_sparkles",
                                side_effect=sparkle),
              mock.patch.object(valuable_named_flow, "back_if_close_x",
                                return_value=False)):
            report, navigated = valuable_named_flow.process_lower(
                bot, (), ("ResourceConsumptionSprint/button_free",))

        self.assertEqual(common.ClaimReport(), report)
        self.assertEqual(0, navigated)
        self.assertEqual(["fixed", "sparkle"] * 4, order)
        controls = fixed_claims.call_args_list[0].args[1]
        self.assertEqual("ResourceConsumptionSprint/button_free", controls[0])
        self.assertTrue(all(name in controls for name in common.TEXT_CLAIM_CONTROLS))

    def test_valuable_verified_claim_resets_four_empty_rounds(self):
        bot = mock.Mock()
        reports = [common.ClaimReport(1, 1)] + [common.ClaimReport()] * 4
        with (mock.patch.object(valuable_named_flow, "claim_fixed_controls",
                                side_effect=reports) as fixed,
              mock.patch.object(valuable_named_flow, "claim_sparkles",
                                return_value=common.ClaimReport()),
              mock.patch.object(valuable_named_flow, "back_if_close_x",
                                return_value=False)):
            report, _ = valuable_named_flow.process_lower(bot, (), ())

        self.assertEqual(common.ClaimReport(1, 1), report)
        self.assertEqual(5, fixed.call_count)

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

    def test_super_value_unknown_tab_signature_is_not_reopened_on_reverse_scan(self):
        original = bytes([0b10101010] * 16)
        animated = bytearray(original)
        animated[0] ^= 0b00000111
        animated[5] ^= 0b00000001
        self.assertTrue(super_value_return._signature_seen(
            bytes(animated), {original}))
        self.assertFalse(super_value_return._signature_seen(
            bytes([0b01010101] * 16), {original}))

    def test_login_gifts_never_probes_rows_without_a_glowing_chest(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_page(_bot, name, *_args, **_kwargs):
            return (40, 140) if name == login_gifts.PAGE else None

        with (mock.patch.object(login_gifts, "find", side_effect=find_page),
              mock.patch.object(login_gifts, "find_all", return_value=[]),
              mock.patch.object(login_gifts, "_tap_reward", return_value=False) as tap):
            self.assertEqual(0, login_gifts.claim_opened(bot))

        tap.assert_not_called()
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
              mock.patch.object(back_to_territory, "back_if_close_x",
                                return_value=False),
              mock.patch.object(back_to_territory, "claim_sparkles",
                                return_value=common.ClaimReport(2, 2)) as sparkle):
            self.assertEqual(2, back_to_territory.claim_opened(bot))

        sparkle.assert_called_once_with(bot, region=back_to_territory.SPARKLE_REWARDS,
                                        attempts=4)

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
        progress = gift_claims.GiftProgress()
        with mock.patch.object(event_center, "run_opened", return_value=False):
            gift_claims._dispatch(bot, GiftScreen.EVENT_CENTER, progress)

        bot.mark_daily_done.assert_not_called()
        self.assertIn(GiftScreen.EVENT_CENTER, progress.unresolved_parents)

    def test_event_center_keeps_finished_rows_across_boss_resume(self):
        bot = mock.Mock()
        progress = gift_claims.GiftProgress()
        progress.event_center_done.add(b"finished-row")
        with mock.patch.object(event_center, "run_opened", return_value=False):
            gift_claims._dispatch(bot, GiftScreen.EVENT_CENTER, progress)

        self.assertEqual({b"finished-row"}, progress.event_center_done)

    def test_back_to_territory_keeps_finished_tabs_across_boss_resume(self):
        bot = mock.Mock()
        progress = gift_claims.GiftProgress()
        progress.back_to_territory_done.add(b"finished-tab")
        with (mock.patch.object(back_to_territory, "run_opened", return_value=False),
              mock.patch.object(gift_claims, "return_home")):
            gift_claims._dispatch(bot, GiftScreen.BACK_TO_TERRITORY, progress)

        self.assertEqual({b"finished-tab"}, progress.back_to_territory_done)

    def test_event_center_finds_inner_red_tab_and_excludes_purchase_edge(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        cv2.circle(screen, (313, 68), 8, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (365, 110), 8, (0, 40, 190), thickness=-1)
        self.assertEqual([(313, 68)], event_center._inner_red_dots(screen))

        after = screen.copy()
        after[575:583, 364:372] = 255
        self.assertIsNone(common.sparkle_point(
            screen, after, region=event_center.SPARKLE_SAFE))

    def test_event_center_persistent_inner_badge_is_processed_once(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot = mock.Mock()
        bot.screenshot.return_value = screen
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.UNKNOWN),
              mock.patch.object(event_center, "_inner_red_dots",
                                return_value=[(313, 68)]),
              mock.patch.object(event_center, "_inner_tab_signature",
                                side_effect=(f"animated-{i}".encode()
                                             for i in range(100))),
              mock.patch.object(event_center, "_process_current_event_content",
                                return_value=(common.ClaimReport(), False)) as process):
            event_center._process_opened_event(bot)

        process.assert_called_once_with(bot)
        self.assertEqual(2, bot.swipe_percent.call_count)

    def test_event_center_tab_signature_tolerates_small_animation_changes(self):
        original = bytes([0b10101010] * 16)
        animated = bytearray(original)
        animated[0] ^= 0b00000111
        animated[5] ^= 0b00000001
        self.assertTrue(event_center._signature_seen(bytes(animated), {original}))

        different = bytes([0b01010101] * 16)
        self.assertFalse(event_center._signature_seen(different, {original}))

    def test_event_center_row_signature_ignores_animated_right_artwork(self):
        first = np.zeros((704, 396, 3), dtype=np.uint8)
        second = first.copy()
        first[200:264, 280:396] = 255
        second[200:264, 280:396] = (0, 0, 180)
        self.assertEqual(event_center._row_signature(first, 232),
                         event_center._row_signature(second, 232))

    def test_event_center_category_row_tolerates_small_animation_changes(self):
        original = bytes([0b11001100] * 24)
        animated = bytearray(original)
        animated[2] ^= 0b00000111
        animated[11] ^= 0b00000001
        visited = {event_center._category_signature("competition", original)}
        self.assertTrue(event_center._category_seen(
            "competition", bytes(animated), visited))
        self.assertFalse(event_center._category_seen(
            "limited", bytes(animated), visited))

    def test_event_center_special_rewards_is_tapped_and_verified(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_named(_bot, name, *_args, **_kwargs):
            if name == "PreciousBlazonExchange/button_rewards":
                return (49, 235)
            return None

        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.PRECIOUS_BLAZON_EXCHANGE),
              mock.patch.object(event_center, "find", side_effect=find_named),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=True)):
            report = event_center._tap_special_navigation(bot)

        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(49, 235, delay=1)

    def test_named_event_without_special_control_stops_immediately(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "find", return_value=None)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(), report)
        self.assertEqual(1, bot.screenshot.call_count)
        bot.sleep.assert_not_called()
        bot.tap.assert_not_called()

    def test_unknown_event_checks_special_control_four_times(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify", return_value=None),
              mock.patch.object(event_center, "find", return_value=None)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(), report)
        self.assertEqual(4, bot.screenshot.call_count)
        self.assertEqual(3, bot.sleep.call_count)
        bot.tap.assert_not_called()

    def test_event_center_unresponsive_rewards_is_tapped_only_four_times(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.HYPNOS_DREAM),
              mock.patch.object(event_center, "find", return_value=(357, 164)),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(4, 0), report)
        self.assertEqual(4, bot.tap.call_count)

    def test_event_center_disappearing_rewards_is_verified(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.HYPNOS_DREAM),
              mock.patch.object(event_center, "find",
                                side_effect=((357, 164), None)),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(357, 164, delay=1)

    def test_named_navigation_event_never_falls_through_to_sparkles(self):
        bot = mock.Mock()
        expected = common.ClaimReport(1, 1)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.DWARFS_TREASURE),
              mock.patch.object(event_center, "_tap_special_navigation",
                                return_value=expected),
              mock.patch.object(event_center, "_tap_reward_navigation") as reward,
              mock.patch.object(event_center, "claim_fixed_controls") as fixed,
              mock.patch.object(event_center, "claim_sparkles") as sparkle):
            report, closed = event_center._process_current_event_content(bot)

        self.assertEqual(expected, report)
        self.assertFalse(closed)
        reward.assert_not_called()
        fixed.assert_not_called()
        sparkle.assert_not_called()

    def test_unverified_named_navigation_event_stays_pending(self):
        bot = mock.Mock()
        unresolved = common.ClaimReport(4, 0)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.PRECIOUS_BLAZON_EXCHANGE),
              mock.patch.object(event_center, "_process_current_event_content",
                                return_value=(unresolved, False))):
            self.assertEqual(unresolved, event_center._process_opened_event(bot))

        bot.mark_daily_done.assert_not_called()

    def test_dwarf_daily_free_disappearance_is_verified_during_transition(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify",
                               side_effect=(GiftScreen.DWARFS_TREASURE, None)),
              mock.patch.object(event_center, "find",
                                side_effect=((356, 180), None)),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(356, 180, delay=1)

    def test_poseidon_opens_captured_tab_then_claims_daily_free(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_named(_bot, name, *_args, **_kwargs):
            calls[name] = calls.get(name, 0) + 1
            if name == "PoseidonsDay/tab_ocean_offering":
                return (34, 78)
            if (name == "PoseidonsDay/button_daily_free" and
                    calls[name] >= 2):
                return (355, 155)
            return None

        calls = {}
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.POSEIDONS_DAY),
              mock.patch.object(event_center, "find", side_effect=find_named),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=True)):
            report = event_center._tap_special_navigation(bot)

        self.assertEqual(common.ClaimReport(2, 1), report)
        self.assertEqual([mock.call(34, 78, delay=1),
                          mock.call(355, 155, delay=1)],
                         bot.tap.call_args_list)

    def test_star_trail_gift_is_tapped_and_verified(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "find",
                                side_effect=((360, 90), (40, 240), None)),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_reward_navigation(bot)

        self.assertEqual(common.ClaimReport(2, 1), report)
        self.assertEqual([mock.call(360, 90, delay=1),
                          mock.call(40, 240, delay=1)], bot.tap.call_args_list)

    def test_star_trail_coin_claim_uses_exact_user_crop(self):
        claim = cv2.imread(str(IMAGES / "GiftClaims" / "GraceOfStarTrail" /
                               "button_claim.png"))
        self.assertEqual((49, 41), claim.shape[:2])

    def test_grace_row_is_checked_without_an_outer_red_dot(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        visited = set()
        with (mock.patch.object(event_center, "find",
                                side_effect=lambda _bot, name, *_args, **_kwargs:
                                (120, 220) if name.startswith("GraceOfStarTrail/")
                                else None),
              mock.patch.object(event_center, "_row_dots", return_value=[]),
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "_process_opened_event") as process,
              mock.patch.object(event_center, "_back_to_list", return_value=True),
              mock.patch.object(event_center, "_list_signature", return_value=b"same"),
              mock.patch.object(event_center, "_verify_clean", return_value=True)):
            self.assertTrue(event_center._scan_category(bot, "limited", visited))

        process.assert_called_once_with(bot)
        self.assertIn(event_center.FORCED_EVENT_PREFIX + b"grace_of_star_trail",
                      visited)

    def test_dwarf_row_is_checked_without_an_outer_red_dot(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        visited = {event_center.FORCED_EVENT_PREFIX + b"grace_of_star_trail"}
        with (mock.patch.object(event_center, "find",
                                side_effect=lambda _bot, name, *_args, **_kwargs:
                                (120, 220) if name.startswith("DwarfsTreasure/")
                                else None),
              mock.patch.object(event_center, "_row_dots", return_value=[]),
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.DWARFS_TREASURE),
              mock.patch.object(event_center, "_process_opened_event") as process,
              mock.patch.object(event_center, "_back_to_list", return_value=True),
              mock.patch.object(event_center, "_list_signature", return_value=b"same"),
              mock.patch.object(event_center, "_verify_clean", return_value=True)):
            self.assertTrue(event_center._scan_category(bot, "limited", visited))

        process.assert_called_once_with(bot)
        self.assertIn(event_center.FORCED_EVENT_PREFIX + b"dwarfs_treasure",
                      visited)

    def test_grace_opened_page_uses_exact_star_trail_control(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        expected = common.ClaimReport(1, 1)
        with (mock.patch.object(event_center, "identify",
                               return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "_process_current_event_content",
                                return_value=(expected, False)) as process):
            self.assertEqual(expected, event_center._process_opened_event(bot))
        process.assert_called_once_with(bot)

    def test_grace_missing_claim_stays_pending_without_db_done(self):
        bot = mock.Mock()
        unresolved = common.ClaimReport(1, 0)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "_process_current_event_content",
                                return_value=(unresolved, False))):
            self.assertEqual(unresolved, event_center._process_opened_event(bot))

        bot.mark_daily_done.assert_not_called()

    def test_grace_claim_search_includes_top_right_control(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        seen_regions = []

        def find_named(_bot, name, *_args, **kwargs):
            seen_regions.append((name, kwargs.get("region")))
            if name.endswith("button_star_trail_gift_current"):
                return (360, 90)
            if name == "GraceOfStarTrail/button_claim":
                return (355, 116)
            return None

        with (mock.patch.object(event_center, "find", side_effect=find_named),
              mock.patch.object(event_center, "close_congratulations",
                                side_effect=(False, True))):
            report = event_center._tap_reward_navigation(bot)

        self.assertEqual(common.ClaimReport(2, 1), report)
        self.assertIn(("GraceOfStarTrail/button_claim",
                       event_center.REWARD_NAV_REGION), seen_regions)

    def test_event_center_scans_limited_only(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with (mock.patch.object(event_center, "find", return_value=(198, 25)),
              mock.patch.object(event_center, "_select_category",
                                return_value=True) as select,
              mock.patch.object(event_center, "_scan_category",
                                return_value=True) as scan,
              mock.patch.object(event_center, "return_home")):
            self.assertTrue(event_center.run_opened(bot, set()))

        self.assertEqual([mock.call(bot, "limited", 18)], select.call_args_list)
        self.assertEqual([call.args[1] for call in scan.call_args_list],
                         ["limited"])

    def test_event_center_skips_categories_completed_before_boss_yield(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        handled = {event_center._category_done_key("limited")}
        with (mock.patch.object(event_center, "find", return_value=(198, 25)),
              mock.patch.object(event_center, "_select_category",
                                return_value=True) as select,
              mock.patch.object(event_center, "_scan_category",
                                return_value=True) as scan,
              mock.patch.object(event_center, "return_home")):
            self.assertTrue(event_center.run_opened(bot, handled))

        select.assert_not_called()
        scan.assert_not_called()

    def test_event_center_special_templates_are_tightly_cropped(self):
        rewards = cv2.imread(str(IMAGES / "GiftClaims" /
                                 "PreciousBlazonExchange" / "button_rewards.png"))
        daily = cv2.imread(str(IMAGES / "GiftClaims" /
                               "DwarfsTreasure" / "button_daily_free.png"))
        hypnos = cv2.imread(str(IMAGES / "GiftClaims" /
                                "HypnosDream" / "button_rewards.png"))
        self.assertLessEqual(rewards.shape[0], 22)
        self.assertLessEqual(hypnos.shape[0], 18)
        self.assertEqual((70, 74), daily.shape[:2])

    def test_star_trail_current_icon_is_a_clickable_crop(self):
        icon = cv2.imread(str(IMAGES / "GiftClaims" / "GraceOfStarTrail" /
                              "button_star_trail_gift_current.png"))
        self.assertEqual((75, 68), icon.shape[:2])
        self.assertEqual("GraceOfStarTrail/button_star_trail_gift_current",
                         event_center.REWARD_NAVIGATION[0])

    def test_revelation_and_sealed_treasury_are_immediate_skips(self):
        bot = mock.Mock()
        for name in (GiftScreen.REVELATION_OF_HORUS,
                     GiftScreen.SEALED_IMPERIAL_TREASURY):
            with (self.subTest(screen=name),
                  mock.patch.object(event_center, "identify", return_value=name),
                  mock.patch.object(event_center, "_process_current_event_content") as process):
                self.assertEqual(common.ClaimReport(),
                                 event_center._process_opened_event(bot))
                process.assert_not_called()

    def test_generic_claim_templates_are_text_only(self):
        for name in common.TEXT_CLAIM_CONTROLS:
            image = cv2.imread(str(IMAGES / "GiftClaims" / f"{name}.png"))
            with self.subTest(template=name):
                self.assertIsNotNone(image)
                self.assertLessEqual(image.shape[0], 35)
                self.assertLessEqual(image.shape[1], 110)

    def test_activities_facebook_with_red_category_is_done(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        template = cv2.imread(str(IMAGES / "GiftClaims" / "EventCenter" /
                                  "facebook_activity.png"))
        height, width = template.shape[:2]
        screen[104:104 + height, 18:18 + width] = template
        cv2.circle(screen, (253, 64), 8, (0, 40, 190), thickness=-1)
        self.assertTrue(event_center._activities_facebook_red(self.bot, screen))

    def test_event_center_checkpointed_persistent_badge_is_skip_done(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        signature = bytes([0] * 24)
        visited = {event_center._category_signature("limited", signature)}
        with (mock.patch.object(event_center, "_row_dots", return_value=[]),
              mock.patch.object(event_center, "_verify_clean", return_value=False)):
            clean = event_center._scan_category(bot, "limited", visited)

        self.assertTrue(clean)
        self.assertTrue(any("skip/done" in call.args[0]
                            for call in bot.record.call_args_list))

    def test_each_child_module_owns_its_image_folder(self):
        folders = {
            spec.task.key: spec.tab.split("/", 1)[0]
            for spec in (*valuable_event.SPECS, *super_value_return.SPECS)
        }
        for key, folder in folders.items():
            with self.subTest(task=key):
                self.assertTrue((IMAGES / "GiftClaims" / folder).is_dir())
                self.assertTrue(any((IMAGES / "GiftClaims" / folder).glob("*.png")))

    def test_common_claim_text_matches_claim_and_claim_free_prefix(self):
        claim = cv2.imread(str(IMAGES / "GiftClaims" / "BackToTerritory" /
                              "button_claim.png"))
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        screen[400:400 + claim.shape[0], 200:200 + claim.shape[1]] = claim
        self.assertIsNotNone(common.find(
            self.bot, "Common/button_claim_text", screen, threshold=0.76))

        for collection in (valuable_event.COMMON_LOWER_CLAIMS,
                           super_value_return.COMMON_LOWER_CLAIMS,
                           event_center.FIXED_CLAIMS,
                           back_to_territory.FIXED_CLAIMS):
            self.assertIn("Common/button_claim_text", collection)

    def test_dispatch_uses_identified_inner_screen_name(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        super_result = {empire_depot.KEY: "cleared"}
        valuable_result = {limited_offer.KEY: "no_dot"}
        progress = gift_claims.GiftProgress()
        with (mock.patch.object(super_value_return, "run_opened",
                                return_value=(super_result, True)) as run_super,
              mock.patch.object(valuable_event, "run_opened",
                                return_value=(valuable_result, True)) as run_valuable):
            gift_claims._dispatch(bot, GiftScreen.SUPER_VALUE_RETURN, progress)
            gift_claims._dispatch(bot, GiftScreen.VALUABLE_EVENT, progress)

        run_super.assert_called_once()
        run_valuable.assert_called_once()
        bot.mark_daily_done.assert_not_called()

    def test_unknown_rotating_screen_is_checked_then_skipped(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        progress = gift_claims.GiftProgress()
        with (mock.patch.object(gift_claims, "return_home") as return_home,
              mock.patch.object(gift_claims, "claim_fixed_controls",
                                return_value=common.ClaimReport()) as fixed,
              mock.patch.object(gift_claims, "back_if_close_x", return_value=False),
              mock.patch.object(gift_claims, "claim_sparkles",
                                return_value=common.ClaimReport()) as sparkle,
              mock.patch.object(valuable_event, "run_opened",
                                return_value=({limited_offer.KEY: "no_dot"}, True)) as run):
            gift_claims._dispatch(bot, GiftScreen.UNKNOWN, progress)
            gift_claims._dispatch(bot, GiftScreen.VALUABLE_EVENT, progress)

        return_home.assert_called_once_with(bot)
        fixed.assert_called_once()
        sparkle.assert_called_once_with(bot, region=(5, 18, 90, 82), attempts=4)
        run.assert_called_once()
        bot.mark_daily_done.assert_not_called()

    def test_parent_with_remaining_red_marker_stays_unresolved_without_db_done(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        progress = gift_claims.GiftProgress()
        with mock.patch.object(super_value_return, "run_opened",
                               return_value=({empire_depot.KEY: "remaining"}, False)):
            gift_claims._dispatch(bot, GiftScreen.SUPER_VALUE_RETURN, progress)

        bot.mark_daily_done.assert_not_called()
        self.assertIn(GiftScreen.SUPER_VALUE_RETURN, progress.unresolved_parents)

    def test_legacy_parent_state_does_not_write_aggregate_checkpoint(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        progress = gift_claims.GiftProgress()
        with (mock.patch.object(back_to_territory, "run_opened", return_value=False),
              mock.patch.object(gift_claims, "return_home")):
            gift_claims._dispatch(bot, GiftScreen.BACK_TO_TERRITORY, progress)

        bot.mark_daily_done.assert_not_called()


if __name__ == "__main__":
    unittest.main()
