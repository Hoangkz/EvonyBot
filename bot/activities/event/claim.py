"""
claim.py — nhận thưởng của một event (Gather Troops, King's Path) theo chấm đỏ, chạy sau
khi event/run.py làm xong mọi nhiệm vụ.

Chỉ chạy khi event có ít nhất 1 nhiệm vụ đã xong hôm nay (daily_done), và mỗi khi số nhiệm
vụ xong tăng lên (lưu daily_done `<event>_claimed_<số nhiệm vụ xong>`): bị ngắt giữa chừng
thì lượt sau nhận lại.

Flow (sau khi mở event bằng run_task, giống nhiệm vụ):
1. Claim All -> bấm (run_task tự lo, xem common.priority_targets).
2. Chấm đỏ trên hàng tab phụ (tab chưa bấm trong Day đang mở) -> bấm tab đó.
3. Hết chấm ở tab phụ: chấm đỏ trên hàng tab Day (Day chưa bấm) -> bấm Day đó.
4. Hết chấm -> rương mốc (chỉ Gather Troops, CHESTS): đọc số đã làm ở "Progress:12 / 70"
   (OCR, số bên phải phải đúng mốc cuối), bấm mọi rương có mốc <= số đó mà chưa có dấu tích
   (VD 12 -> rương 5, 10); mỗi lần bấm chờ băng "Congratulations!" mất.
Mỗi tab chỉ bấm 1 lần mỗi lượt (chấm không mất cũng không kẹt).
"""
import cv2
import numpy as np

from ...ocr import read_milestone
from .common import EVENT_OPENED, STOP, EventState, claim_all, run_task
from .constants import (
    CHEST_HALF,
    CHEST_TICK,
    CHEST_TICK_THRESHOLD,
    CLAIM_ALL,
    CLAIM_MAX_STEPS,
    CONGRATS_WAIT,
    CONGRATULATIONS,
    DOT_AREA,
    DOT_DAY_Y,
    DOT_ROW_HALF,
    DOT_TAB_Y,
    DOT_TAP_OFFSET,
    GATHER_CHESTS,
    MILESTONE_BOX,
)

# Rương mốc theo event: [((x, y) tâm icon, mốc)].
CHESTS = {"gather_troops": GATHER_CHESTS}


def claim_key(event: str, done_count: int) -> str:
    """Key daily_done: đã nhận thưởng của `event` khi có `done_count` nhiệm vụ xong."""
    return f"{event}_claimed_{done_count}"


def maybe_claim(bot, state: EventState, event: str, name: str, icon: str, keys: list[str]):
    """Nhận thưởng `event` nếu có nhiệm vụ trong `keys` xong hôm nay mà chưa nhận ứng với số
    nhiệm vụ xong hiện tại."""
    done_count = sum(1 for key in keys if bot.is_daily_done(key))
    if done_count == 0:
        return
    key = claim_key(event, done_count)
    if bot.is_daily_done(key):
        return
    bot.log(f"{name}: {done_count} task(s) done, claiming rewards")
    run(bot, state, name, icon, CHESTS.get(event, ()))
    bot.mark_daily_done(key)


def run(bot, state: EventState, name: str, icon: str, chests=()):
    """Mở event `icon`, bấm lần lượt các tab có chấm đỏ (mỗi tab Claim All), rồi nhận rương
    mốc `chests` đã tới mốc."""
    def handle(action, pos, screen):
        if action != EVENT_OPENED:
            return None
        _claim_dots(bot, state, name)
        if chests:
            _claim_chests(bot, name, chests)
        return STOP

    run_task(bot, state, f"{name} claim", icon, handle)


def _claim_dots(bot, state: EventState, name: str):
    tapped = set()   # ("day", x) / ("tab", x của Day đang mở, x) đã bấm trong lượt này
    day = None       # x của tab Day vừa bấm (None = Day đang mở lúc vào)
    dx, dy = DOT_TAP_OFFSET
    for _ in range(CLAIM_MAX_STEPS):
        screen = bot.screenshot()
        claim = bot.find(CLAIM_ALL, screen=screen)
        if claim is not None:
            claim_all(bot, state, claim)
            continue
        tabs = [x for x in red_dots(screen, DOT_TAB_Y) if ("tab", day, x) not in tapped]
        if tabs:
            tapped.add(("tab", day, tabs[0]))
            bot.log(f"{name}: red dot on tab at x {tabs[0]}")
            bot.tap(tabs[0] + dx, DOT_TAB_Y + dy, delay=2)
            continue
        days = [x for x in red_dots(screen, DOT_DAY_Y) if ("day", x) not in tapped]
        if days:
            day = days[0]
            tapped.add(("day", day))
            bot.log(f"{name}: red dot on day at x {day}")
            bot.tap(day + dx, DOT_DAY_Y + dy, delay=2)
            continue
        bot.log(f"{name}: no red dots left")
        return
    bot.log(f"{name}: claim stopped after {CLAIM_MAX_STEPS} steps")


def _claim_chests(bot, name: str, chests):
    """Bấm các rương có mốc <= số đã làm (OCR "Progress:x / y") mà chưa có dấu tích."""
    screen = bot.screenshot()
    done = read_milestone(bot.crop(screen, *MILESTONE_BOX), total=chests[-1][1])
    if done is None:
        bot.log(f"{name}: cannot read milestone progress, chests skipped")
        return
    for (x, y), milestone in chests:
        if milestone > done:
            break
        area = bot.crop(screen, x - CHEST_HALF, y - CHEST_HALF, 2 * CHEST_HALF, 2 * CHEST_HALF)
        if bot.find(CHEST_TICK, threshold=CHEST_TICK_THRESHOLD, screen=area) is not None:
            continue
        bot.log(f"{name}: claim chest {milestone} (progress {done})")
        bot.tap(x, y, delay=1)
        _wait_congratulations_gone(bot)


def _wait_congratulations_gone(bot):
    """Chờ băng "Congratulations!" (hiện sau khi nhận rương) mất, tối đa CONGRATS_WAIT giây."""
    for _ in range(CONGRATS_WAIT * 2):
        if bot.find(CONGRATULATIONS) is None:
            return
        bot.sleep(0.5)


def red_dots(screen, row_y: int) -> list[int]:
    """x tâm các chấm đỏ trên hàng tab quanh `row_y` (trái -> phải)."""
    top = max(0, row_y - DOT_ROW_HALF)
    row = screen[top:row_y + DOT_ROW_HALF].astype(np.int16)
    blue, green, red = row[..., 0], row[..., 1], row[..., 2]
    mask = ((red > 150) & (green < 70) & (blue < 60)).astype(np.uint8)
    _, _, stats, centers = cv2.connectedComponentsWithStats(mask)
    low, high = DOT_AREA
    return sorted(int(cx) for (cx, _), stat in zip(centers[1:], stats[1:])
                  if low <= stat[cv2.CC_STAT_AREA] <= high)
