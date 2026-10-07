import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities import gift_claims
from bot.activities.gift_claims import common
from bot.activities.daily_activities.run import _run_gift_claims
from bot.worker.tasks import PRIORITY_FILE


class GiftClaimRegistryTests(unittest.TestCase):
    def test_all_declared_templates_are_readable_images(self):
        folder = Path(__file__).parents[2] / "Images" / "GiftClaims"
        expected = {
            "EventCenter/launcher.png", "EventCenter/launcher_side.png",
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
            "SpeedupSprint/subtab_package.png", "SpeedupSprint/button_free.png",
            "SuperBlazonSale/tab.png",
            "SuperBlazonSale/button_free.png", "SulisWishing/tab.png",
            "SuperValueWeeklyCard/tab.png", "SuperValueWeeklyCard/button_scores.png",
            "SuccessivePurchaseBenefits/tab.png",
            "SuccessivePurchaseBenefits/button_daily_free.png", "LoginGifts/tab.png",
            "LoginGifts/detail_popup.png",
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

    def test_every_module_has_unique_lowest_priority(self):
        data = json.loads(PRIORITY_FILE.read_text(encoding="utf-8"))
        daily = {item["key"]: item["priority"] for item in data["Daily Activities"]}
        keys = [task.key for task in gift_claims.TASKS]

        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), {key for key in daily if key.startswith("gift_")})
        self.assertTrue(all(daily[key] == -100 for key in keys))
        self.assertLess(-100, min(value for key, value in daily.items()
                                  if not key.startswith("gift_")))

    def test_each_gift_is_attempted_once_and_remembered_for_today(self):
        called = []
        tasks = (
            SimpleNamespace(key="gift_a", label="A", run=lambda bot: called.append("a") or True),
            SimpleNamespace(key="gift_b", label="B", run=lambda bot: called.append("b") or False),
        )
        done = {"gift_a"}
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = done.add

        with mock.patch.object(gift_claims, "TASKS", tasks):
            gift_claims.run(bot)

        self.assertEqual(called, ["b"])
        self.assertEqual(done, {"gift_a", "gift_b"})

    def test_post_daily_phase_runs_only_when_worker_enabled_it(self):
        bot = SimpleNamespace(post_daily_gifts_enabled=False)
        with mock.patch.object(gift_claims, "run") as run:
            _run_gift_claims(bot)
            run.assert_not_called()
            bot.post_daily_gifts_enabled = True
            _run_gift_claims(bot)
            run.assert_called_once_with(bot)

    def test_claim_template_is_never_tapped_twice_on_an_unchanged_page(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(common, "find", return_value=(100, 200)):
            count = common.tap_claims(bot, ("Example/button",), max_taps=6)

        self.assertEqual(count, 1)
        bot.tap.assert_called_once_with(100, 200, delay=2)

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


if __name__ == "__main__":
    unittest.main()
