"""
Flow test Daily Activities / Resource Collecting (bot/activities/daily_activities/resource_collecting/), phiên bản giao diện
mới: màn chính -> Quests -> tab Activity -> Claim All -> dòng "Research technologies for 1 time(s) in the City" đang là Claim
(đã làm xong) -> xong, không bấm Go.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (01..04 chép từ
tests/daily_activities/screens/).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities import resource_collecting
from bot.activities.daily_activities.constants import TASK_DONE
from tests.daily_activities import CLAIM_ALL_ONCE, TO_ACTIVITY, open_task_of
from tests.flow import Step, end, run_flow

SCREENS = Path(__file__).parent / "screens"


class ResourceCollectingFlow(unittest.TestCase):
    def test_row_claimed_is_done(self):
        flow = [
            *TO_ACTIVITY, *CLAIM_ALL_ONCE,
            Step("03_activity_top.png", end(result=TASK_DONE)),
        ]
        run_flow(self, open_task_of(resource_collecting.TASK), SCREENS, flow, {})

    def test_row_without_go_marked_done_target_zero(self):
        """open_task_or_finish: dòng đã Claim (không Go) -> đánh dấu xong hôm nay, mục tiêu 0."""
        from bot.activities.daily_activities.common import open_task_or_finish
        flow = [
            *TO_ACTIVITY, *CLAIM_ALL_ONCE,
            Step("03_activity_top.png", end(result=False)),
        ]
        device = run_flow(self, lambda bot, _s: open_task_or_finish(bot, resource_collecting.TASK),
                          SCREENS, flow, {})
        self.assertIn("Resource Collecting", device.daily_done)
        self.assertIn("daily_resource_collecting_reached_0", device.daily_done)


if __name__ == "__main__":
    unittest.main()
