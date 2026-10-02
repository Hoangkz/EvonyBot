"""
run.py — nhiệm vụ City Tax (King's Path, Day 1): Day 1 -> tab phụ "City Tax" -> đọc số
đã làm ở dòng Go -> Go -> Chợ -> Tax -> thu thuế 4 loại tài nguyên cho đủ mục tiêu.
Flow chung tới Go: xem ../path_task.py.

Sau Go:
1. Chờ 10 s (về thành, Chợ ở giữa màn hình) -> bấm giữa màn hình -> chờ 5 s -> menu Chợ
   có icon "Tax" -> bấm. Không thấy icon thì bấm giữa thêm 1 lần.
2. Màn Tax: chia (mục tiêu - số đã làm) cho 4 dòng, dư dồn vào các dòng đầu
   (VD 110 -> 28, 28, 27, 27).
3. Mỗi dòng: bấm "Tax" -> popup -> gõ số lần vào ô số -> bấm "Tax" (quá lượt miễn phí thì
   tiêu kim cương) -> về màn Tax.
4. Thu đủ 4 dòng -> đánh dấu xong.
Không đọc được số đã làm ở dòng Go thì không thu (không biết số lần, tránh tiêu kim cương).
Bị ngắt giữa chừng: lượt sau đọc lại số đã làm ở dòng Go rồi chia lại phần còn thiếu.
"""
from ...common import EventState
from .. import path_task
from .constants import (
    CENTER,
    DAY,
    GO_EXTRA_WAIT,
    INPUT_DELETES,
    KEY,
    MENU_TRIES,
    MENU_WAIT,
    POPUP,
    POPUP_INPUT_OFFSET,
    POPUP_TAX,
    ROW_TAX,
    SCREEN_WAIT,
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
    """Chia `total` thành `parts` phần gần bằng nhau, dư dồn vào các phần đầu."""
    base, extra = divmod(max(0, total), parts)
    return [base + (1 if i < extra else 0) for i in range(parts)]


def _tax(bot, path, done, target):
    """Sau Go: mở màn Tax qua menu Chợ rồi thu thuế 4 dòng cho đủ mục tiêu."""
    if done is None:
        bot.log(f"{NAME}: progress unknown, not taxing")
        return
    counts = split_counts(target - done)
    bot.log(f"{NAME}: done {done}, target {target}, tax {counts}")
    bot.sleep(GO_EXTRA_WAIT)
    if not _open_tax(bot):
        return
    for row, count in enumerate(counts):
        if count == 0:
            continue
        if not _tax_row(bot, row, count):
            return
    bot.log(f"{NAME}: all rows taxed, done")
    bot.mark_daily_done(path.key)


def _open_tax(bot) -> bool:
    """Thành (Chợ ở giữa) -> bấm giữa màn hình -> icon Tax -> màn Tax."""
    for _ in range(MENU_TRIES):
        bot.tap_percent(*CENTER, delay=MENU_WAIT)
        icon = bot.find(TAX_MENU)
        if icon is not None:
            bot.tap(*icon)
            if bot.wait_for(TAX_SCREEN, timeout=SCREEN_WAIT) is not None:
                return True
            bot.log(f"{NAME}: Tax screen not shown")
            return False
    bot.log(f"{NAME}: Tax icon not found")
    return False


def _tax_row(bot, row: int, count: int) -> bool:
    """Dòng thứ `row` (0..3) trên màn Tax: Tax -> popup -> gõ `count` -> Tax."""
    buttons = sorted(bot.find_all(ROW_TAX), key=lambda p: p[1])
    if len(buttons) < TAX_ROWS:
        bot.log(f"{NAME}: {len(buttons)} Tax buttons found, expected {TAX_ROWS}")
        return False
    bot.tap(*buttons[row])
    popup = bot.wait_for(POPUP, timeout=SCREEN_WAIT)
    if popup is None:
        bot.log(f"{NAME}: Tax popup not shown (row {row + 1})")
        return False
    dx, dy = POPUP_INPUT_OFFSET
    bot.tap(popup[0] + dx, popup[1] + dy, delay=1)
    for _ in range(INPUT_DELETES):
        bot.shell("input keyevent KEYCODE_DEL")
    bot.shell(f"input text {count}")
    bot.shell("input keyevent KEYCODE_ENTER")
    bot.sleep(1)
    button = bot.find(POPUP_TAX)
    if button is None:
        bot.log(f"{NAME}: popup Tax button not found (row {row + 1})")
        return False
    bot.log(f"{NAME}: row {row + 1} tax x{count}")
    bot.tap(*button, delay=TAX_WAIT)
    if bot.wait_for(TAX_SCREEN, timeout=SCREEN_WAIT) is None:
        bot.log(f"{NAME}: not back on Tax screen (row {row + 1})")
        return False
    return True


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB, after_go=_tax,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
