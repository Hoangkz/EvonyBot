"""
Flow test Daily Activities / Troop Training (bot/activities/daily_activities/troop_training/), phiên bản giao diện
mới: màn chính -> Quests -> tab Activity -> Claim All -> dòng "Train 300 troops in the Main City" đang là Claim
(đã làm xong) -> xong, không bấm Go.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (01..04 chép từ
tests/daily_activities/screens/).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities import troop_training
from bot.activities.daily_activities.constants import TASK_DONE
from tests.daily_activities import CLAIM_ALL_ONCE, TO_ACTIVITY, open_task_of
from tests.flow import Step, end, run_flow

SCREENS = Path(__file__).parent / "screens"


class TroopTrainingFlow(unittest.TestCase):
    def test_row_claimed_is_done(self):
        flow = [
            *TO_ACTIVITY, *CLAIM_ALL_ONCE,
            Step("03_activity_top.png", end(result=TASK_DONE)),
        ]
        run_flow(self, open_task_of(troop_training.TASK), SCREENS, flow, {})


if __name__ == "__main__":
    unittest.main()
