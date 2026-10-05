"""
Flow test Daily Activities (bố cục giống tests/event/): mỗi nhiệm vụ một thư mục
tests/daily_activities/<nhiệm vụ>/ (test_flow.py + screens/), tên trùng thư mục code
bot/activities/daily_activities/<nhiệm vụ>/. screens/ của thư mục này: ảnh phần chung (màn chính,
Quests, danh sách Activity — phiên bản giao diện MỚI), được chép vào screens/ của từng nhiệm vụ.

Phần chung (common.open_task): màn chính (nút "•••") -> nút Quests góc dưới trái -> tab Activity ->
danh sách Activity (Claim All bấm trước) -> cuộn tìm tiêu đề dòng nhiệm vụ -> Go.
"""
from pathlib import Path

from bot.activities.daily_activities.common import open_task, task_cards, task_done_cards, task_titles
from bot.activities.daily_activities.constants import ACTIVITY_TAB, CLAIM_ALL, MAIN_MORE, OLD_MENU_ACTIVITY, QUESTS_BUTTON
from tests.flow import Step, back, end, swipe, tap, tap_at

SCROLL = swipe(70, 70, 55, 55)   # constants.LIST_SWIPE: cuộn danh sách Activity xuống
# Màn chính -> nút Quests -> popup Quests (đang ở Chapter Quests) -> tab Activity.
TO_ACTIVITY = [
    Step("01_main.png", tap(QUESTS_BUTTON)),
    Step("02_quests_chapter.png", tap(ACTIVITY_TAB)),
]
# Bảng Activity đã mở sẵn ngay lần nhìn đầu: Back đóng rồi mở lại từ màn chính (không cuộn lên).
def reopen(screen):
    return [Step(screen, back()), *TO_ACTIVITY]


# Đầu danh sách có Claim All: bấm; ảnh tĩnh nên Claim All vẫn còn -> coi là kẹt, bỏ qua lượt này.
CLAIM_ALL_ONCE = [
    Step("03_activity_top.png", tap(CLAIM_ALL)),
]


def open_task_of(task):
    """Hàm chạy cho run_flow: open_task với tiêu đề dòng (bản mới) và ảnh thẻ (bản cũ) của `task`."""
    return lambda bot, _settings: open_task(bot, task_titles(task), task_cards(task),
                                              done_cards=task_done_cards(task))


# Ảnh dùng chung, không chép: flow test đặt SCREENS = TESTS_DIR và ghi đường dẫn ảnh từ tests/ (tiền tố bên dưới).
TESTS_DIR = Path(__file__).resolve().parent.parent
DAILY = "daily_activities/screens/"           # ảnh phần chung Daily Activities
KP = "event/kings_path/screens/"              # màn sau Go dùng chung với King's Path
GATHER = "event/gather_troops/"               # màn Train / Speedup dùng chung với Gather Troops


def _hide_card(x0, y0):
    """Biến thể ảnh lưới 13 (tài khoản khác): che một thẻ chưa xong (thẻ đã xong nằm cuối lưới, không ở đây)."""
    def apply(bgr):
        bgr[y0:y0 + 140, x0:x0 + 114] = 30
        return bgr
    return apply


# Ảnh 13_old_activity_grid có thẻ Troop Healing / Trap Building chưa xong: test thẻ "Completed" của hai nhiệm vụ này
# thì che thẻ đó (run_flow(..., variants=OLD_GRID_VARIANTS)).
OLD_GRID_VARIANTS = {"no_heal": _hide_card(141, 408), "no_trap": _hide_card(265, 408)}


def old_grid_completed(done_screen: str, hide: str = ""):
    """Giao diện cũ: màn chính -> "•••" -> Activity -> lưới (thẻ "100%" đầu lưới bấm nhận, ảnh tĩnh -> bỏ qua) ->
    cuộn -> `done_screen` (ảnh trong DAILY): thẻ nhiệm vụ "Completed" -> open_task_or_finish return False, xong.
    `hide`: biến thể OLD_GRID_VARIANTS của ảnh lưới 13."""
    grid = f"{DAILY}13_old_activity_grid.png" + (f"?{hide}" if hide else "")
    return [
        Step(f"{DAILY}11_old_main.png", tap(MAIN_MORE)),
        Step(f"{DAILY}12_old_more_menu.png", tap(OLD_MENU_ACTIVITY)),
        Step(grid, tap_at(75, 325)),
        Step(grid, SCROLL),
        Step(f"{DAILY}{done_screen}", end(result=False)),
    ]
