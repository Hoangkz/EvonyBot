"""
Flow test Daily Activities (bố cục giống tests/event/): mỗi nhiệm vụ một thư mục
tests/daily_activities/<nhiệm vụ>/ (test_flow.py + screens/), tên trùng thư mục code
bot/activities/daily_activities/<nhiệm vụ>/. screens/ của thư mục này: ảnh phần chung (màn chính,
Quests, danh sách Activity — phiên bản giao diện MỚI), được chép vào screens/ của từng nhiệm vụ.

Phần chung (common.open_task): màn chính (nút "•••") -> nút Quests góc dưới trái -> tab Activity ->
danh sách Activity (Claim All bấm trước) -> cuộn tìm tiêu đề dòng nhiệm vụ -> Go.
"""
from bot.activities.daily_activities.common import open_task, task_cards, task_done_cards, task_titles
from bot.activities.daily_activities.constants import ACTIVITY_TAB, CLAIM_ALL, QUESTS_BUTTON
from tests.flow import Step, swipe, tap

SCROLL = swipe(70, 70, 55, 55)   # constants.LIST_SWIPE: cuộn danh sách Activity xuống
# Bảng Activity đã mở sẵn: cuộn lên đầu trước (constants.LIST_SWIPE_UP); ảnh tĩnh -> 1 lần là thấy không đổi.
TO_TOP = swipe(55, 55, 70, 70)

# Màn chính -> nút Quests -> popup Quests (đang ở Chapter Quests) -> tab Activity.
TO_ACTIVITY = [
    Step("01_main.png", tap(QUESTS_BUTTON)),
    Step("02_quests_chapter.png", tap(ACTIVITY_TAB)),
]
# Đầu danh sách có Claim All: bấm; ảnh tĩnh nên Claim All vẫn còn -> coi là kẹt, bỏ qua lượt này.
CLAIM_ALL_ONCE = [
    Step("03_activity_top.png", tap(CLAIM_ALL)),
]


def open_task_of(task):
    """Hàm chạy cho run_flow: open_task với tiêu đề dòng (bản mới) và ảnh thẻ (bản cũ) của `task`."""
    return lambda bot, _settings: open_task(bot, task_titles(task), task_cards(task),
                                              done_cards=task_done_cards(task))
