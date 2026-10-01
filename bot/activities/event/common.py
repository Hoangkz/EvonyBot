"""
common.py — phần dùng chung cho mọi nhiệm vụ Event.

Mỗi nhiệm vụ (gather_troops/..., kings_path/...) chạy cùng một cấu trúc vòng lặp:
chụp màn hình -> find_first(priority_targets() + ảnh riêng của nhiệm vụ +
common_targets()) -> nếu action là
của nhiệm vụ thì tự xử lý, còn lại gọi handle_common(). handle_common lo phần đi từ màn
hình chính tới nút event: nhận quà đăng nhập trước, thấy nút "•••" thì tìm Event Center
(nhiều ngưỡng trên cùng ảnh, không thấy thì kéo màn hình) rồi bấm nút event ngay dưới.
"""
from dataclasses import dataclass

from ...common import click_images, delay, exit_images, go_home
from .constants import (
    BACK,
    CLAIM_ALL,
    CLAIM_LOGIN_GIFT,
    EVENT_BUTTON_OFFSET,
    EVENT_CENTER,
    EVENT_CENTER_REGION,
    EVENT_CENTER_THRESHOLDS,
    EVENT_LIST_MAX_SCROLLS,
    EVENT_LIST_SWIPE,
    LOGIN_GIFT_ICON,
    LOGIN_GIFT_REWARD_OFFSET,
    LOGIN_GIFT_TITLE,
    MAIN_SCREEN,
    ON_MAIN_SCREEN,
    OPEN_LOGIN_GIFT,
    SWIPE_RIGHT,
    SWIPE_TIMES,
    SWIPE_UP,
    TAP,
)

# Kết quả của handle_common() để vòng lặp nhiệm vụ biết vừa xảy ra gì.
EVENT_OPENED = "event_opened"   # vừa bấm nút event dưới Event Center


@dataclass
class EventState:
    """Trạng thái dùng chung giữa các nhiệm vụ trong một lượt chạy Event."""
    login_done: bool = False   # mỗi lượt chỉ nhận quà 1 lần, kể cả khi bấm trượt


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
