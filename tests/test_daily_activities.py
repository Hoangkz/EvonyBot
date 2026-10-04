import importlib
import unittest
from unittest import mock

import numpy as np

from ui.tabs.daily_activities_tab import SUPPORTED_TASKS

_PKG = "bot.activities.daily_activities"
daily = importlib.import_module(f"{_PKG}.run")          # thứ tự nhiệm vụ, run()
common = importlib.import_module(f"{_PKG}.common")      # vòng lặp chung run_task
const = importlib.import_module(f"{_PKG}.constants")
collecting = importlib.import_module(f"{_PKG}.resource_collecting.run")
gathering = importlib.import_module(f"{_PKG}.resource_gathering.run")
gold_levy = importlib.import_module(f"{_PKG}.gold_levy.run")
troop_training = importlib.import_module(f"{_PKG}.troop_training.run")
trap = importlib.import_module(f"{_PKG}.trap_building.run")
black_market = importlib.import_module(f"{_PKG}.black_market.run")
enhancing = importlib.import_module(f"{_PKG}.general_enhancing.run")
wheel = importlib.import_module(f"{_PKG}.wheel_of_fortune.run")
patrol = importlib.import_module(f"{_PKG}.patrol.run")
compose = importlib.import_module(f"{_PKG}.material_composing.run")
monster = importlib.import_module(f"{_PKG}.monster_killing.run")


def _task(label):
    return next(task for task in daily.TASKS if task.label == label)


