import importlib
import unittest
from unittest import mock

import numpy as np

from bot.activities.daily_activities.common import daily_job
from ui.tabs.daily_activities_tab import SUPPORTED_TASKS

_PKG = "bot.activities.daily_activities"
# Các việc Daily (bảng nhiệm vụ của worker: bot/worker/priority.py).
_ORDER = ("offering", "resource_tax", "gold_levy",
          "troop_training", "troop_healing", "trap_building", "alliance_donation", "alliance_help", "black_market",
          "general_enhancing", "wheel_of_fortune", "patrol", "material_composing")
TASKS = tuple(importlib.import_module(f"{_PKG}.{name}").TASK for name in _ORDER)
common = importlib.import_module(f"{_PKG}.common")
const = importlib.import_module(f"{_PKG}.constants")


class DailyTests(unittest.TestCase):
    def test_ui_tasks_match_execution_tasks(self):
        # UI đặt Offering lên đầu; thứ tự chạy vẫn theo TASKS.
        self.assertEqual(sorted(key for key, _ in SUPPORTED_TASKS),
                         sorted(task.label for task in TASKS))

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

    def test_rewards_on_old_ui_claims_100_cards_and_stops_without_reopening_the_list(self):
        """Giao diện cũ (lưới thẻ Activity): nhận thẻ 100% rồi dừng. Trước đây vòng lặp mở bảng lại (Back rồi mở) mãi."""
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        badges = iter([(17, 266), (140, 266), None])
        bot.find.side_effect = lambda path, **_kw: (
            (160, 13) if path == const.OLD_ACTIVITY_TITLE
            else next(badges) if path == const.OLD_DONE_BADGE else None)
        with mock.patch.object(common, "open_activity_list") as open_list:
            common.collect_activity_rewards(bot)
        open_list.assert_not_called()
        bot.back.assert_not_called()
        dx, dy = const.OLD_DONE_TAP
        self.assertEqual(bot.tap.call_args_list,
                         [mock.call(17 + dx, 266 + dy, delay=const.OLD_DONE_WAIT),
                          mock.call(140 + dx, 266 + dy, delay=const.OLD_DONE_WAIT)])

    def test_every_task_has_priority_key(self):
        from bot.worker.priority import DATA
        keys = {t["key"] for t in DATA["Daily Activities"]}
        self.assertEqual([t.label for t in TASKS if t.key not in keys], [])


if __name__ == "__main__":
    unittest.main()
