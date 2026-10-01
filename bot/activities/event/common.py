"""
common.py — phần dùng chung cho mọi nhiệm vụ Event.

Mọi nhiệm vụ (gather_troops/..., kings_path/...) đều đi qua cùng các bước để tới màn
event: màn chính -> nhận quà đăng nhập -> nút dưới Event Center -> danh sách event ->
icon event. Các bước đó nằm trong run_task(); nhiệm vụ chỉ khai báo ảnh riêng của mình
và hàm `handle` xử lý action của các ảnh đó.

Ví dụ một nhiệm vụ mới (xem gather_troops/ground_troop/run.py là bản tối giản):

    from ...common import EVENT_OPENED, HANDLED, STOP, run_task
    from ...constants import GATHER_TROOPS_ICON
    from .constants import DAY_2, OPEN_DAY_2, ON_DAY_2, ..., REGIONS, THRESHOLDS

    def run(bot, task, state):
        def handle(action, pos, screen):
            if action == EVENT_OPENED:      # vừa mở màn event (VD 05_gather_be_prepared)
                return None                 # None = quét tiếp; STOP = dừng nhiệm vụ
            if action == OPEN_DAY_2:
                bot.tap(*pos, delay=2)
            elif action == ON_DAY_2:
                ...
                return STOP
            return HANDLED                  # action riêng đã xử lý xong -> quét lại

        run_task(bot, state, "Ground Troop", GATHER_TROOPS_ICON, handle,
                 targets=[(DAY_2_SELECTED, ON_DAY_2), (DAY_2, OPEN_DAY_2)],
                 regions=REGIONS, thresholds=THRESHOLDS)

Ảnh riêng (`targets`) xét sau priority_targets() (Claim All) và trước common_targets(),
màn sau đặt trước màn trước. `handle` trả None cho action không phải của nhiệm vụ để
handle_common() lo (quà, Event Center, BACK, go_home...).
"""
from dataclasses import dataclass

from ...common import click_images, delay, exit_images, find_first, go_home
from ...ocr import read_progress
from .constants import (
    BACK,
    CLAIM_ALL,
    CLAIM_LOGIN_GIFT,
    DAY_LOCK,
    DAY_LOCK_THRESHOLD,
    DAY_TABS,
    DAY_TABS_REGION,
    EVENT_BUTTON_OFFSET,
    EVENT_CENTER,
    EVENT_CENTER_REGION,
    EVENT_CENTER_THRESHOLDS,
    EVENT_LIST_MAX_SCROLLS,
    EVENT_LIST_SWIPE,
    GO_BUTTON,
    GO_REGION,
    LOGIN_GIFT_ICON,
    LOGIN_GIFT_REWARD_OFFSET,
    LOGIN_GIFT_TITLE,
    MAIN_SCREEN,
    ON_MAIN_SCREEN,
    OPEN_LOGIN_GIFT,
    PROGRESS_FROM_GO,
    SWIPE_RIGHT,
    SWIPE_TIMES,
    SWIPE_UP,
    TAP,
)

# Kết quả của handle_common() để vòng lặp nhiệm vụ biết vừa xảy ra gì; run_task() cũng
# gọi handle(EVENT_OPENED, None, None) ngay sau khi mở được icon event.
EVENT_OPENED = "event_opened"   # vừa bấm nút event dưới Event Center
# Giá trị `handle` của nhiệm vụ trả cho run_task().
HANDLED = "handled"             # action riêng đã xử lý xong -> quét lại
STOP = "stop"                   # nhiệm vụ kết thúc -> run_task() return


@dataclass
class EventState:
    """Trạng thái dùng chung giữa các nhiệm vụ trong một lượt chạy Event."""
    login_done: bool = False   # mỗi lượt chỉ nhận quà 1 lần, kể cả khi bấm trượt


def run_task(bot, state: EventState, name: str, event_icon: str, handle=None, *,
             targets=(), regions=None, thresholds=None):
    """Vòng lặp chung của một nhiệm vụ Event: chụp màn hình -> find_first(
    priority_targets() + `targets` + common_targets()) -> `handle(action, pos, screen)`
    trước; handle trả None thì handle_common() xử lý. Khi handle_common vừa bấm nút
    event: mở `event_icon` trong danh sách event (không thấy thì return), rồi gọi
    `handle(EVENT_OPENED, None, None)`. `handle` trả STOP thì return.
    Không có `handle`: dừng ngay khi vừa mở được event."""
    while True:
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, priority_targets() + list(targets)
                                 + common_targets(state), regions=regions,
                                 thresholds=thresholds)
        bot.log(f"{name}: {action} at {pos}")
        result = handle(action, pos, screen) if handle is not None else None
        if result == STOP:
            return
        if result is not None:
            continue
        if handle_common(bot, state, action, pos, screen) != EVENT_OPENED:
            continue
        # Màn danh sách event: tìm (cuộn tối đa 4 lần) rồi bấm icon event.
        if not open_event(bot, event_icon):
            bot.log(f"{name}: event not found")
            return
        bot.log(f"{name}: event opened")
        if handle is None or handle(EVENT_OPENED, None, None) == STOP:
            return


def priority_targets() -> list[tuple[str, str]]:
    """(ảnh, action) đặt TRƯỚC ảnh riêng của nhiệm vụ: thấy là bấm ngay rồi quét lại."""
    return [(CLAIM_ALL, TAP)]


