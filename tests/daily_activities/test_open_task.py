"""
Flow test phần chung (open_task) không gắn với nhiệm vụ nào; test mở từng nhiệm vụ nằm ở
tests/daily_activities/<nhiệm vụ>/test_flow.py.

Flow test phần chung của mọi nhiệm vụ Daily Activities, phiên bản giao diện MỚI
(bot/activities/daily_activities/common.py open_task):
màn chính (nút "•••") -> nút Quests góc dưới trái -> popup Quests (đang ở Chapter Quests) -> tab
Activity -> danh sách Activity: thấy Claim All thì bấm trước -> cuộn tìm tiêu đề dòng nhiệm vụ -> Go.

Ảnh: tests/daily_activities/screens/ (396x704)
- 01_main.png              màn chính
- 02_quests_chapter.png    popup Quests, tab Chapter Quests
- 03_activity_top.png      tab Activity, đầu danh sách (Research = Claim, Train = Claim, Gather = Go)
- 04_activity_scrolled.png đã cuộn (Offer Go, Tax Go, Levy ở sát đáy)
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities.common import open_task
from bot.activities.daily_activities.constants import (
    ACTIVITY_TAB,
    CLAIM_ALL,
    GO_BUTTON,
    QUESTS_BUTTON,
    TASK_NOT_FOUND,
    TASK_OPENED,
)
from bot.activities.daily_activities.offering.constants import FOLDER_PATH as OFFER
from tests.flow import Step, back, end, run_flow, swipe, tap

SCREENS = Path(__file__).parent / "screens"
SCROLL = swipe(70, 70, 55, 55)

# Màn chính -> Quests -> tab Activity.
TO_ACTIVITY = [
    Step("01_main.png", tap(QUESTS_BUTTON)),
    Step("02_quests_chapter.png", tap(ACTIVITY_TAB)),
]
# Đầu danh sách có Claim All: bấm; ảnh tĩnh nên Claim All vẫn còn -> coi là kẹt, bỏ qua lượt này.
CLAIM_ALL_ONCE = [
    Step("03_activity_top.png", tap(CLAIM_ALL)),
]


def _run(titles):
    return lambda bot, _settings: open_task(bot, titles)


class OpenTaskFlow(unittest.TestCase):
    def test_already_on_activity_list(self):
        """Đang ở sẵn danh sách Activity: không bấm Quests / tab; cuộn lên đầu trước (có thể đang ở giữa danh
        sách) rồi tìm."""
        flow = [
            Step("03_activity_top.png", swipe(55, 55, 70, 70)),
            *CLAIM_ALL_ONCE,
            Step("03_activity_top.png", SCROLL),
            Step("04_activity_scrolled.png", tap(GO_BUTTON)),
            Step("01_main.png", end(result=TASK_OPENED)),
        ]
        run_flow(self, _run(f"{OFFER}/Offer.png"), SCREENS, flow, {})

    def test_not_found_at_end_of_list(self):
        """Cuộn tới khi danh sách không đổi (hết), không thấy tiêu đề -> Back, mở lại bảng Activity từ màn
        chính, tìm thêm 1 lần (LIST_RETRIES) -> TASK_NOT_FOUND. Claim All đã kẹt ở lượt đầu: không bấm lại."""
        search = [
            Step("03_activity_top.png", SCROLL),
            Step("04_activity_scrolled.png", SCROLL),
        ]
        flow = [*TO_ACTIVITY, *CLAIM_ALL_ONCE, *search,
                Step("04_activity_scrolled.png", back()),
                *TO_ACTIVITY, *search,
                Step("04_activity_scrolled.png", end(result=TASK_NOT_FOUND))]
        run_flow(self, _run("DailyActivites/ActivitiesPatrol/ActivitiesPatrol.png"), SCREENS, flow, {})

if __name__ == "__main__":
    unittest.main()
