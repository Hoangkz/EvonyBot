import tempfile
import unittest
from importlib import import_module
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

from bot.activities import gift_claims
from bot.activities.gift_claims import common, lobby, valuable_event
from bot.activities.gift_claims import registry
from bot.activities.gift_claims.screens import GiftScreen
from bot.daily_reset import done_today
from database import Database


class GiftClaimRegistryTests(unittest.TestCase):
    def test_child_task_persists_its_own_key_only_after_success(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        successful = common.GiftTask("gift_test_child", "Test child",
                                     lambda _bot: True)
        failed = common.GiftTask("gift_test_failed", "Test failed",
                                 lambda _bot: False)

        self.assertTrue(successful.run(bot))
        self.assertFalse(failed.run(bot))

        bot.mark_daily_done.assert_called_once_with("gift_test_child")

    def test_each_event_center_package_exposes_a_run_entry_point(self):
        names = (
            "blessing_of_pallas", "dragon_battle", "dwarfs_treasure",
            "grace_of_star_trail", "hypnos_dream", "poseidons_day",
            "precious_blazon_exchange", "revelation_of_horus",
            "sealed_imperial_treasury",
        )
        for name in names:
            with self.subTest(event=name):
                module = import_module(
                    f"bot.activities.gift_claims.event_center.{name}")
                self.assertTrue(callable(module.run))

    def test_all_declared_templates_are_readable_images(self):
        folder = Path(__file__).parents[2] / "Images" / "GiftClaims"
        expected = {
            "EventCenter/launcher.png", "EventCenter/launcher_side.png",
            "Common/button_close_x.png", "Common/button_daily_free_text.png",
            "Common/button_claim_text.png", "Common/button_claimable.png",
            "Common/button_claimable_alt.png", "Common/button_free_text.png",
            "Common/button_claim_all_text.png",
            "BackToTerritory/title.png", "BackToTerritory/button_claim.png",
            "FollowUs/title.png",
            "FollowUs/facebook_icon.png",
            "GeneralVault/tab.png", "GeneralVault/button_daily_free.png",
            "DragonBattle/title.png",
            "Lobby/notification_dot.png", "Lobby/notification_dot_bottom.png",
            "ValuableEvent/title.png", "ValuableEvent/launcher.png",
            "ValuableEvent/notification_dot.png", "SuperValueReturn/title.png",
            "SuperValueReturn/notification_dot.png", "EventCenter/notification_dot.png",
            "BacchusTavern/title.png", "LoginGifts/title.png",
            "DragonBattle/reward.png", "DragonBattle/list_row.png",
            "GraceOfStarTrail/title.png", "GraceOfStarTrail/list_row.png",
            "GraceOfStarTrail/button_star_trail_gift.png",
            "GraceOfStarTrail/button_star_trail_gift_alt.png",
            "GraceOfStarTrail/button_star_trail_gift_current.png",
            "GraceOfStarTrail/button_claim.png", "LimitedOffer/tab.png",
            "LimitedOffer/button_free.png", "SpeedupSprint/tab.png",
            "ResourceConsumptionSprint/tab.png",
            "ResourceConsumptionSprint/button_free.png",
            "AncientDynastyTreasury/tab.png",
            "AncientDynastyTreasury/button_daily_free.png",
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
            "EmpireDepot/tab.png", "EmpireDepot/launcher.png",
            "EmpireDepot/button_claimable.png",
            "LuckyRaffle/tab.png", "LuckyRaffle/button_claimable.png",
            "CityGrowthPlan/tab.png", "CityGrowthPlan/button_claim_all.png",
            "CityGrowthPlan/detail_popup.png", "CityGrowthPlan/claimed.png",
            "EventCenter/title.png",
            "EventCenter/facebook_activity.png",
            "PreciousBlazonExchange/title.png",
            "PreciousBlazonExchange/button_rewards.png",
            "DwarfsTreasure/title.png", "DwarfsTreasure/list_row.png",
            "DwarfsTreasure/button_daily_free.png",
            "HypnosDream/title.png",
            "HypnosDream/button_rewards.png",
            "PoseidonsDay/title.png",
            "PoseidonsDay/tab_ocean_offering.png",
            "PoseidonsDay/button_daily_free.png",
            "RevelationOfHorus/title.png",
            "SealedImperialTreasury/title.png",
        }
        actual = {path.relative_to(folder).as_posix() for path in folder.rglob("*.png")}
        self.assertEqual(expected, actual)
        self.assertTrue(all(cv2.imread(str(folder / name)) is not None
                            for name in expected))

    def test_combined_gift_task_is_saved_only_after_registry_locations_finish(self):
        done = set()
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add
        task = common.GiftTask("gift_example", "Example", lambda _bot: True)
        location = registry.ClaimLocation(registry.VALUABLE_EVENT, task)

        def pending(_bot, zone=None):
            if "gift_example" in done:
                return ()
            return (location,) if zone in (None, registry.VALUABLE_EVENT) else ()

        with mock.patch.object(registry, "pending", side_effect=pending):
            self.assertTrue(gift_claims.run(bot))

        self.assertEqual(done, {"gift_example", gift_claims.KEY})

    def test_pending_location_writes_scan_checkpoint_not_aggregate(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        task = common.GiftTask("gift_example", "Example", lambda _bot: False)
        location = registry.ClaimLocation(registry.VALUABLE_EVENT, task)
        with mock.patch.object(registry, "pending", return_value=(location,)):
            self.assertFalse(gift_claims.run(bot))

        bot.mark_daily_done.assert_called_once_with(gift_claims.SCAN_KEYS[0])
        self.assertNotIn(mock.call(gift_claims.KEY),
                         bot.mark_daily_done.call_args_list)

    def test_database_keeps_individual_gift_checkpoint_after_reopen(self):
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
        self.assertIn("gift_limited_offer", done)

    def test_gift_checkpoint_expires_at_the_server_reset_not_midnight(self):
        # The exact case from the flow contract: the 14/10 completion is no
        # longer current at 15:00 on 15/10 because the 14:00 server reset has
        # already happened.
        from datetime import datetime

        self.assertFalse(done_today("2026-10-14T21:05:00", "14:00",
                                    datetime(2026, 10, 15, 15, 0)))
        self.assertTrue(done_today("2026-10-14T21:05:00", "14:00",
                                   datetime(2026, 10, 15, 13, 59)))

    def test_registry_is_the_full_inventory_not_a_red_badge(self):
        keys = {item.task.key for item in registry.locations()}
        self.assertIn("gift_limited_offer", keys)
        self.assertIn("gift_resource_consumption_sprint", keys)
        self.assertIn("gift_ancient_dynasty_treasury", keys)
        self.assertIn("gift_login_gifts", keys)
        self.assertIn("gift_precious_blazon_exchange", keys)
        self.assertIn("gift_dwarfs_treasure", keys)
        self.assertIn("gift_blessing_of_pallas", keys)
        self.assertIn("gift_poseidons_day", keys)

        bot = mock.Mock()
        bot.is_daily_done.side_effect = {"gift_limited_offer"}.__contains__
        pending_keys = {item.task.key for item in registry.pending(bot)}
        self.assertNotIn("gift_limited_offer", pending_keys)
        self.assertIn("gift_login_gifts", pending_keys)

    def test_region_1_contains_super_value_return_and_no_event_center_tasks(self):
        region_1 = {item.task.key for item in registry.locations(registry.REGION_1)}
        region_2 = {item.task.key for item in registry.locations(registry.REGION_2)}

        self.assertTrue({"gift_empire_depot", "gift_lucky_raffle",
                         "gift_city_growth_plan", "gift_login_gifts"} <= region_1)
        self.assertIn("gift_resource_consumption_sprint", region_1)
        self.assertIn("gift_grace_of_star_trail", region_2)
        self.assertTrue(region_1.isdisjoint(region_2))

    def test_run_region_executes_only_requested_region(self):
        done = set()
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add
        region_1_task = common.GiftTask(
            "gift_region_1_test", "Region 1 test", lambda _bot: True)
        region_2_task = common.GiftTask(
            "gift_region_2_test", "Region 2 test", lambda _bot: True)
        locations = (
            registry.ClaimLocation(registry.REGION_1, region_1_task),
            registry.ClaimLocation(registry.REGION_2, region_2_task),
        )

        def pending(_bot, zone=None):
            return tuple(item for item in locations
                         if item.zone == zone and item.task.key not in done)

        with mock.patch.object(registry, "pending", side_effect=pending):
            self.assertTrue(gift_claims.run_region(bot, registry.REGION_2))

        self.assertIn("gift_region_2_test", done)
        self.assertNotIn("gift_region_1_test", done)

    def test_gift_region_keeps_join_boss_deadline_active(self):
        bot = mock.Mock()
        bot._boss_interrupt_enabled = True
        bot._deadline = 123.0
        observed = []

        def pending(_bot, _zone=None):
            observed.append((_bot._boss_interrupt_enabled, _bot._deadline))
            return ()

        with mock.patch.object(registry, "pending", side_effect=pending):
            self.assertTrue(gift_claims.run_region(bot, registry.REGION_2))

        self.assertTrue(observed)
        self.assertTrue(all(state == (True, 123.0) for state in observed))
        self.assertIs(bot._boss_interrupt_enabled, True)
        self.assertEqual(123.0, bot._deadline)

    def test_clean_region_scan_does_not_finish_missing_labels_before_three_passes(self):
        done = set()
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add
        with (mock.patch.object(lobby, "open_named", return_value=True),
              mock.patch.object(valuable_event, "run_opened",
                                return_value=({}, True)) as valuable_scan,
              mock.patch.object(gift_claims.super_value_return, "run_opened",
                                return_value=({}, True)) as super_scan):
            self.assertFalse(gift_claims.run_region(bot, registry.REGION_1))

        self.assertEqual(set(), done)
        valuable_scan.assert_called_once()
        super_scan.assert_called_once()

    def test_clean_super_value_return_keeps_unseen_children_pending(self):
        done = {task.key for task in registry.VALUABLE_EVENT_TASKS}
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add
        with (mock.patch.object(lobby, "open_named", return_value=True) as opener,
              mock.patch.object(gift_claims.super_value_return, "run_opened",
                                return_value=({}, True)) as super_scan):
            self.assertFalse(gift_claims.run_region(bot, registry.REGION_1))

        self.assertFalse({task.key for task in registry.SUPER_VALUE_RETURN_TASKS}
                         <= done)
        opener.assert_called_once_with(bot, GiftScreen.SUPER_VALUE_RETURN)
        super_scan.assert_called_once()

    def test_three_complete_empty_scans_finish_remaining_keys_and_aggregate(self):
        done = set()
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add
        task = common.GiftTask("gift_missing_event", "Missing Event",
                               lambda _bot: False)
        location = registry.ClaimLocation(registry.REGION_1, task)

        def pending(_bot, zone=None):
            if task.key in done:
                return ()
            return (location,) if zone in (None, registry.REGION_1) else ()

        with (mock.patch.object(registry, "pending", side_effect=pending),
              mock.patch.object(gift_claims, "_run_region_once",
                                return_value=(False, True))):
            self.assertFalse(gift_claims.run(bot))
            self.assertFalse(gift_claims.run(bot))
            self.assertTrue(gift_claims.run(bot))

        self.assertTrue(set(gift_claims.SCAN_KEYS) <= done)
        self.assertIn(task.key, done)
        self.assertIn(gift_claims.KEY, done)

    def test_three_scan_checkpoints_and_aggregate_persist_in_sqlite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gift-three-scans.db"
            db = Database(path)
            serial = "test-device"
            db.add_device(serial)
            bot = mock.Mock()
            bot.is_daily_done.side_effect = lambda key: done_today(
                db.daily_done(serial).get(key), db.server_time())
            bot.mark_daily_done.side_effect = lambda key: \
                db.mark_daily_task_done(serial, key)
            with mock.patch.object(gift_claims, "_run_region_once",
                                   return_value=(False, True)):
                self.assertFalse(gift_claims.run(bot))
                self.assertFalse(gift_claims.run(bot))
                self.assertTrue(gift_claims.run(bot))
            db.close()

            reopened = Database(path)
            try:
                saved = reopened.daily_done(serial)
            finally:
                reopened.close()

        self.assertTrue(set(gift_claims.SCAN_KEYS) <= saved.keys())
        self.assertIn(gift_claims.KEY, saved)
        self.assertTrue({item.task.key for item in registry.locations()}
                        <= saved.keys())

    def test_day_without_any_gift_parent_finishes_after_three_empty_scans(self):
        done = set()
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add
        with (mock.patch.object(lobby, "open_named", return_value=False),
              mock.patch.object(gift_claims.event_center,
                                "open_event_center", return_value=None)):
            self.assertFalse(gift_claims.run(bot))
            self.assertFalse(gift_claims.run(bot))
            self.assertTrue(gift_claims.run(bot))

        self.assertTrue(set(gift_claims.SCAN_KEYS) <= done)
        self.assertTrue({item.task.key for item in registry.locations()}
                        <= done)
        self.assertIn(gift_claims.KEY, done)

    def test_named_parent_uses_fixed_launcher_not_a_notification_badge(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(common, "return_home", return_value=True),
              mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "find", return_value=(259, 591)),
              mock.patch.object(lobby, "identify",
                                side_effect=(None, GiftScreen.VALUABLE_EVENT)),
              mock.patch.object(lobby, "open_next") as open_next):
            self.assertTrue(lobby.open_named(bot, GiftScreen.VALUABLE_EVENT))

        bot.tap.assert_called_once_with(259, 571, delay=1)
        bot.tap_percent.assert_not_called()
        open_next.assert_not_called()

    def test_super_value_return_uses_empire_depot_city_launcher(self):
        name, region = lobby.FIXED_PARENT_LAUNCHERS[
            GiftScreen.SUPER_VALUE_RETURN]
        self.assertEqual("EmpireDepot/launcher", name)
        self.assertEqual((0, 70, 25, 95), region)

    def test_claim_template_is_never_tapped_twice_on_an_unchanged_page(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(common, "find", return_value=(100, 200)):
            count = common.tap_claims(bot, ("Example/button",), max_taps=6)

        self.assertEqual(count, 1)
        bot.tap.assert_called_once_with(100, 200, delay=1)

    def test_claimable_aliases_at_same_control_are_tapped_once(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(common, "find", return_value=(100, 200)):
            count = common.tap_claims(
                bot, ("Common/button_claimable", "EmpireDepot/button_claimable"),
                initial_wait_attempts=0,
            )

        self.assertEqual(1, count)
        bot.tap.assert_called_once_with(100, 200, delay=1)

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

    def test_sparkle_check_stops_after_four_unverified_samples(self):
        bot = mock.Mock()
        with mock.patch.object(common, "claim_sparkle",
                               return_value=common.ClaimReport()) as claim:
            report = common.claim_sparkles(bot, attempts=4)

        self.assertEqual(common.ClaimReport(), report)
        self.assertEqual(4, claim.call_count)

    def test_x_control_uses_back_instead_of_tapping_x(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with mock.patch.object(common, "find", return_value=(13, 13)):
            self.assertTrue(common.back_if_close_x(bot))

        bot.back.assert_called_once_with(delay=0.8)
        bot.tap.assert_not_called()

    def test_claim_helper_waits_for_delayed_button_content(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(common, "find",
                               side_effect=(None, None, (100, 200), None)):
            count = common.tap_claims(bot, ("Example/button",),
                                      initial_wait_attempts=5)

        self.assertEqual(count, 1)
        self.assertEqual(bot.sleep.call_count, 2)
        bot.tap.assert_called_once_with(100, 200, delay=1)

    def test_fixed_claim_does_not_count_an_unverified_tap(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_named(_bot, name, *_args, **_kwargs):
            return None if name == "LoginGifts/congratulations" else (100, 200)

        with (mock.patch.object(common, "find", side_effect=find_named),
              mock.patch.object(common, "find_all", return_value=[(100, 200)])):
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

        with (mock.patch.object(common, "find", side_effect=find_named),
              mock.patch.object(common, "find_all",
                                side_effect=([(100, 200)], []))):
            report = common.claim_fixed_controls(
                bot, ("Example/button",), initial_wait_attempts=0)

        self.assertEqual(1, report.attempted)
        self.assertEqual(1, report.verified)
        bot.back.assert_called_once_with(delay=0.8)

    def test_fixed_claim_taps_every_identical_visible_button(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        first, second = (100, 200), (100, 300)
        with (mock.patch.object(common, "find", return_value=None),
              mock.patch.object(common, "find_all", side_effect=(
                  [first, second], [second], [second], [], []))):
            report = common.claim_fixed_controls(
                bot, ("Common/button_claim_text",), max_taps=6,
                initial_wait_attempts=0)

        self.assertEqual((2, 2), (report.attempted, report.verified))
        self.assertEqual([mock.call(*first, delay=1), mock.call(*second, delay=1)],
                         bot.tap.call_args_list)

    def test_stubborn_control_does_not_block_another_claim(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        stuck, claim = (100, 200), (100, 300)
        with (mock.patch.object(common, "find", return_value=None),
              mock.patch.object(common, "find_all", side_effect=(
                  [stuck, claim], [stuck, claim],
                  [stuck, claim], [stuck], [stuck]))):
            report = common.claim_fixed_controls(
                bot, ("Common/button_free_text",), max_taps=6,
                initial_wait_attempts=0)

        self.assertEqual((2, 1), (report.attempted, report.verified))
        self.assertEqual([mock.call(*stuck, delay=1), mock.call(*claim, delay=1)],
                         bot.tap.call_args_list)

    def test_valuable_navigation_is_not_registered_as_claim_control(self):
        specs = {spec.task.key: spec for spec in valuable_event.SPECS}
        resource = specs["gift_resource_consumption_sprint"]
        ancient = specs["gift_ancient_dynasty_treasury"]
        refining = specs["gift_refining_stone_sprint"]
        weekly = specs["gift_super_value_weekly_card"]
        self.assertEqual(("SpeedupSprint/subtab_package",),
                         refining.navigation)
        self.assertEqual(("SpeedupSprint/button_free",), refining.claims)
        self.assertEqual(("ResourceConsumptionSprint/button_free",),
                         resource.claims)
        self.assertEqual(("AncientDynastyTreasury/button_daily_free",),
                         ancient.navigation)
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

    def test_lobby_navigation_failure_stays_pending_without_yielding_to_boss(self):
        bot = mock.Mock()
        with mock.patch.object(gift_claims.lobby, "return_home", return_value=False):
            self.assertIsNone(
                gift_claims.lobby.open_next(bot, gift_claims.lobby.BOTTOM, []))


if __name__ == "__main__":
    unittest.main()
