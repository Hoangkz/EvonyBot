"""
Flow test Daily Activities / Resource Tax (bot/activities/daily_activities/resource_tax/), phiên bản
giao diện mới: màn chính -> Quests -> tab Activity -> Claim All -> cuộn -> dòng "Tax on resources for
N time(s)" -> Go. Phần sau Go (Chợ -> Tax): TODO khi có ảnh.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (01..04 chép từ
tests/daily_activities/screens/).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities import resource_tax
from bot.activities.daily_activities.constants import GO_BUTTON, TASK_OPENED
from tests.daily_activities import CLAIM_ALL_ONCE, SCROLL, TO_ACTIVITY, open_task_of
from tests.flow import Step, end, run_flow, tap

SCREENS = Path(__file__).parent / "screens"
TAX_GO_Y = 568   # Go dưới tiêu đề Tax (y 526) trên 04_activity_scrolled — dòng thứ 2, không phải Go của Offer


class ResourceTaxFlow(unittest.TestCase):
    def test_open_task(self):
        flow = [
            *TO_ACTIVITY, *CLAIM_ALL_ONCE,
            Step("03_activity_top.png", SCROLL),
            Step("04_activity_scrolled.png", tap(GO_BUTTON)),
            Step("01_main.png", end(result=TASK_OPENED)),
        ]
        device = run_flow(self, open_task_of(resource_tax.TASK), SCREENS, flow, {})
        go = [e for _, e in device.events if e[0] == "tap"][-1]
        self.assertEqual(go[2], TAX_GO_Y)


if __name__ == "__main__":
    unittest.main()
