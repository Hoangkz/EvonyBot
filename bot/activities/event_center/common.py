"""
common.py — phần dùng chung cho mọi nhiệm vụ Event Center.

run_task() lo đường đi: màn chính -> bấm chính nút Event Center -> tab -> cuộn tìm icon
event -> bấm. Nhiệm vụ chỉ khai báo ảnh riêng (`targets`) và hàm `handle` xử lý action của
các ảnh đó (xem crazy_eggs/run.py):

    def handle(action, pos, screen):
        if action == ON_EGGS:
            ...
            return 1800      # giá trị khác None / HANDLED -> run_task trả về giá trị này
        return None          # không phải action của nhiệm vụ -> run_task tự xử lý

    result = run_task(bot, "Crazy Eggs", ACTIVITIES, ICON, handle, targets=[(TITLE, ON_EGGS)])

Ảnh riêng xét trước ảnh dùng chung (tab, popup, màn chính).
"""
from ...context import DEFAULT_THRESHOLD
from ...common import GAME_PACKAGE, click_images, delay, exit_images, find_first, go_home
from ..event.common import find_event_center, swipe_around
from ..event.constants import MAIN_SCREEN
from .constants import (
    BACK,
    COMPETITION_TAB,
    EVENT_CENTER_TAP_OFFSET,
    AFTER_RESTART_ATTEMPTS,
    ATTEMPTS,
    LIST_MAX_SCROLLS,
    LIST_SWIPE,
    LIST_SWIPE_DURATION,
    MAX_STEPS,
    ON_EVENT_CENTER,
    ON_MAIN_SCREEN,
    RESTART_WAIT,
    TAB_REGION,
    TAB_THRESHOLD,
    TABS,
    TAP,
)

# Giá trị `handle` trả cho run_task(): action riêng đã xử lý xong -> quét lại.
HANDLED = "handled"
# run_task() trả về khi ở màn Event Center mà không thấy tab cần mở (đã BACK khỏi Event Center).
TAB_NOT_FOUND = "tab_not_found"
# run_task() trả về khi cuộn hết danh sách mà không thấy icon event (đã BACK khỏi Event Center).
ICON_NOT_FOUND = "icon_not_found"


def run_task(bot, name: str, tab: str, icon: str, handle, *, targets=(), regions=None,
             thresholds=None, icon_threshold: float = DEFAULT_THRESHOLD):
    """Vòng lặp chung: chụp màn hình -> find_first(`targets` + ảnh dùng chung) ->
    `handle(action, pos, screen)` trước; trả None thì run_task tự xử lý, HANDLED thì quét
    lại, giá trị khác thì return giá trị đó. Ở màn Event Center (thấy tab Competition): bấm
    tab `tab` rồi mở `icon` (ngưỡng `icon_threshold`). Không thấy tab -> TAB_NOT_FOUND; không thấy icon -> ICON_NOT_FOUND;
    quá MAX_STEPS màn hình -> None."""
    regions = {COMPETITION_TAB: TAB_REGION, **(regions or {})}
    all_targets = list(targets) + common_targets()
    for _ in range(MAX_STEPS):
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, all_targets, regions=regions, thresholds=thresholds)
        if action is None:
            bot.log(f"{name}: unknown screen (no image matched), Back / go home")
        else:
            bot.log(f"{name}: {action} at {pos}")
        result = handle(action, pos, screen)
        if result == HANDLED:
            continue
        if result is not None:
            return result
        if action == ON_EVENT_CENTER:
            if not open_tab(bot, screen, tab):
                bot.record(f"{name}: tab {tab} not found")
                bot.back(delay=1)
                return TAB_NOT_FOUND
            if not open_event(bot, icon, icon_threshold):
                bot.record(f"{name}: event not found")
                return ICON_NOT_FOUND
        elif action == ON_MAIN_SCREEN:
            open_event_center(bot, screen)
        elif action == BACK:
            bot.back(delay=1)
        elif action == TAP:
            bot.tap(*pos, delay=2)
        else:
            go_home(bot, screen)
            delay(bot)
    bot.record(f"{name}: stopped after {MAX_STEPS} steps")
    return None


