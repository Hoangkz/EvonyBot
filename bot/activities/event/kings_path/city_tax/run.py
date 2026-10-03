"""
run.py — nhiệm vụ City Tax (King's Path, Day 1): Day 1 -> tab phụ "City Tax" -> đọc số
đã làm ở dòng Go -> Go -> Chợ -> Tax -> thu thuế 4 loại tài nguyên cho đủ mục tiêu.
Flow chung tới Go: xem ../path_task.py.

Sau Go:
1. Chờ 10 s (về thành, Chợ ở giữa màn hình) -> bấm giữa màn hình -> chờ 5 s -> menu Chợ
   có icon "Tax" -> bấm. Không thấy icon thì bấm giữa thêm 1 lần.
2. Màn Tax: chia (mục tiêu - số đã làm) cho 4 dòng, làm tròn lên cho nhanh, 4 dòng bằng nhau
   (VD đã làm 20, mục tiêu 110 -> còn 90 -> 90 / 4 = 22,5 -> mỗi dòng 23; dư vài lần không sao).
3. Mỗi dòng: bấm "Tax" -> popup -> bấm "−" tới khi ô số không đổi (= 1) -> bấm "+" (số lần - 1)
   lần -> bấm "Tax" (quá lượt miễn phí thì tiêu kim cương) -> về màn Tax.
4. Thu đủ 4 dòng -> đánh dấu xong.
Không đọc được số đã làm ở dòng Go thì không thu (không biết số lần, tránh tiêu kim cương).
Bị ngắt giữa chừng: lượt sau đọc lại số đã làm ở dòng Go rồi chia lại phần còn thiếu.
"""
import math

from ...city_building import MARKET
from ...common import EventState, mark_target_reached
from .. import path_task
from ..building import open_building
from .constants import (
    CLOSE_BACKS,
    CLOSE_CHECKS,
    CONGRATS_TAP,
    COUNT_BOX,
    DAY,
    KEY,
    MINUS_MAX_TAPS,
    MINUS_OFFSET,
    OKAY,
    PLUS_HALF,
    PLUS_OFFSET,
    POPUP,
    POPUP_PLUS,
    POPUP_TAX,
    ROW_NAMES,
    ROW_TAX,
    ROW_BUTTON_REGION,
    ROW_TAX_GEMS,
    ROW_TAX_GEMS_THRESHOLD,
    SAME_COUNT,
    SAME_STREAK,
    SCREEN_WAIT,
    STEP_WAIT,
    TAX_STEP_WAIT,
    TAXING_GIFT,
    TAB,
    TAB_INDEX,
    TAB_SELECTED,
    TAX_MENU,
    TAX_ROWS,
    TAX_SCREEN,
    TAX_WAIT,
)

NAME = "City Tax"


def split_counts(total: int, parts: int = TAX_ROWS) -> list[int]:
    """Chia `total` thành `parts` phần bằng nhau, làm tròn lên (tổng có thể dư < `parts`)."""
    return [math.ceil(max(0, total) / parts)] * parts


def _tax(bot, path, done, target):
    """Sau Go: mở màn Tax qua menu Chợ rồi thu thuế 4 dòng cho đủ mục tiêu."""
    if done is None:
        bot.log(f"{NAME}: progress unknown, not taxing")
        return
    counts = split_counts(target - done)
    bot.log(f"{NAME}: done {done}, target {target}, tax {counts}")
    if not open_building(bot, NAME, MARKET, TAX_MENU, TAX_SCREEN):
        return
    for row, count in enumerate(counts):
        if count == 0:
            continue
        result = _tax_row(bot, row, count)
        if result == path_task.AGAIN:
            return path_task.AGAIN
        if not result:
            return None
    bot.record(f"{NAME}: all rows taxed, done")
    mark_target_reached(bot, path.key)
    return None


def _tax_row(bot, row: int, count: int):
    """Dòng thứ `row` (0..3) trên màn Tax: Tax -> popup -> chọn `count` bằng "−" / "+" -> Tax.
    True: xong dòng; False: lỗi, dừng; path_task.AGAIN: popup không đóng, đã Back -> đi lại từ đầu."""
    tag = f"{NAME} [{row + 1}/{TAX_ROWS} {ROW_NAMES[row]}]"   # đang thu loại nào, trong mọi log
    buttons = _row_buttons(bot)
    if len(buttons) < TAX_ROWS:
        bot.record(f"{tag}: {len(buttons)} Tax buttons found after {SCREEN_WAIT} s, expected {TAX_ROWS}")
        return False
    bot.log(f"{tag}: open Tax popup (x{count})")
    bot.tap(*buttons[row], delay=TAX_STEP_WAIT)
    popup = bot.wait_for(POPUP, timeout=SCREEN_WAIT)
    if popup is None:
        bot.record(f"{tag}: Tax popup not shown")
        return False
    bot.sleep(TAX_STEP_WAIT)   # popup hiện hẳn rồi mới bấm "−"
    bot.log(f"{tag}: set count to {count} (− to 1, + x{count - 1})")
    if not _set_count(bot, popup, count):
        bot.record(f"{tag}: count still changing after {MINUS_MAX_TAPS} taps on −")
        return False
    bot.sleep(TAX_STEP_WAIT)   # ô số cập nhật xong rồi mới bấm Tax
    button = bot.find(POPUP_TAX)
    if button is None:
        bot.record(f"{tag}: popup Tax button not found")
        return False
    bot.log(f"{tag}: tap Tax x{count}")
    bot.tap(*button, delay=TAX_WAIT + TAX_STEP_WAIT)
    if not _popup_closed(bot, popup):
        # Không lưu done: Back ra rồi đi lại từ đầu (đọc lại tiến độ ở dòng Go, chia lại phần thiếu).
        bot.record(f"{tag}: Tax popup still open after {CLOSE_CHECKS} checks, back x{CLOSE_BACKS}, again")
        for _ in range(CLOSE_BACKS):
            bot.back(delay=1)
        return path_task.AGAIN
    if bot.wait_for(TAX_SCREEN, timeout=SCREEN_WAIT) is None:
        bot.record(f"{tag}: not back on Tax screen")
        return False
    bot.sleep(TAX_STEP_WAIT)   # màn Tax ổn định rồi mới tìm nút dòng sau
    bot.record(f"{tag}: taxed x{count}")
    return True


