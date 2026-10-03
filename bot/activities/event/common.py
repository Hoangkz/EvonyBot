"""
common.py — phần dùng chung cho mọi nhiệm vụ Event.

Mọi nhiệm vụ (gather_troops/..., kings_path/...) đều đi qua cùng các bước để tới màn
event: màn chính -> nhận quà đăng nhập -> nút event (nút có ruy băng đếm ngược, xem
find_event_button) -> danh sách event -> icon event. Các bước đó nằm trong run_task(); nhiệm vụ chỉ khai báo ảnh riêng của mình
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
import time
from dataclasses import dataclass

import cv2
import numpy as np

from ...common import click_images, delay, exit_images, find_first, go_home, images_in
from ...context.templates import TEMPLATE_DIR
from ...ocr import read_progress
from ...ocr.read_progress import run_two_lines as read_progress_two_lines
from .constants import (
    BACK,
    CLAIM,
    CLAIM_ALL,
    CLAIM_ALL_MAX_TAPS,
    CLAIM_LOGIN_GIFT,
    DAY_LOCK,
    DAY_LOCK_THRESHOLD,
    DAY_TABS,
    DAY_TABS_REGION,
    EVENT_BUTTON_OFFSET,
    EVENT_CENTER,
    EVENT_CENTER_REGION,
    EVENT_CENTER_THRESHOLDS,
    EVENT_ICON_THRESHOLD,
    EVENT_LIST_MAX_SCROLLS,
    EVENT_OPEN_RETRIES,
    CHEST_FROM_TIP,
    CHEST_OPENED,
    CHEST_OPENED_THRESHOLD,
    CHEST_TAP,
    CHEST_WAIT,
    LOGIN_REWARD_KEY,
    VOYAGE_BACKS,
    VOYAGE_FREE,
    VOYAGE_FREE_REGION,
    VOYAGE_ICON,
    VOYAGE_KEY,
    VOYAGE_ONCE_DY,
    VOYAGE_SCREEN_WAIT,
    VOYAGE_SKIP_OFF,
    VOYAGE_SKIP_REGION,
    VOYAGE_SKIP_THRESHOLD,
    VOYAGE_STEP_WAIT,
    VOYAGE_THRESHOLD,
    VOYAGE_TITLE,
    VOYAGE_WAIT,
    PROGRESS_TIP,
    PROGRESS_TIP_REGION,
    PROGRESS_TIP_THRESHOLD,
    EVENT_LIST_TITLE,
    EVENT_LIST_TITLE_BOX,
    EVENT_LIST_TITLES_DIR,
    EVENT_LIST_TITLE_THRESHOLD,
    EVENT_LIST_WAIT,
    EVENT_LIST_SWIPE,
    REFRESH_TITLE_ICONS,
    TITLE_MIN_STD,
    TITLE_SAME,
    GO_BUTTON,
    GO_REGION,
    LOGIN_GIFT_ICON,
    LOGIN_GIFT_REWARD_OFFSET,
    LOGIN_GIFT_TITLE,
    MAIN_SCREEN,
    ON_EVENT_LIST,
    ON_MAIN_SCREEN,
    OPEN_LOGIN_GIFT,
    PROGRESS_FROM_GO,
    PROGRESS_LINE1_FROM_GO,
    PROGRESS_LINE2_FROM_GO,
    RIBBON_BUTTON_OFFSET,
    RIBBON_SEARCH,
    RIBBON_TAIL,
    SWIPE_RIGHT,
    SWIPE_TIMES,
    SWIPE_UP,
    TAP,
)

# Kết quả của handle_common() để vòng lặp nhiệm vụ biết vừa xảy ra gì; run_task() cũng
# gọi handle(EVENT_OPENED, None, None) ngay sau khi mở được icon event.
EVENT_OPENED = "event_opened"   # vừa bấm nút event
# Giá trị `handle` của nhiệm vụ trả cho run_task().
HANDLED = "handled"             # action riêng đã xử lý xong -> quét lại
STOP = "stop"                   # nhiệm vụ kết thúc -> run_task() return


@dataclass
class EventState:
    """Trạng thái dùng chung giữa các nhiệm vụ trong một lượt chạy Event."""
    login_done: bool = False   # mỗi lượt chỉ nhận quà 1 lần, kể cả khi bấm trượt
    claim_all_taps: int = 0    # số lần bấm Claim All liên tiếp (xem CLAIM_ALL_MAX_TAPS)


# ---- Nhiệm vụ đã đạt mục tiêu ------------------------------------------------------------
# Đạt mục tiêu (target reached / hết nút Go / làm đủ số cần) -> lưu "<key>_complete" trong
# daily_done: không hết hạn ở lần reset server, event/run.py bỏ qua nhiệm vụ luôn (hàm dọn dẹp
# khi event hết hạn sẽ xoá — TODO). Chỉ hết lượt / hết tài nguyên trong ngày thì vẫn
# mark_daily_done(key) như cũ (mai kiểm tra tiếp).
#
# Hai kiểu xong:
# - mark_complete: hết nút Go (đã làm tới mốc cao nhất của nhiệm vụ) -> "<key>_complete", xong hẳn
#   dù người dùng chọn mục tiêu nào.
# - mark_target_reached: đạt số lượng người dùng chọn (ô chọn: settings Event {key: {"value": N}})
#   mà vẫn còn Go -> "<key>_complete_<N>" và "<key>_reached_<N>" (đạt N hôm nay). Người dùng tăng
#   mục tiêu (N -> M > N) thì không còn key ứng với M -> nhiệm vụ chạy lại (is_complete /
#   is_done_today). Ô tích (không có số): như mark_complete.
def task_target(bot, key: str) -> int | None:
    """Mục tiêu người dùng chọn cho nhiệm vụ `key` (tab Event, "value"), hoặc None (ô tích)."""
    task = (getattr(bot, "settings", None) or {}).get("Event", {}).get(key)
    value = task.get("value") if isinstance(task, dict) else None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def complete_key(key: str, target: int | None = None) -> str:
    return f"{key}_complete" if target is None else f"{key}_complete_{target}"


def reached_key(key: str, target: int) -> str:
    return f"{key}_reached_{target}"


def is_complete(bot, key: str) -> bool:
    """Xong cả vòng event: hết Go (xong hẳn), hoặc đã đạt mục tiêu HIỆN TẠI của nhiệm vụ."""
    target = task_target(bot, key)
    return bool(bot.done_at(complete_key(key))
                or (target is not None and bot.done_at(complete_key(key, target))))


def mark_complete(bot, key: str):
    """Hết nút Go: xong hôm nay (đếm cho claim.py) và xong hẳn cả vòng event (mọi mục tiêu)."""
    bot.mark_daily_done(key)
    bot.mark_daily_done(complete_key(key))


def mark_target_reached(bot, key: str):
    """Đạt số lượng người dùng chọn (vẫn còn Go): xong hôm nay và xong vòng event VỚI mục tiêu
    này; tăng mục tiêu thì chưa xong. Ô tích (không có số): như mark_complete."""
    target = task_target(bot, key)
    if target is None:
        mark_complete(bot, key)
        return
    bot.mark_daily_done(key)
    bot.mark_daily_done(complete_key(key, target))
    bot.mark_daily_done(reached_key(key, target))


def is_done_today(bot, key: str) -> bool:
    """Nhiệm vụ đã xong hôm nay (daily_done `key`), TRỪ khi hôm nay xong là vì đạt một mục tiêu nhỏ
    hơn mục tiêu hiện tại (người dùng vừa tăng lên) -> chưa xong, chạy lại. Xong vì hết lượt / hết
    tài nguyên trong ngày (không có "<key>_reached_*" hôm nay) vẫn tính là xong."""
    if not bot.is_daily_done(key):
        return False
    target = task_target(bot, key)
    if target is None or bot.done_at(complete_key(key)):
        return True
    prefix = f"{key}_reached_"
    reached = [int(k[len(prefix):]) for k in bot.daily_keys()
               if k.startswith(prefix) and k[len(prefix):].isdigit() and bot.is_daily_done(k)]
    return not reached or max(reached) >= target


def run_task(bot, state: EventState, name: str, event_icon: str, handle=None, *,
             targets=(), regions=None, thresholds=None):
    """Vòng lặp chung của một nhiệm vụ Event: chụp màn hình -> find_first(
    priority_targets() + `targets` + common_targets()) -> `handle(action, pos, screen)`
    trước; handle trả None thì handle_common() xử lý. Khi handle_common vừa bấm nút
    event: mở `event_icon` trong danh sách event (không thấy thì return), rồi gọi
    `handle(EVENT_OPENED, None, None)`. `handle` trả STOP thì return.
    Không có `handle`: dừng ngay khi vừa mở được event.
    Không vào được danh sách event (open_event trả NOT_IN_LIST, đã Back): thử lại thêm
    EVENT_OPEN_RETRIES lần, vẫn không được thì return (nhiệm vụ dừng, event/run.py chuyển sang
    nhiệm vụ khác). Vào được danh sách thì đếm lại từ 0; ở danh sách mà không thấy icon
    (NOT_FOUND) thì return luôn."""
    failures = 0   # số lần liên tiếp không vào được danh sách event
    while True:
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, priority_targets() + list(targets)
                                 + common_targets(state), regions=regions,
                                 thresholds={**{title: EVENT_LIST_TITLE_THRESHOLD
                                                for title in event_list_titles()},
                                             **(thresholds or {})})
        if action is None:
            bot.log(f"{name}: unknown screen (no image matched), Back / go home")
        else:
            bot.log(f"{name}: {action} at {pos}")
        if action == CLAIM:
            claim_all(bot, state, pos)
            continue
        state.claim_all_taps = 0   # gặp màn khác: đếm lại số lần bấm Claim All liên tiếp
        result = handle(action, pos, screen) if handle is not None else None
        if result == STOP:
            return
        if result is not None:
            continue
        if handle_common(bot, state, action, pos, screen) != EVENT_OPENED:
            continue
        # Màn danh sách event: tìm (cuộn tối đa 4 lần) rồi bấm icon event.
        result = open_event(bot, event_icon)
        if result == NOT_FOUND:
            bot.record(f"{name}: event not found in event list, skip to next task")
            return
        if result == NOT_IN_LIST:
            failures += 1
            if failures > EVENT_OPEN_RETRIES:
                bot.record(f"{name}: event list not opened after {failures} tries, skip to next task")
                return
            bot.record(f"{name}: event list not opened, retry {failures}/{EVENT_OPEN_RETRIES}")
            continue
        failures = 0
        bot.log(f"{name}: event opened")
        if handle is None or handle(EVENT_OPENED, None, None) == STOP:
            return


def claim_all(bot, state: EventState, pos):
    """Bấm Claim All. Lỗi game (nút không mất): bấm liên tiếp quá CLAIM_ALL_MAX_TAPS lần thì
    Back và đếm lại từ 0."""
    state.claim_all_taps += 1
    if state.claim_all_taps > CLAIM_ALL_MAX_TAPS:
        bot.record(f"Event: Claim All still there after {CLAIM_ALL_MAX_TAPS} taps, back")
        state.claim_all_taps = 0
        bot.back(delay=1)
        return
    bot.tap(*pos, delay=2)


def priority_targets() -> list[tuple[str, str]]:
    """(ảnh, action) đặt TRƯỚC ảnh riêng của nhiệm vụ: thấy là bấm ngay rồi quét lại."""
    return [(CLAIM_ALL, CLAIM)]


def common_targets(state: EventState) -> list[tuple[str, str]]:
    """(ảnh, action) dùng chung, đặt SAU ảnh riêng của nhiệm vụ. Màn quà (chữ "Login
    Gifts") xét trước icon vì tab trong màn đó cũng giống icon; hết quà thì bỏ cả hai.
    Ảnh exit/click (popup) xét trước ảnh của màn chính (icon quà, MAIN_SCREEN): popup đè
    lên thành thì vẫn thấy ảnh màn chính nhưng bấm không được, phải đóng popup trước.
    Icon quà xét trước nút "•••" để ở màn chính luôn nhận quà trước khi tìm Event Center."""
    targets = []
    if not state.login_done:
        targets.append((LOGIN_GIFT_TITLE, CLAIM_LOGIN_GIFT))
    # Đang ở sẵn danh sách event: tìm icon luôn (trước đây không nhận ra màn -> go_home Back ra thành).
    targets += [(title, ON_EVENT_LIST) for title in event_list_titles()]
    targets += [(path, BACK) for path in exit_images()]
    targets += [(path, TAP) for path in click_images()]
    if not state.login_done:
        targets.append((LOGIN_GIFT_ICON, OPEN_LOGIN_GIFT))
    targets.append((MAIN_SCREEN, ON_MAIN_SCREEN))
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
    elif action == ON_EVENT_LIST:
        bot.log("Event: already on event list")
        return EVENT_OPENED
    elif action == ON_MAIN_SCREEN:
        button = find_event_button(bot, screen)
        if button is None:
            bot.log("Event: event button not found, swiping")
            swipe_around(bot)
            return None
        bot.log(f"Event: tap event button {button}")
        bot.tap(*button, delay=5)
        return EVENT_OPENED
    elif action == BACK:
        bot.back(delay=1)
    elif action == TAP:
        bot.tap(*pos, delay=2)
    else:
        go_home(bot, screen)
        delay(bot)
    return None


# Kết quả open_event.
OPENED = "opened"            # đã bấm icon event
NOT_IN_LIST = "not_in_list"  # không thấy tiêu đề danh sách lẫn icon: có thể chưa vào được danh sách
NOT_FOUND = "not_found"      # đang ở danh sách (thấy tiêu đề) mà cuộn hết không thấy icon


def open_event(bot, icon: str) -> str:
    """Ở màn danh sách event: tìm `icon` rồi bấm vào (OPENED). Không thấy thì cuộn xuống, cuộn quá
    EVENT_LIST_MAX_SCROLLS lần vẫn không thấy thì BACK và trả NOT_FOUND (đã thấy tiêu đề danh sách)
    hoặc NOT_IN_LIST (không thấy).
    Chờ tiêu đề danh sách event (EVENT_LIST_TITLE, VD "Wine Festival Event") tối đa EVENT_LIST_WAIT
    giây; không thấy vẫn cuộn tìm như thường, chỉ nhớ là không thấy (không lưu DB): tìm được icon
    King's Path / Gather Troops thì chụp màn, cắt tiêu đề danh sách lưu thành ảnh mới (add_title).
    Lần đầu thấy tiêu đề danh sách: kiểm rương Login Rewards hôm nay (claim_login_reward) rồi mới
    tìm icon. Gặp Voyage to Civilizations mà hôm nay chưa làm: vào bấm Free rồi Back (open_voyage)."""
    list_seen = wait_event_list_title(bot, EVENT_LIST_WAIT)
    if not list_seen:
        bot.log(f"Event: event list title not seen after {EVENT_LIST_WAIT} s, still searching")
    best = 0.0   # điểm khớp cao nhất qua các lần cuộn (ghi vào lịch sử khi không thấy)
    reward_checked = voyage_checked = False
    for scroll in range(EVENT_LIST_MAX_SCROLLS + 1):
        screen = bot.screenshot()
        # Danh sách tải chậm hơn EVENT_LIST_WAIT: thấy tiêu đề ở lần cuộn nào cũng tính là đã vào.
        list_seen = list_seen or find_event_list_title(bot, screen) is not None
        if list_seen and not reward_checked:
            reward_checked = True
            if claim_login_reward(bot, screen):
                screen = bot.screenshot()
        if not voyage_checked and open_voyage(bot, screen):
            voyage_checked = True
            screen = bot.screenshot()
        score, pos = bot.best_match(icon, screen=screen)
        if pos is not None and score >= EVENT_ICON_THRESHOLD:
            if not list_seen and icon in REFRESH_TITLE_ICONS:
                add_title(bot, screen, event_list_titles(), EVENT_LIST_TITLES_DIR,
                          EVENT_LIST_TITLE_BOX)
            bot.tap(*pos, delay=3)
            return OPENED
        best = max(best, score)
        if scroll < EVENT_LIST_MAX_SCROLLS:
            bot.swipe_percent(*EVENT_LIST_SWIPE, duration=0.5, delay=2)
    bot.record(f"Event: {icon} not found after {EVENT_LIST_MAX_SCROLLS} scrolls (best {best:.2f})")
    bot.back(delay=1)
    return NOT_FOUND if list_seen else NOT_IN_LIST


def claim_login_reward(bot, screen) -> bool:
    """Rương Login Rewards hôm nay (xem constants.py): mỗi ngày kiểm 1 lần. True nếu vừa bấm nhận
    (màn hình đã đổi)."""
    if bot.is_daily_done(LOGIN_REWARD_KEY):
        return False
    tip = bot.find(PROGRESS_TIP, threshold=PROGRESS_TIP_THRESHOLD, screen=screen,
                   region=PROGRESS_TIP_REGION)
    if tip is None:
        bot.log("Event: login reward progress bar not found, check next time")
        return False
    dx, dy, w, h = CHEST_FROM_TIP
    area = bot.crop(screen, tip[0] + dx, tip[1] + dy, w, h)
    if bot.find(CHEST_OPENED, threshold=CHEST_OPENED_THRESHOLD, screen=area) is not None:
        bot.log("Event: login reward already opened")
        bot.mark_daily_done(LOGIN_REWARD_KEY)
        return False
    bot.record(f"Event: claim login reward at progress bar {tip}")
    bot.tap(tip[0] + CHEST_TAP[0], tip[1] + CHEST_TAP[1], delay=CHEST_WAIT)
    bot.mark_daily_done(LOGIN_REWARD_KEY)
    return True


def open_voyage(bot, screen) -> bool:
    """Voyage to Civilizations (xem constants.py): hôm nay chưa vào và thấy icon trên `screen` ->
    vào và lưu VOYAGE_KEY ngay (mỗi ngày chỉ vào 1 lần, có Free hay không), tích Skip animation, có
    Free thì bấm Voyage Once, Back về danh sách. True nếu đã vào (màn hình đã đổi)."""
    if bot.is_daily_done(VOYAGE_KEY):
        return False
    pos = bot.find(VOYAGE_ICON, threshold=VOYAGE_THRESHOLD, screen=screen)
    if pos is None:
        return False
    bot.log("Event: open Voyage to Civilizations")
    bot.tap(*pos, delay=VOYAGE_WAIT)
    bot.mark_daily_done(VOYAGE_KEY)
    if bot.wait_for(VOYAGE_TITLE, timeout=VOYAGE_SCREEN_WAIT) is None:
        bot.record("Event: Voyage to Civilizations screen not shown")
        _back_to_event_list(bot)
        return True
    bot.sleep(VOYAGE_STEP_WAIT)   # màn vừa hiện: chờ tải xong rồi mới bấm
    screen = bot.screenshot()
    skip = bot.find(VOYAGE_SKIP_OFF, threshold=VOYAGE_SKIP_THRESHOLD, screen=screen,
                    region=VOYAGE_SKIP_REGION)
    if skip is not None:
        bot.log("Event: Voyage: tick Skip animation")
        bot.tap(*skip, delay=VOYAGE_WAIT)
        screen = bot.screenshot()
    free = bot.find(VOYAGE_FREE, screen=screen, region=VOYAGE_FREE_REGION)
    if free is not None:
        bot.record("Event: Voyage: free Voyage Once")
        bot.tap(free[0], free[1] + VOYAGE_ONCE_DY, delay=VOYAGE_WAIT)
    else:
        bot.log("Event: Voyage: no Free today")
    _back_to_event_list(bot)
    return True


def _back_to_event_list(bot):
    """Back tới khi về danh sách event (tối đa VOYAGE_BACKS lần; popup kết quả cũng đóng bằng
    Back): thấy tiêu đề danh sách HOẶC icon Voyage to Civilizations (chính dòng vừa bấm vào). Không
    chỉ dựa vào tiêu đề: đợt lễ hội đổi tiêu đề (VD "Event Center") thì không thấy tiêu đề, Back đủ
    VOYAGE_BACKS lần ra tới màn chính (máy 21943: event -> màn chính -> hộp thoát game)."""
    for _ in range(VOYAGE_BACKS):
        bot.back(delay=VOYAGE_STEP_WAIT)
        screen = bot.screenshot()
        if (find_event_list_title(bot, screen) is not None
                or bot.find(VOYAGE_ICON, threshold=VOYAGE_THRESHOLD, screen=screen) is not None):
            return
    bot.log("Event: event list not shown after Voyage")


def event_list_titles() -> list[str]:
    """Mọi ảnh tiêu đề danh sách event: title.png gốc và các ảnh bot đã thêm (EVENT_LIST_TITLES_DIR)."""
    return [EVENT_LIST_TITLE, *images_in(EVENT_LIST_TITLES_DIR)]


def find_event_list_title(bot, screen=None):
    """Vị trí tiêu đề danh sách event (khớp bất kỳ ảnh nào trong event_list_titles), hoặc None."""
    screen = bot.screenshot() if screen is None else screen
    for title in event_list_titles():
        pos = bot.find(title, threshold=EVENT_LIST_TITLE_THRESHOLD, screen=screen)
        if pos is not None:
            return pos
    return None


def wait_event_list_title(bot, timeout: float) -> bool:
    """Chờ tối đa `timeout` giây tới khi thấy tiêu đề danh sách event (mọi ảnh tiêu đề)."""
    end = time.monotonic() + timeout
    while True:
        if find_event_list_title(bot) is not None:
            return True
        if time.monotonic() >= end:
            return False
        bot.sleep(0.5)


def add_title(bot, screen, titles: list[str], folder: str, box) -> bool:
    """Cắt ô `box` (x, y, w, h) của `screen`; khác MỌI ảnh trong `titles` (điểm < TITLE_SAME) thì
    lưu thành ảnh mới <n>.png trong `folder` (không ghi đè ảnh nào). True nếu đã lưu."""
    crop = bot.crop(screen, *box)
    if crop.size == 0 or float(crop.std()) < TITLE_MIN_STD:
        bot.log("Event: title area is blank, not saving")
        return False
    for template in titles:
        path = TEMPLATE_DIR / template
        old = cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR) if path.exists() else None
        if old is not None and old.shape == crop.shape \
                and float(cv2.matchTemplate(crop, old, cv2.TM_CCOEFF_NORMED).max()) >= TITLE_SAME:
            return False
    directory = TEMPLATE_DIR / folder
    directory.mkdir(parents=True, exist_ok=True)
    number = 1 + max((int(p.stem) for p in directory.glob("*.png") if p.stem.isdigit()), default=0)
    path = directory / f"{number}.png"
    cv2.imencode(".png", crop)[1].tofile(str(path))
    bot.record(f"Event: new title image {folder}/{path.name}")
    return True


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
    """Số đã làm ở "300 / 500" ngay trên nút `go` (OCR), hoặc None nếu đọc lỗi. Đọc 1 dòng
    lỗi thì thử kiểu số lớn bị xuống 2 dòng ("23,530 /" + "50,000")."""
    def crop(box):
        dx, dy, w, h = box
        return bot.crop(screen, go[0] + dx, go[1] + dy, w, h)

    done = read_progress(crop(PROGRESS_FROM_GO))
    if done is None:
        done = read_progress_two_lines(crop(PROGRESS_LINE1_FROM_GO), crop(PROGRESS_LINE2_FROM_GO))
    return done


def find_event_button(bot, screen):
    """Điểm bấm nút event (MỘT kết quả duy nhất), hoặc None. `screen` là chính ảnh chụp vừa
    nhận ra màn chính (nút "•••"), không chụp lại.
    Nút event = nút có ruy băng đỏ đếm ngược, vị trí đổi theo số nút khác (có khi ngay dưới
    Event Center, có khi lên hàng trên cùng). Tìm đuôi ruy băng trong cả 2 vùng RIBBON_SEARCH:
    vùng nào trả về toạ độ thì vùng đó đúng. Ngưỡng thứ nhất trước, không vùng nào đạt thì lần
    lượt thử các ngưỡng thấp hơn; cả 2 vùng cùng đạt thì lấy chỗ khớp cao hơn. Ngưỡng thấp nhất
    cũng không đạt: bấm ngay dưới chữ "Event Center" như trước (không thấy cả Event Center ->
    None)."""
    matches = [(*bot.best_match(RIBBON_TAIL, screen=screen, region=region), thresholds)
               for region, thresholds in RIBBON_SEARCH]
    dx, dy = RIBBON_BUTTON_OFFSET
    for level in range(len(RIBBON_SEARCH[0][1])):
        passed = [(score, tail) for score, tail, thresholds in matches
                  if tail is not None and score >= thresholds[level]]
        if passed:
            score, (x, y) = max(passed)
            bot.log(f"Event: ribbon at {(x, y)} score {score:.3f} (level {level})")
            return x + dx, y + dy
    event_center = find_event_center(bot, screen)
    if event_center is None:
        return None
    bot.log("Event: no ribbon, using button below Event Center")
    ox, oy = EVENT_BUTTON_OFFSET
    return event_center[0] + ox, event_center[1] + oy


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