NOT_FOUND = (TAB_NOT_FOUND, ICON_NOT_FOUND)


def run_task_with_retry(bot, name: str, *args, **kwargs):
    """run_task(); không thấy tab / icon (TAB_NOT_FOUND / ICON_NOT_FOUND) thì gọi lại, tối đa
    ATTEMPTS lần. Vẫn không được thì tắt game (force-stop) rồi gọi thêm AFTER_RESTART_ATTEMPTS lần:
    run_task thấy launcher -> go_home mở lại game. Trả kết quả của lần gọi cuối (vẫn
    TAB_NOT_FOUND / ICON_NOT_FOUND = nhiệm vụ tự quyết)."""
    result = None
    for restarted, attempts in ((False, ATTEMPTS), (True, AFTER_RESTART_ATTEMPTS)):
        if restarted:
            bot.record(f"{name}: {result} after {ATTEMPTS} tries, restarting game")
            restart_game(bot)
        for attempt in range(1, attempts + 1):
            result = run_task(bot, name, *args, **kwargs)
            if result not in NOT_FOUND:
                return result
            bot.log(f"{name}: {result} ({attempt}/{attempts}{', after restart' if restarted else ''})")
    return result


def restart_game(bot):
    """Tắt game; lần quét sau thấy launcher -> go_home mở lại game."""
    bot.record("Tắt game để khởi động lại")
    bot.shell(f"am force-stop {GAME_PACKAGE}")
    delay(bot, RESTART_WAIT)


def common_targets() -> list[tuple[str, str]]:
    """(ảnh, action) dùng chung, đặt SAU ảnh riêng của nhiệm vụ. Màn Event Center nhận bằng
    tab Competition; popup (exit/click) trước màn chính."""
    return [
        (COMPETITION_TAB, ON_EVENT_CENTER),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (MAIN_SCREEN, ON_MAIN_SCREEN),
    ]


def open_tab(bot, screen, tab: str) -> bool:
    """Màn Event Center: bấm tab `tab` (ảnh đang chọn hoặc chưa chọn). Không thấy -> False."""
    for path in TABS[tab]:
        pos = bot.find(path, threshold=TAB_THRESHOLD, screen=screen, region=TAB_REGION)
        if pos is not None:
            bot.tap(*pos, delay=2)
            return True
    return False


def open_event_center(bot, screen):
    """Màn chính: bấm chính nút Event Center; không thấy thì kéo màn hình để lộ lại."""
    center = find_event_center(bot, screen)
    if center is None:
        bot.log("Event Center: not found, swiping")
        swipe_around(bot)
        return
    dx, dy = EVENT_CENTER_TAP_OFFSET
    bot.tap(center[0] + dx, center[1] + dy, delay=5)


def open_event(bot, icon, threshold: float = DEFAULT_THRESHOLD) -> bool:
    """Trong tab Event Center: tìm `icon` (một ảnh, hoặc danh sách ảnh — thấy ảnh nào bấm ảnh đó)
    cuộn tối đa LIST_MAX_SCROLLS lần rồi bấm. Không thấy thì BACK và trả False."""
    icons = (icon,) if isinstance(icon, str) else tuple(icon)
    for scroll in range(LIST_MAX_SCROLLS + 1):
        screen = bot.screenshot()
        pos = next((p for p in (bot.find(i, threshold=threshold, screen=screen) for i in icons)
                    if p is not None), None)
        if pos is not None:
            bot.tap(*pos, delay=3)
            return True
        if scroll < LIST_MAX_SCROLLS:
            bot.swipe_percent(*LIST_SWIPE, duration=LIST_SWIPE_DURATION, delay=2)
    bot.record(f"Event Center: {icons} not found after {LIST_MAX_SCROLLS} scrolls")
    bot.back(delay=1)
    return False