class DailyGoTests(unittest.TestCase):
    @mock.patch.object(common, "find_first")
    def test_task_label_matching_requests_top_left_position(self, find_first):
        find_first.return_value = (const.DONE, (10, 20))
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((720, 400, 3), dtype=np.uint8)

        self.assertTrue(common.run_task(bot, daily.TASKS[0]))

        self.assertEqual(find_first.call_args.kwargs["top_left"], const.ROW_ANCHORS)

    def test_go_is_searched_in_full_row_from_task_top(self):
        bot = mock.Mock()
        bot.crop.side_effect = lambda image, x, y, w, h: image[y:y + h, x:x + w]
        bot.find.return_value = (340, 48)
        screen = np.zeros((720, 400, 3), dtype=np.uint8)

        self.assertEqual(common.open_task_row(
            bot, screen, (50, 200), after_open_tap=None), const.ROW_OPENED)

        bot.crop.assert_called_once_with(screen, 0, 200, 400, 100)
        bot.tap.assert_called_once_with(340, 248, delay=4)
        bot.back.assert_not_called()

    def test_missing_go_marks_visible_task_row_complete_without_tapping(self):
        bot = mock.Mock()
        bot.crop.side_effect = lambda image, x, y, w, h: image[y:y + h, x:x + w]
        bot.find.return_value = None
        screen = np.zeros((720, 400, 3), dtype=np.uint8)

        self.assertEqual(common.open_task_row(
            bot, screen, (50, 200), after_open_tap=None), const.ROW_COMPLETE)

        bot.tap.assert_not_called()
        bot.back.assert_not_called()

    @mock.patch.object(common, "find_first")
    @mock.patch.object(common, "open_task_row", return_value=const.ROW_COMPLETE)
    def test_task_is_done_when_its_visible_row_has_no_go(self, open_row, find_first):
        find_first.return_value = (const.OPEN, (38, 347))
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        self.assertTrue(common.run_task(bot, daily.TASKS[0]))
        open_row.assert_called_once()

    @mock.patch.object(common, "delay")
    @mock.patch.object(common, "go_home")
    @mock.patch.object(common, "find_first", side_effect=[(None, None),
                                                          (const.DONE, (10, 20))])
    def test_unknown_transition_waits_instead_of_opening_quit(self, _first, home, wait):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        self.assertTrue(common.run_task(bot, daily.TASKS[0]))

        wait.assert_called_once_with(bot, 1)
        home.assert_not_called()

    def test_ui_order_matches_csharp_execution_order(self):
        self.assertEqual([key for key, _ in SUPPORTED_TASKS],
                         [task.label for task in daily.TASKS])

    @mock.patch.object(daily, "collect_activity_rewards")
    @mock.patch.object(daily, "run_task")
    def test_monster_is_retried_after_five_other_completed_tasks(self, run_task,
                                                                 collect_rewards):
        selected = daily.TASKS[:7]
        done = set()
        monster_calls = 0
        bot = mock.Mock()
        bot._daily_monster_deferred = False
        bot.is_daily_done.side_effect = lambda label: label in done
        bot.mark_daily_done.side_effect = done.add

        def execute(current_bot, task):
            nonlocal monster_calls
            if task.label == "Monster Killing":
                monster_calls += 1
                current_bot._daily_monster_deferred = monster_calls == 1
                return monster_calls > 1
            return True

        run_task.side_effect = execute
        settings = {task.label: True for task in selected}

        with mock.patch.object(daily, "TASKS", selected):
            daily.run(bot, settings)

        labels = [call.args[1].label for call in run_task.call_args_list]
        self.assertEqual(labels[:7], [selected[0].label]
                         + [task.label for task in selected[1:6]]
                         + [selected[0].label])
        self.assertEqual(monster_calls, 2)
        collect_rewards.assert_called_once_with(bot)

    @mock.patch.object(collecting, "open_daily_activity", return_value=True)
    def test_resource_collecting_returns_to_daily_after_collection(self, open_activity):
        bot = mock.Mock()
        collecting.handle(bot, "collection", (120, 300), None)
        bot.tap.assert_called_once_with(120, 300, delay=4)
        open_activity.assert_called_once_with(bot)

    def test_resource_collecting_does_not_treat_skill_book_shop_as_finish(self):
        task = _task("Resource Collecting")
        self.assertEqual(task.done, ())
        paths = [path for path, action in common.task_targets(task)
                 if action == const.DONE]
        self.assertFalse(any(path.endswith(("Finish.png", "Finish1.png"))
                             for path in paths))

    def test_resource_collecting_uses_claim_row_as_completion_proof(self):
        task = _task("Resource Collecting")
        self.assertEqual(task.actions, (
            ("Collection.png", "collection"),
            ("ClaimCollecting.png", const.VERIFY_COLLECTING),
            ("ActivitiesSourceCollecting.png", const.OPEN_COLLECTING_HELPER),
        ))

    @mock.patch.object(common, "open_task_row", return_value=const.ROW_COMPLETE)
    @mock.patch.object(common, "find_first",
                       return_value=(const.VERIFY_COLLECTING, (20, 300)))
    def test_resource_collecting_completes_only_when_claim_row_has_no_go(self,
                                                                         _first,
                                                                         open_row):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        task = _task("Resource Collecting")

        self.assertTrue(common.run_task(bot, task))
        open_row.assert_called_once_with(
            bot, bot.screenshot.return_value, (20, 300), None, task.folder,
            open_when_available=False)

    def test_resource_gathering_runs_immediately_after_offering(self):
        labels = [task.label for task in daily.TASKS]
        self.assertEqual(labels.index("Resource Gathering"), labels.index("Offering") + 1)

    @mock.patch.object(gathering, "open_daily_activity", return_value=True)
    def test_resource_gathering_uses_hand_then_reopens_quests(self, open_activity):
        bot = mock.Mock()
        self.assertFalse(gathering.handle(bot, "hand", (198, 269), None))
        bot.tap.assert_called_once_with(198, 269, delay=3)
        open_activity.assert_called_once_with(bot)

    def test_open_daily_activity_clicks_quest_icon_then_activity_and_verifies(self):
        outside = np.zeros((704, 396, 3), dtype=np.uint8)
        quests = np.ones((704, 396, 3), dtype=np.uint8)
        activity = np.full((704, 396, 3), 2, dtype=np.uint8)
        bot = mock.Mock()
        bot.screenshot.side_effect = [outside, quests, activity]

        def find(path, **kwargs):
            screen = kwargs["screen"]
            if screen is outside and path.endswith("QuestButtonCurrent.png"):
                return 22, 619
            if screen is quests and path.endswith("Click_Activities1.png"):
                return 321, 162
            if screen is activity and path.endswith("Click_ActivitiesLight.png"):
                return 45, 330
            return None

        bot.find.side_effect = find

        self.assertTrue(common.open_daily_activity(bot))
        self.assertEqual(bot.tap.call_args_list,
                         [mock.call(22, 619, delay=3), mock.call(321, 162, delay=2)])
        bot.tap_percent.assert_not_called()

    def test_open_daily_activity_closes_monster_search_drawer_once(self):
        search = np.zeros((704, 396, 3), dtype=np.uint8)
        outside = np.ones((704, 396, 3), dtype=np.uint8)
        quests = np.full((704, 396, 3), 2, dtype=np.uint8)
        activity = np.full((704, 396, 3), 3, dtype=np.uint8)
        bot = mock.Mock()
        bot.screenshot.side_effect = [search, outside, quests, activity]

        def find(path, **kwargs):
            screen = kwargs["screen"]
            if screen is search and path.endswith("BackToTerritoryCurrent.png"):
                return 357, 153
            if screen is outside and path.endswith("QuestButtonCurrent.png"):
                return 22, 619
            if screen is quests and path.endswith("Click_Activities1.png"):
                return 321, 162
            if screen is activity and path.endswith("Click_ActivitiesLight.png"):
                return 45, 330
            return None

        bot.find.side_effect = find

        self.assertTrue(common.open_daily_activity(bot, close_search=True))
        self.assertEqual(bot.tap.call_args_list,
                         [mock.call(357, 153, delay=4),
                          mock.call(22, 619, delay=3),
                          mock.call(321, 162, delay=2)])
        bot.back.assert_not_called()

    @mock.patch.object(common, "find_first", return_value=(const.DONE, (45, 395)))
    def test_rewards_claim_all_then_every_open_chest(self, first):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        popup_results = iter([None, None, (198, 215), None, (198, 215), None])
        claim_results = iter([(198, 638), None, None, None])
        bot.find.side_effect = lambda path, **_kwargs: (
            next(popup_results) if path.endswith("CongratulationsCurrent.png")
            else next(claim_results))
        bot.find_all.side_effect = [
            [(72, 295), (137, 295)], [(137, 295)], []]

        common.collect_activity_rewards(bot)

        self.assertEqual(bot.tap.call_args_list,
                         [mock.call(198, 638, delay=2),
                          mock.call(72, 295, delay=2),
                          mock.call(137, 295, delay=2)])
        self.assertEqual(bot.back.call_count, 2)
        bot.find_all.assert_any_call(
            "DailyActivites/CollectionActivities/OpenChestCurrent.png",
            threshold=0.72, screen=bot.screenshot.return_value,
            region=(8, 37, 92, 47))
        first.assert_called_once()

    def test_individual_task_does_not_claim_rewards_before_completion_check(self):
        paths = [path for path, _ in common.task_targets(daily.TASKS[0])]
        self.assertFalse(any(path.endswith("/Claim_All.png") for path in paths))

    def test_every_task_can_open_daily_from_the_current_quest_button(self):
        targets = common.task_targets(daily.TASKS[0])
        self.assertIn(("DailyActivites/UseAllActivities/QuestButtonDaily.png",
                       const.TAP), targets)
        self.assertIn(("DailyActivites/UseAllActivities/QuestButtonCity.png",
                       const.TAP), targets)

    def test_gold_levy_opens_radial_menu_entry_before_buttons(self):
        bot = mock.Mock()
        gold_levy.handle(bot, "levy", (188, 172), None)
        self.assertEqual(bot.tap.call_args_list, [
            mock.call(188, 172, delay=3), mock.call(280, 545, delay=3),
            mock.call(105, 545, delay=3),
        ])

    def test_training_swipes_the_current_troop_carousel_height(self):
        bot = mock.Mock()
        troop_training.handle(bot, "interface", (99, 661), None)
        bot.swipe_percent.assert_called_once_with(
            30, 65, 80, 65, duration=0.3, delay=1)

    @mock.patch.object(trap, "delay")
    @mock.patch.object(trap, "replace_text")
    def test_trap_interface_selects_tier_one_and_builds(self, replace_text, _delay):
        bot = mock.Mock()
        trap.handle(bot, "interface", (144, 618), None)
        self.assertEqual(bot.tap.call_args_list, [
            mock.call(95, 453, delay=1), mock.call(336, 582), mock.call(300, 660),
        ])
        replace_text.assert_called_once_with(bot, "150", 3)

    def test_trap_speedup_returns_to_activity_flow(self):
        bot = mock.Mock()
        trap.handle(bot, "speed", (294, 672), None)
        self.assertEqual(bot.tap.call_args_list,
                         [mock.call(294, 672, delay=2), mock.call(100, 670, delay=2)])
        bot.back.assert_called_once_with(delay=2)

    @mock.patch.object(black_market, "tap_first")
    def test_black_market_never_uses_gem_refresh_fallback(self, tap_first):
        bot = mock.Mock()
        self.assertTrue(black_market.handle(bot, "buy", (199, 22), None))
        self.assertIsNone(tap_first.call_args.kwargs.get("missing"))
        bot.back.assert_called_once_with(delay=2)

    @mock.patch.object(enhancing, "tap_first", return_value=True)
    def test_cultivate_exits_after_five_attempts(self, _tap_first):
        bot = mock.Mock()
        self.assertTrue(enhancing.handle(bot, "cultivate_loop", (199, 22), None))
        bot.tap.assert_called_once_with(110, 666)
        bot.back.assert_called_once_with(delay=2)

    @mock.patch.object(wheel, "tap_first", return_value=True)
    def test_wheel_exits_after_one_spin(self, _tap_first):
        bot = mock.Mock()
        self.assertTrue(wheel.handle(bot, "spin", (198, 22), None))
        bot.tap.assert_called_once_with(170, 550)
        bot.back.assert_called_once_with(delay=2)

    def test_patrol_uses_current_free_patrol_button_three_times(self):
        bot = mock.Mock()
        self.assertTrue(patrol.handle(bot, "patrol", (199, 22), None))
        self.assertEqual(bot.tap.call_args_list, [
            mock.call(169, 607, delay=1), mock.call(286, 668, delay=3),
            mock.call(108, 668, delay=3), mock.call(169, 607, delay=1),
            mock.call(286, 668, delay=3), mock.call(108, 668, delay=3),
            mock.call(169, 607, delay=1), mock.call(286, 668, delay=3),
        ])
        bot.back.assert_called_once_with(delay=2)

    def test_compose_exits_after_three_composes(self):
        bot = mock.Mock()
        bot.crop.return_value = np.zeros((666, 396, 3), dtype=np.uint8)
        bot.find.return_value = (140, 517)
        self.assertTrue(compose.handle(bot, "compose", (139, 8),
                                       np.zeros((704, 396, 3), dtype=np.uint8)))
        self.assertEqual(bot.tap.call_args_list, [
            mock.call(140, 525, delay=2), mock.call(100, 670, delay=2),
            mock.call(100, 670, delay=2), mock.call(100, 670, delay=2),
        ])
        bot.back.assert_called_once_with(delay=2)

    def test_general_enhancing_uses_csharp_after_go_position(self):
        self.assertEqual(_task("General Enhancing").after_open_tap, (30, 50))

    def test_monster_search_selects_monster_tab_before_search(self):
        bot = mock.Mock()
        bot._daily_monster_search_misses = 0
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.find.side_effect = [None, (100, 285)]
        monster.handle(bot, "tap_monster", (140, 525), None)
        self.assertEqual(bot.tap.call_args_list,
                         [mock.call(140, 525, delay=2), mock.call(200, 670, delay=4)])
        bot.back.assert_not_called()

    def test_monster_current_attack_card_is_pressed_immediately(self):
        bot = mock.Mock()
        bot._daily_monster_search_misses = 2
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.find.return_value = (197, 501)

        monster.handle(bot, "tap_monster", (140, 525), None)

        self.assertEqual(bot.tap.call_args_list, [
            mock.call(140, 525, delay=2), mock.call(200, 670, delay=4),
            mock.call(197, 501, delay=3),
        ])
        self.assertEqual(bot._daily_monster_search_misses, 0)
        self.assertEqual(bot.find.call_args.kwargs["region"], (20, 55, 80, 82))

    @mock.patch.object(monster, "delay")
    def test_monster_waits_on_stale_search_without_opening_quit(self, wait):
        bot = mock.Mock()
        bot._daily_monster_search_misses = 2
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.find.side_effect = [None, None]

        monster.handle(bot, "tap_monster", (140, 525), None)

        bot.back.assert_not_called()
        wait.assert_called_once_with(bot, 5)
        self.assertEqual(bot._daily_monster_search_misses, 0)

    @mock.patch.object(monster, "delay")
    def test_monster_never_backs_when_stale_search_drawer_is_closed(self, wait):
        bot = mock.Mock()
        bot._daily_monster_search_misses = 2
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.find.side_effect = [None, None]

        monster.handle(bot, "tap_monster", (140, 525), None)

        bot.back.assert_not_called()
        wait.assert_called_once_with(bot, 5)

    @mock.patch.object(monster, "dispatch_march", return_value=True)
    @mock.patch.object(monster, "open_daily_activity", return_value=True)
    def test_monster_checks_after_two_then_finishes_after_three_more(self,
                                                                    open_activity,
                                                                    dispatch):
        bot = mock.Mock()
        bot._daily_monster_marches = 0
        for _ in range(5):
            monster.handle(bot, "march", (196, 40), None)

        self.assertEqual(bot._daily_monster_marches, 5)
        self.assertEqual(open_activity.call_args_list,
                         [mock.call(bot, close_search=True),
                          mock.call(bot, close_search=True)])
        bot.tap_percent.assert_not_called()
        self.assertEqual(dispatch.call_count, 5)

    def test_current_monster_march_uses_full_tiers_and_verifies_transition(self):
        march_screen = np.zeros((704, 396, 3), dtype=np.uint8)
        outside = np.ones((704, 396, 3), dtype=np.uint8)
        bot = mock.Mock()
        bot.find.side_effect = [(137, 673), None, None]
        bot.screenshot.return_value = outside

        self.assertTrue(monster.dispatch_march(bot, march_screen))

        bot.tap.assert_called_once_with(137, 673, delay=3)
        self.assertEqual(bot.find.call_args_list[0].kwargs["region"], (5, 85, 60, 100))

    @mock.patch.object(monster, "open_daily_activity", return_value=False)
    @mock.patch.object(monster, "dispatch_march", return_value=True)
    def test_monster_stops_when_activity_cannot_be_opened(self, dispatch, open_activity):
        bot = mock.Mock()
        bot._daily_monster_marches = 1

        self.assertTrue(monster.handle(bot, "march", (196, 40), None))

        self.assertEqual(bot._daily_monster_marches, 2)
        open_activity.assert_called_once_with(bot, close_search=True)

    @mock.patch.object(common, "delay")
    @mock.patch.object(common, "claim_task_row", return_value=True)
    @mock.patch.object(common, "open_task_row",
                       side_effect=[const.ROW_COMPLETE, const.ROW_COMPLETE])
    @mock.patch.object(common, "find_first",
                       side_effect=[(const.OPEN_MONSTER_FIRST, (20, 300)),
                                    (const.OPEN_MONSTER_SECOND, (20, 400))])
    def test_monster_claims_first_row_then_defers_second(self, find_first,
                                                         open_row, claim_row, _delay):
        bot = mock.Mock()
        bot._daily_monster_first_claimed = False
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        self.assertFalse(common.run_task(bot, _task("Monster Killing")))

        self.assertEqual(bot._daily_monster_marches, 2)
        self.assertTrue(bot._daily_monster_first_claimed)
        self.assertTrue(bot._daily_monster_deferred)
        claim_row.assert_called_once()
        self.assertEqual(open_row.call_count, 1)

    def test_monster_images_keep_csharp_priority(self):
        task = _task("Monster Killing")
        self.assertEqual([name for name, _ in task.actions], [
            "March.png", "AttackMonster.png", "TapMonster.png", "FindMonster.png",
            "ActivitiesAttackMonsterNext.png", "ActivitiesAttackMonster.png",
        ])
        self.assertEqual(task.done, ())

    @mock.patch.object(common, "scroll_to_top")
    @mock.patch.object(common, "scroll_up")
    @mock.patch.object(common, "find_first")
    def test_repeated_stationary_scroll_returns_to_top(self, find_first, scroll_up,
                                                       scroll_to_top):
        find_first.side_effect = [
            (const.SCROLL, (45, 503)), (const.SCROLL, (45, 503)),
            (const.SCROLL, (45, 503)), (const.DONE, (20, 20)),
        ]
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        self.assertTrue(common.run_task(bot, daily.TASKS[0]))

        self.assertEqual(scroll_up.call_count, 2)
        scroll_to_top.assert_called_once_with(bot)

    def test_every_task_has_priority_key(self):
        import json
        from pathlib import Path
        data = json.loads((Path(__file__).parent.parent / "bot" / "worker" / "priority.json")
                          .read_text(encoding="utf-8"))
        keys = {t["key"] for t in data["Daily Activities"]}
        self.assertEqual([t.label for t in daily.TASKS if t.key not in keys], [])


if __name__ == "__main__":
    unittest.main()