def _row_buttons(bot) -> list:
    """Nút Tax của các dòng (trên -> dưới), chờ tối đa SCREEN_WAIT giây tới khi popup đã đóng và
    thấy đủ TAX_ROWS nút (popup đang đóng dở che 2 dòng trên -> chỉ thấy 2 nút, bấm nhầm dòng)."""
    buttons = []
    for _ in range(SCREEN_WAIT):
        screen = bot.screenshot()
        if _dismiss_congrats(bot, screen):
            continue
        if bot.find(POPUP, screen=screen) is None:
            # Nút "Tax" (còn lượt miễn phí); không đủ thì tìm hình kim cương (hết lượt, "💎 2").
            buttons = bot.find_all(ROW_TAX, screen=screen)
            if len(buttons) < TAX_ROWS:
                buttons += bot.find_all(ROW_TAX_GEMS, threshold=ROW_TAX_GEMS_THRESHOLD,
                                        screen=screen, region=ROW_BUTTON_REGION)
            buttons = sorted(buttons, key=lambda p: p[1])
            if len(buttons) >= TAX_ROWS:
                return buttons
        bot.sleep(1)
    return buttons


def _dismiss_congrats(bot, screen) -> bool:
    """Băng "Congratulations! Taxing Gift" (icon hộp quà) trên `screen` -> bấm CONGRATS_TAP cho mất.
    True nếu đã bấm."""
    if bot.find(TAXING_GIFT, screen=screen) is None:
        return False
    bot.log(f"{NAME}: Taxing Gift banner, tap {CONGRATS_TAP}")
    bot.tap_percent(*CONGRATS_TAP, delay=1)
    return True


def _popup_closed(bot, popup) -> bool:
    """Sau khi bấm Tax trong popup: hộp xác nhận kim cương -> Okay; không thấy nút "+" của popup
    (quanh vị trí đo từ chữ "Cost" ở `popup`) = đã đóng. Còn thấy thì kiểm tra lại, tối đa
    CLOSE_CHECKS lần, mỗi lần chờ 1 s."""
    px, py = popup[0] + PLUS_OFFSET[0], popup[1] + PLUS_OFFSET[1]
    for _ in range(CLOSE_CHECKS):
        screen = bot.screenshot()
        # Hộp xác nhận tiêu kim cương (thu quá lượt miễn phí) -> Okay; xét trước "+" vì hộp làm tối nút.
        okay = bot.find(OKAY, screen=screen)
        if okay is not None:
            bot.log(f"{NAME}: confirm spending gems, Okay")
            bot.tap(*okay, delay=1)
            continue
        if _dismiss_congrats(bot, screen):
            return True   # băng chỉ hiện khi popup đã đóng (thu xong)
        area = bot.crop(screen, px - PLUS_HALF, py - PLUS_HALF, 2 * PLUS_HALF, 2 * PLUS_HALF)
        if bot.find(POPUP_PLUS, screen=area) is None:
            return True
        bot.sleep(1)
    return False


def _set_count(bot, popup, count: int) -> bool:
    """Popup Tax: bấm "−" tới khi ô số đứng yên SAME_STREAK lần bấm liên tiếp (= nhỏ nhất, 1), rồi
    "+" (`count` - 1) lần. False nếu bấm "−" MINUS_MAX_TAPS lần mà chưa đứng yên."""
    x, y = popup
    box = (x + COUNT_BOX[0], y + COUNT_BOX[1], COUNT_BOX[2], COUNT_BOX[3])
    before = bot.crop(bot.screenshot(), *box)
    same = 0   # số lần bấm "−" liên tiếp mà ô số không đổi
    for _ in range(MINUS_MAX_TAPS):
        bot.tap(x + MINUS_OFFSET[0], y + MINUS_OFFSET[1], delay=STEP_WAIT)
        now = bot.crop(bot.screenshot(), *box)
        same = same + 1 if bot.best_match(before, screen=now)[0] >= SAME_COUNT else 0
        if same >= SAME_STREAK:
            break
        before = now
    else:
        return False
    for _ in range(count - 1):
        bot.tap(x + PLUS_OFFSET[0], y + PLUS_OFFSET[1], delay=STEP_WAIT)
    return True


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB, after_go=_tax,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
