"""
run.py — nhiệm vụ Patrol (King's Path, Day 2): Day 2 -> tab phụ "Teamwork" -> dòng
"Patrol for" -> Go -> Tường thành -> Patrol -> patrol tới khi đủ mục tiêu hoặc hết lượt
trong ngày. Flow chung tới Go: xem ../path_task.py; mở Tường thành: ../building.py.

Sau Go (màn Patrol, mỗi bước chụp 1 ảnh):
1. Đã patrol lượt hiện tại (phần thưởng có dấu tích lớn) -> Refresh (ra bộ mới).
2. Ô "Select All" chưa tích -> bấm.
3. Đã tích -> bấm "Patrol" (tốn kim cương) -> +10 tiến độ, lưu lượt vào daily_done.
Dừng (Back) khi: số đã làm + 10 x số lượt lượt này >= mục tiêu -> đánh dấu xong; hoặc đủ
ROUNDS_PER_DAY lượt hôm nay / nút Refresh xám (Refreshes Today 10/10) / Refresh không ra bộ mới
-> đánh dấu xong hôm nay,
mai làm tiếp (tiến độ game lưu ở dòng Go, lượt sau đọc lại).
"""
import cv2
import numpy as np

from ...common import EventState
from .. import path_task
from ..building import open_building
from .constants import (
    BIG_TICK_AREA,
    BIG_TICKS,
    BUTTON_WAIT,
    DAY,
    ITEMS_BOX,
    KEY,
    MAX_STEPS,
    MENU_PATROL,
    PATROL_BUTTON,
    PATROL_CONFIRM_WAIT,
    PATROL_TITLE,
    PER_ROUND,
    REFRESH_BOX,
    REFRESH_BUTTON,
    REFRESH_GREEN,
    ROUNDS_PER_DAY,
    ROW_TITLE,
    SELECT_ALL_BOX,
    SELECT_ALL_OFF,
    SELECT_ALL_ON,
    SELECT_ALL_THRESHOLD,
    SELECT_ALL_TRIES,
    TAB,
    TAB_INDEX,
    TAB_SELECTED,
)

NAME = "Patrol"


def round_key(n: int) -> str:
    """Key daily_done: đã patrol lượt thứ `n` hôm nay."""
    return f"{KEY}_round_{n}"


def rounds_today(bot) -> int:
    return sum(1 for n in range(1, ROUNDS_PER_DAY + 1) if bot.is_daily_done(round_key(n)))


def _patrol(bot, path, done, target):
    """Sau Go: mở màn Patrol rồi patrol từng lượt (Select All -> Patrol -> Refresh)."""
    if not open_building(bot, NAME, MENU_PATROL, PATROL_TITLE):
        return
    progress = done or 0
    refreshed = False   # vừa bấm Refresh, chưa thấy bộ phần thưởng mới
    select_taps = 0     # số lần bấm Select All liên tiếp mà ô vẫn chưa tích
    for _ in range(MAX_STEPS):
        today = rounds_today(bot)
        if progress >= target:
            return _finish(bot, path, f"progress {progress} / {target}, done")
        if today >= ROUNDS_PER_DAY:
            return _finish(bot, path, f"{today} rounds today, done for today")
        screen = bot.screenshot()
        if bot.find(PATROL_TITLE, screen=screen) is None:
            bot.record(f"{NAME}: not on Patrol screen, stop")
            return
        if _claimed(screen):
            if not _refresh_enabled(screen):
                return _finish(bot, path, "Refresh disabled (out of refreshes), done for today")
            if refreshed:
                return _finish(bot, path, "Refresh gave no new rewards (out of refreshes), done for today")
            if not _tap(bot, screen, REFRESH_BUTTON, "round patrolled, Refresh"):
                return
            refreshed = True
            continue
        refreshed = False
        off = bot.find(SELECT_ALL_OFF, threshold=SELECT_ALL_THRESHOLD, screen=screen, center=False)
        if off is not None:
            if select_taps >= SELECT_ALL_TRIES:
                bot.record(f"{NAME}: Select All still unticked after {select_taps} taps, stop")
                return
            select_taps += 1
            bot.log(f"{NAME}: tick Select All")
            bot.tap(off[0] + SELECT_ALL_BOX[0], off[1] + SELECT_ALL_BOX[1], delay=1)
            continue
        select_taps = 0
        if bot.find(SELECT_ALL_ON, threshold=SELECT_ALL_THRESHOLD, screen=screen) is None:
            bot.record(f"{NAME}: Select All not found, stop")
            return
        if not _tap(bot, screen, PATROL_BUTTON, f"Patrol (round {today + 1} today)"):
            return
        if not _wait_claimed(bot):
            bot.record(f"{NAME}: patrol not confirmed after {PATROL_CONFIRM_WAIT} s, not counted, stop")
            return
        today += 1
        progress += PER_ROUND
        bot.record(f"{NAME}: round {today} today done (progress {progress} / {target})")
        bot.mark_daily_done(round_key(today))
    bot.record(f"{NAME}: too many steps, stop")


def _finish(bot, path, message: str):
    bot.log(f"{NAME}: {message}")
    bot.back(delay=1)
    bot.mark_daily_done(path.key)


def _claimed(screen) -> bool:
    """Phần thưởng đã có dấu tích lớn (vừa patrol): >= BIG_TICKS khối xanh lá >= BIG_TICK_AREA px."""
    x, y, w, h = ITEMS_BOX
    box = screen[y:y + h, x:x + w].astype(np.int16)
    blue, green, red = box[..., 0], box[..., 1], box[..., 2]
    mask = ((green > 150) & (red < 150) & (blue < 90)).astype(np.uint8)
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    return int((stats[1:, cv2.CC_STAT_AREA] >= BIG_TICK_AREA).sum()) >= BIG_TICKS


def _wait_claimed(bot) -> bool:
    """Sau khi bấm Patrol: chờ (tối đa PATROL_CONFIRM_WAIT giây) màn chuyển sang "đã patrol"."""
    for _ in range(PATROL_CONFIRM_WAIT):
        if _claimed(bot.screenshot()):
            return True
        bot.sleep(1)
    return False


def _refresh_enabled(screen) -> bool:
    """Nút Refresh còn xanh (bấm được); xám = hết lượt Refresh hôm nay."""
    x, y, w, h = REFRESH_BOX
    box = screen[y:y + h, x:x + w].astype(np.int16)
    return float((box[..., 1] - box[..., 2]).mean()) > REFRESH_GREEN


def _tap(bot, screen, template: str, message: str) -> bool:
    """Bấm nút `template` trên `screen` (ghi log `message`); không thấy nút -> log, False."""
    pos = bot.find(template, screen=screen)
    if pos is None:
        bot.record(f"{NAME}: {template} not found, stop")
        return False
    bot.log(f"{NAME}: {message}")
    bot.tap(*pos, delay=BUTTON_WAIT)
    return True


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB,
    row_title=ROW_TITLE, after_go=_patrol,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