def common_targets(state: EventState) -> list[tuple[str, str]]:
    """(ảnh, action) dùng chung, đặt SAU ảnh riêng của nhiệm vụ. Màn quà (chữ "Login
    Gifts") xét trước icon vì tab trong màn đó cũng giống icon; hết quà thì bỏ cả hai.
    Icon quà xét trước nút "•••" để ở màn chính luôn nhận quà trước khi tìm Event Center."""
    targets = []
    if not state.login_done:
        targets += [(LOGIN_GIFT_TITLE, CLAIM_LOGIN_GIFT), (LOGIN_GIFT_ICON, OPEN_LOGIN_GIFT)]
    targets.append((MAIN_SCREEN, ON_MAIN_SCREEN))
    targets += [(path, BACK) for path in exit_images()]
    targets += [(path, TAP) for path in click_images()]
    return targets


def handle_common(bot, state: EventState, action, pos, screen):
    """Xử lý các action của common_targets(). Trả EVENT_OPENED khi vừa bấm nút event,
    còn lại None."""
    if action == CLAIM_LOGIN_GIFT:
        bot.log("Event: claim Login Gifts")
        dx, dy = LOGIN_GIFT_REWARD_OFFSET
        bot.tap(pos[0] + dx, pos[1] + dy, delay=2)
        bot.back(delay=1)
        state.login_done = True
    elif action == OPEN_LOGIN_GIFT:
        bot.log("Event: open Login Gifts")
        bot.tap(*pos, delay=2)
    elif action == ON_MAIN_SCREEN:
        event_center = find_event_center(bot, screen)
        if event_center is None:
            bot.log("Event: Event Center not found, swiping")
            swipe_around(bot)
            return None
        dx, dy = EVENT_BUTTON_OFFSET
        bot.tap(event_center[0] + dx, event_center[1] + dy, delay=5)
        return EVENT_OPENED
    elif action == BACK:
        bot.back(delay=1)
    elif action == TAP:
        bot.tap(*pos, delay=2)
    else:
        go_home(bot, screen)
        delay(bot)
    return None


def open_event(bot, icon: str) -> bool:
    """Ở màn danh sách event: tìm `icon` rồi bấm vào. Không thấy thì cuộn xuống, cuộn quá
    EVENT_LIST_MAX_SCROLLS lần vẫn không thấy thì BACK và trả False."""
    for scroll in range(EVENT_LIST_MAX_SCROLLS + 1):
        pos = bot.find(icon)
        if pos is not None:
            bot.tap(*pos, delay=3)
            return True
        if scroll < EVENT_LIST_MAX_SCROLLS:
            bot.swipe_percent(*EVENT_LIST_SWIPE, duration=0.5, delay=1)
    bot.log(f"Event: {icon} not found after {EVENT_LIST_MAX_SCROLLS} scrolls")
    bot.back(delay=1)
    return False


def day_locked(bot, screen, day: int) -> bool:
    """Tab "Day `day`" của màn event đang khoá. Ngày khoá luôn là các ngày cuối nên chỉ
    cần đếm ổ khoá trên hàng tab: N ổ khoá -> Day DAY_TABS - N + 1 .. DAY_TABS khoá
    (VD 4 ổ khoá -> Day 2 khoá)."""
    locks = len(bot.find_all(DAY_LOCK, threshold=DAY_LOCK_THRESHOLD, screen=screen,
                             region=DAY_TABS_REGION))
    bot.log(f"Event: {locks} locked day(s)")
    return day > DAY_TABS - locks


def nearest_go(bot, screen, tab):
    """Nút "Go" gần `tab` nhất (tức dòng nhiệm vụ chưa xong trên cùng), hoặc None."""
    gos = bot.find_all(GO_BUTTON, screen=screen, region=GO_REGION)
    if not gos:
        return None
    return min(gos, key=lambda p: (p[0] - tab[0]) ** 2 + (p[1] - tab[1]) ** 2)


def read_go_progress(bot, screen, go) -> int | None:
    """Số đã làm ở "300 / 500" ngay trên nút `go` (OCR), hoặc None nếu đọc lỗi."""
    dx, dy, w, h = PROGRESS_FROM_GO
    return read_progress(bot.crop(screen, go[0] + dx, go[1] + dy, w, h))


def find_event_center(bot, screen):
    """Tâm chữ "Event Center" trên `screen` (không chụp lại), thử từng ngưỡng trong
    EVENT_CENTER_THRESHOLDS từ cao xuống thấp; None nếu ngưỡng thấp nhất cũng không thấy."""
    for threshold in EVENT_CENTER_THRESHOLDS:
        pos = bot.find(EVENT_CENTER, threshold=threshold, screen=screen,
                       region=EVENT_CENTER_REGION)
        if pos is not None:
            bot.log(f"Event: Event Center at threshold {threshold}")
            return pos
    return None


def swipe_around(bot):
    """Kéo màn hình sang phải 3 lần rồi lên 3 lần để lộ lại Event Center."""
    for swipe in (SWIPE_RIGHT, SWIPE_UP):
        for _ in range(SWIPE_TIMES):
            bot.swipe_percent(*swipe, duration=0.5, delay=1)
