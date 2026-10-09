import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities import gift_claims
from bot.activities.gift_claims import common, valuable_event
from bot.activities.gift_claims.screens import GiftScreen
from bot.activities.daily_activities.run import _run_gift_claims
from bot.context.errors import YieldToBoss
from bot.worker.tasks import PRIORITY_FILE
from database import Database


class GiftClaimRegistryTests(unittest.TestCase):
    def test_all_declared_templates_are_readable_images(self):
        folder = Path(__file__).parents[2] / "Images" / "GiftClaims"
        expected = {
            "EventCenter/launcher.png", "EventCenter/launcher_side.png",
            "Common/button_claimable.png", "Common/button_claimable_alt.png",
            "BackToTerritory/title.png", "BackToTerritory/button_claim.png",
            "FollowUs/title.png",
            "FollowUs/facebook_icon.png",
            "GeneralVault/tab.png", "GeneralVault/button_daily_free.png",
            "DragonBattle/title.png",
            "Lobby/notification_dot.png", "Lobby/notification_dot_bottom.png",
            "ValuableEvent/title.png",
            "ValuableEvent/notification_dot.png", "SuperValueReturn/title.png",
            "SuperValueReturn/notification_dot.png", "EventCenter/notification_dot.png",
            "BacchusTavern/title.png", "LoginGifts/title.png",
            "DragonBattle/reward.png", "DragonBattle/list_row.png",
            "GraceOfStarTrail/title.png", "GraceOfStarTrail/list_row.png",
            "GraceOfStarTrail/button_star_trail_gift.png",
            "GraceOfStarTrail/button_claim.png", "LimitedOffer/tab.png",
            "LimitedOffer/button_free.png", "SpeedupSprint/tab.png",
            "RefiningStoneSprint/tab.png",
            "RefiningStoneSprint/subtab_sprint_quest.png",
            "StrategicStockpile/tab.png",
            "StrategicStockpile/button_free.png",
            "StrategicStockpile/button_redeem.png",
            "StrategicStockpile/button_confirm_redeem.png",
            "StrategicStockpile/subtab_stockpile.png",
            "SpeedupSprint/subtab_package.png", "SpeedupSprint/button_free.png",
            "SuperBlazonSale/tab.png",
            "SuperBlazonSale/button_free.png", "SulisWishing/tab.png",
            "SuperValueWeeklyCard/tab.png", "SuperValueWeeklyCard/button_scores.png",
            "SuccessivePurchaseBenefits/tab.png",
            "SuccessivePurchaseBenefits/button_daily_free.png",
            "SuccessivePurchaseBenefits/button_daily_free_text.png", "LoginGifts/tab.png",
            "LoginGifts/detail_popup.png", "LoginGifts/congratulations.png",
            "LoginGifts/reward_glowing_treasure_box.png",
            "EmpireDepot/tab.png", "EmpireDepot/button_claimable.png",
            "LuckyRaffle/tab.png", "LuckyRaffle/button_claimable.png",
            "CityGrowthPlan/tab.png", "CityGrowthPlan/button_claim_all.png",
            "CityGrowthPlan/detail_popup.png", "CityGrowthPlan/claimed.png",
            "EventCenter/title.png",
        }
        actual = {path.relative_to(folder).as_posix() for path in folder.rglob("*.png")}
        self.assertEqual(expected, actual)
        self.assertTrue(all(cv2.imread(str(folder / name)) is not None
                            for name in expected))

    def test_gifts_are_one_lowest_priority_db_task(self):
        data = json.loads(PRIORITY_FILE.read_text(encoding="utf-8"))
        daily = {item["key"]: item["priority"] for item in data["Daily Activities"]}
        keys = {key for key in daily if key.startswith("gift_")}

        self.assertEqual({gift_claims.KEY}, keys)
        self.assertEqual(-100, daily[gift_claims.KEY])
        self.assertLess(-100, min(value for key, value in daily.items()
                                  if not key.startswith("gift_")))

    def test_combined_gift_task_is_saved_only_after_both_boundaries_finish(self):
        done = set()
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add
        with mock.patch.object(gift_claims.lobby, "open_next",
                               side_effect=(None, None)):
            gift_claims.run(bot)
        self.assertEqual(done, {gift_claims.KEY})
        bot.mark_daily_done.assert_called_once_with(gift_claims.KEY)

    def test_interrupted_dot_is_not_saved_and_is_retried(self):
        from bot.context import TimedOut

        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        calls = [GiftScreen.VALUABLE_EVENT, GiftScreen.VALUABLE_EVENT, None, None]

        def open_next(_bot, _boundary, attempted):
            value = calls.pop(0)
            if value is not None:
                attempted.append((50, 500))
            return value

        with (mock.patch.object(gift_claims.lobby, "open_next", side_effect=open_next),
              mock.patch.object(gift_claims.valuable_event, "run_opened",
                                side_effect=(TimedOut(), ({}, True)))):
            with self.assertRaises(TimedOut):
                gift_claims.run(bot)
            self.assertEqual([], bot._gift_claims_progress.attempted["bottom"])
            gift_claims.run(bot)

        bot.mark_daily_done.assert_called_once_with(gift_claims.KEY)

    def test_database_migrates_old_child_keys_to_one_combined_task(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gift-test.db"
            db = Database(path)
            db.add_device("test-device")
            db.mark_daily_task_done("test-device", "gift_limited_offer")
            db.mark_daily_task_done("test-device", gift_claims.KEY)
            db.close()

            reopened = Database(path)
            try:
                done = reopened.daily_done("test-device")
            finally:
                reopened.close()

        self.assertIn(gift_claims.KEY, done)
        self.assertNotIn("gift_limited_offer", done)

    def test_post_daily_phase_runs_only_when_worker_enabled_it(self):
        bot = SimpleNamespace(post_daily_gifts_enabled=False)
        with mock.patch.object(gift_claims, "run") as run:
            _run_gift_claims(bot)
            run.assert_not_called()
            bot.post_daily_gifts_enabled = True
            bot.is_daily_done = lambda _key: False
            _run_gift_claims(bot)
            run.assert_called_once_with(bot)

    def test_claim_template_is_never_tapped_twice_on_an_unchanged_page(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(common, "find", return_value=(100, 200)):
            count = common.tap_claims(bot, ("Example/button",), max_taps=6)

        self.assertEqual(count, 1)
        bot.tap.assert_called_once_with(100, 200, delay=2)

    def test_claimable_aliases_at_same_control_are_tapped_once(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(common, "find", return_value=(100, 200)):
            count = common.tap_claims(
                bot, ("Common/button_claimable", "EmpireDepot/button_claimable"),
                initial_wait_attempts=0,
            )

        self.assertEqual(1, count)
        bot.tap.assert_called_once_with(100, 200, delay=2)

    def test_sparkle_fallback_only_uses_lower_non_purchase_area(self):
        before = np.zeros((704, 396, 3), dtype=np.uint8)
        after = before.copy()
        after[300:306, 120:126] = 255       # safe lower-content sparkle
        after[30:36, 250:256] = 255         # top carousel/resource bar
        after[660:666, 200:206] = 255       # bottom purchase strip

        point = common.sparkle_point(before, after)

        self.assertIsNotNone(point)
        self.assertLess(abs(point[0] - 123), 5)
        self.assertLess(abs(point[1] - 303), 5)

    def test_claim_helper_waits_for_delayed_button_content(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(common, "find",
                               side_effect=(None, None, (100, 200), None)):
            count = common.tap_claims(bot, ("Example/button",),
                                      initial_wait_attempts=5)

        self.assertEqual(count, 1)
        self.assertEqual(bot.sleep.call_count, 2)
        bot.tap.assert_called_once_with(100, 200, delay=2)

    def test_fixed_claim_does_not_count_an_unverified_tap(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_named(_bot, name, *_args, **_kwargs):
            return None if name == "LoginGifts/congratulations" else (100, 200)

        with mock.patch.object(common, "find", side_effect=find_named):
            report = common.claim_fixed_controls(
                bot, ("Example/button",), initial_wait_attempts=0)

        self.assertEqual(1, report.attempted)
        self.assertEqual(0, report.verified)

    def test_fixed_claim_counts_congratulations_as_verified(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_named(_bot, name, *_args, **_kwargs):
            if name == "LoginGifts/congratulations":
                return (198, 320)
            return (100, 200)

        with mock.patch.object(common, "find", side_effect=find_named):
            report = common.claim_fixed_controls(
                bot, ("Example/button",), initial_wait_attempts=0)

        self.assertEqual(1, report.attempted)
        self.assertEqual(1, report.verified)
        bot.back.assert_called_once_with(delay=0.8)

    def test_valuable_navigation_is_not_registered_as_claim_control(self):
        specs = {spec.task.key: spec for spec in valuable_event.SPECS}
        refining = specs["gift_refining_stone_sprint"]
        weekly = specs["gift_super_value_weekly_card"]
        self.assertEqual(("SpeedupSprint/subtab_package",),
                         refining.navigation)
        self.assertEqual(("SpeedupSprint/button_free",), refining.claims)
        self.assertEqual(("SuperValueWeeklyCard/button_scores",),
                         weekly.navigation)
        self.assertEqual((), weekly.claims)

    def test_event_center_uses_fixed_launcher_and_inner_title(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        def find_named(_bot, name, *_args, **_kwargs):
            if name == "EventCenter/launcher_side":
                return (360, 310)
            if name == "EventCenter/title":
                return (200, 25)
            return None

        with (mock.patch.object(common, "return_home", return_value=True),
              mock.patch.object(common, "find", side_effect=find_named)):
            opened = common.open_event_center(bot)

        self.assertIs(opened, screen)
        bot.tap.assert_called_once_with(360, 290, delay=1)

    def test_lobby_navigation_failure_yields_instead_of_finishing_boundary(self):
        bot = mock.Mock()
        with mock.patch.object(gift_claims.lobby, "return_home", return_value=False):
            with self.assertRaises(YieldToBoss):
                gift_claims.lobby.open_next(bot, gift_claims.lobby.BOTTOM, [])


if __name__ == "__main__":
    unittest.main()
