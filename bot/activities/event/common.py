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
import importlib
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from ...common.go_home import EXIT_CANCEL, EXIT_DIALOG, EXIT_THRESHOLD
from ...common import click_images, delay, exit_images, find_first, go_home, images_in, to_city
from ...context.templates import TEMPLATE_DIR, read_image
from ...ocr import read_progress
from ...ocr.read_progress import run_two_lines as read_progress_two_lines
from ..result import TaskResult, report
from . import constants, cycle
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
    EVENT_ENDED_CHECKS,
    EVENT_ENDED_LAG_WAIT,
    EVENT_ENDED_MAX_BACKS,
    EVENT_ENDED_SAME_DIFF,
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
    DAYS_REGION,
    DAYS_TEXT,
    DAYS_THRESHOLD,
    EVENT_OPEN_SETTLE,
    EVENT_OPEN_WAITS,
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
EVENT_ENDED = "event_ended"     # màn chính có Event Center nhưng không có nút event (không ruy băng): event 7 ngày đã hết
# Giá trị `handle` của nhiệm vụ trả cho run_task().
HANDLED = "handled"             # action riêng đã xử lý xong -> quét lại
STOP = "stop"                   # nhiệm vụ kết thúc -> run_task() return


@dataclass
class EventState:
    """Trạng thái dùng chung giữa các nhiệm vụ trong một lượt chạy Event."""
    login_done: bool = False   # mỗi lượt chỉ nhận quà 1 lần, kể cả khi bấm trượt
    claim_all_taps: int = 0    # số lần bấm Claim All liên tiếp (xem CLAIM_ALL_MAX_TAPS)
    absent: set = field(default_factory=set)   # key event không còn trong game hôm nay (hết ruy băng / không thấy icon): perform_task lưu vào DB


# ---- Báo kết quả nhiệm vụ cho worker ------------------------------------------------------
# Nhiệm vụ BÁO kết quả giữa chừng (bot/activities/result.py); chỗ chạy nhiệm vụ (event/run.py event_job) lưu vào daily_done ngay; worker chỉ quyết định
# bỏ qua nhiệm vụ đã xong / đã đạt mục tiêu / Day khoá, và đọc lại mục tiêu người dùng chọn.
# - mark_done: hết lượt / hết tài nguyên trong ngày (mai kiểm tra tiếp).
# - mark_complete: hết nút Go (đã làm tới mốc cao nhất của nhiệm vụ) -> xong hẳn dù người dùng chọn mục tiêu nào.
# - mark_target_reached: đạt số lượng người dùng chọn (ô chọn: settings Event {key: {"value": N}}) mà vẫn còn Go;
#   người dùng tăng mục tiêu thì worker cho chạy lại. Ô tích (không có số): như mark_complete.
# - mark_locked: Day / cấp lính còn khoá, chưa thể làm (worker bỏ qua tới lần reset server).
def mark_done(bot, key: str):
    report(bot, TaskResult(done=True, key=key))


def mark_complete(bot, key: str):
    report(bot, TaskResult(done=True, complete=True, key=key))


# Nhiệm vụ Event -> việc Daily Activities làm cùng thao tác trong game: (gói trong daily_activities, ...).
_DAILY_OF = {
    "heal": "troop_healing",                  # King's Path Heal / 3-Day Heal  -> Troop Heading
    "train": "troop_training",                # King's Path Train Troop, Gather Troops 4 loại lính -> Troop Training
    "trap": "trap_building",                  # Gather Troops Trap Factory -> Trap Building
    "cultivate": "general_enhancing",         # Gather Troops Cultivate Generals -> General Enhancing
    "patrol": "patrol",                       # King's Path Patrol -> Patrol
    "wheel": "wheel_of_fortune",              # King's Path Wheel -> Wheel of Fortune
    "black_market": "black_market",           # King's Path Black Market -> Black Market
    "tax": "resource_tax",                    # King's Path City Tax -> Resource Tax
}


def mark_daily_activity(bot, kind: str):
    """Nhiệm vụ Event vừa thật sự làm xong thao tác `kind` (khoá của _DAILY_OF): việc Daily Activities cùng thao tác hôm nay cũng coi là
    xong, khỏi làm lại. Lưu daily_done của việc Daily (vào DB); đã lưu rồi thì thôi. Gọi từ phần của nhiệm vụ Event, KHÔNG gọi trong
    hàm dùng chung với Daily (patrol_rounds, spin_wheel, buy_items...) để Daily không tự đánh dấu mình giữa chừng."""
    # import trong hàm: các gói daily_activities nạp gói event (vòng import nếu import ở mức module).
    constants = importlib.import_module(f"{__package__.rsplit('.', 1)[0]}.daily_activities.{_DAILY_OF[kind]}.constants")
    if not bot.is_daily_done(constants.KEY):
        bot.record(f"Event: {kind} done, also marks Daily Activities {constants.LABEL} done today")
        bot.mark_daily_done(constants.KEY)


def mark_target_reached(bot, key: str):
    report(bot, TaskResult(done=True, target_reached=True, key=key))


def mark_locked(bot, key: str):
    report(bot, TaskResult(locked=True, key=key))


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
        opened = handle_common(bot, state, action, pos, screen)
        if opened == EVENT_ENDED:
            bot.record(f"{name}: no event ribbon next to Event Center, event has ended, skip to next task")
            state.absent.update(cycle.EVENT_OF_ICON.values())   # cả 2 event 7 ngày đều nằm sau nút ruy băng này
            return
        if opened != EVENT_OPENED:
            continue
        # Màn danh sách event: tìm (cuộn tối đa 4 lần) rồi bấm icon event.
        result = open_event(bot, event_icon)
        if result == NOT_FOUND:
            bot.record(f"{name}: event not found in event list, skip to next task")
            if event_icon in cycle.EVENT_OF_ICON:
                state.absent.add(cycle.EVENT_OF_ICON[event_icon])
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
        cycle.observe(bot, event_icon)   # chưa có ngày reset / đã quá ngày reset của event thì đọc ngày và lưu mốc reset
        if handle is None or handle(EVENT_OPENED, None, None) == STOP:
            return


TAB_CHANGE_TRIES = 10   # tap_tab: số lần chờ thêm 1s (sau lần kiểm tra đầu) khi tab chưa đổi


def tap_tab(bot, x, y, action, targets, regions=None, thresholds=None) -> bool:
    """Bấm tab Day / tab phụ của event (`action` là action vừa nhận ra ở chỗ bấm), chờ 1s rồi kiểm tra đã đổi chưa (nhận
    diện lại bằng `targets` thấy action khác), chưa thì chờ thêm 1s rồi kiểm tra lại, tối đa TAB_CHANGE_TRIES lần chờ thêm.
    Hết lượt mà chưa đổi thì thôi (False), vòng run_task nhận diện lại màn rồi bấm lại."""
    bot.tap(x, y, delay=1)
    for attempt in range(TAB_CHANGE_TRIES + 1):
        if attempt:
            bot.sleep(1)
        now, _ = find_first(bot, bot.screenshot(), list(targets), regions=regions, thresholds=thresholds)
        if now != action:
            return True
    bot.log(f"Event: tab still {action} after {TAB_CHANGE_TRIES} extra waits, tap again")
    return False


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


def _event_list_shown(bot, screen) -> bool:
    """Đã ở danh sách event: thấy chữ "day(s)" dưới hàng rương quà hàng ngày (cố định, không đổi theo đợt lễ hội như
    tiêu đề)."""
    return bot.find(DAYS_TEXT, threshold=DAYS_THRESHOLD, screen=screen, region=DAYS_REGION) is not None


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
        if to_city(bot):   # màn thế giới cũng có "•••" và Event Center: về thành rồi nhận diện lại
            return None
        button = find_event_button(bot, screen)
        if button is None:
            if find_event_center(bot, screen) is None:
                bot.log("Event: event button not found, swiping")
                swipe_around(bot)
                return None
            # Thấy Event Center mà không có ruy băng: lần đầu đã tính, kiểm thêm tới đủ EVENT_ENDED_CHECKS lần, mỗi lần sau một cú Back
            # xác nhận game đang phản hồi (xem _recheck_ribbon). Chưa kiểm đủ (game lag) thì không kết luận, quét lại màn.
            button, confirmed = _recheck_ribbon(bot)
            if button is None:
                return EVENT_ENDED if confirmed else None
        bot.log(f"Event: tap event button {button}")
        bot.tap(*button, delay=1)
        for attempt in range(EVENT_OPEN_WAITS + 1):
            if attempt:
                bot.sleep(1)
            if _event_list_shown(bot, bot.screenshot()):
                bot.sleep(EVENT_OPEN_SETTLE)
                return EVENT_OPENED
        bot.log(f"Event: event list not shown after {EVENT_OPEN_WAITS} extra waits, tap again")
        return None
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
                add_title(bot, screen, event_list_titles(), constants.LEARNED_TITLES_DIR,
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
    key = LOGIN_REWARD_KEY
    if bot.is_daily_done(key):
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
        bot.mark_daily_done(key)
        return False
    bot.record(f"Event: claim login reward at progress bar {tip}")
    bot.tap(tip[0] + CHEST_TAP[0], tip[1] + CHEST_TAP[1], delay=CHEST_WAIT)
    bot.mark_daily_done(key)
    return True


def open_voyage(bot, screen) -> bool:
    """Voyage to Civilizations (xem constants.py): tích Skip animation và nhận Free.

    Chỉ ghi DONE khi không còn Free; lỗi mở trang/cú bấm chưa ăn thì giữ chưa
    DONE. True nếu đã vào (màn hình đã đổi).
    """
    key = VOYAGE_KEY
    if bot.is_daily_done(key):
        return False
    pos = bot.find(VOYAGE_ICON, threshold=VOYAGE_THRESHOLD, screen=screen)
    if pos is None:
        return False
    scope = "Voyage"
    bot.log(f"Event: open {scope} to Civilizations")
    bot.tap(*pos, delay=VOYAGE_WAIT)
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
        # DONE chỉ khi nút Free đã biến mất. Popup Congratulations cũng che nút Free, nên đây là
        # dấu xác nhận cú bấm đã được game nhận; nếu nút vẫn còn thì lượt sau sẽ thử lại.
        screen = bot.screenshot()
        if bot.find(VOYAGE_FREE, screen=screen, region=VOYAGE_FREE_REGION) is not None:
            bot.record(f"Event: {scope} Free vẫn còn sau khi bấm; chưa DONE")
            _back_to_event_list(bot)
            return True
    else:
        bot.log("Event: Voyage: no Free today")
    bot.mark_daily_done(key)
    bot.record(f"Event: {scope} DONE")
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
    """Mọi ảnh tiêu đề danh sách event: title.png gốc, ảnh thêm tay (EVENT_LIST_TITLES_DIR, đường
    dẫn dưới Images/) và ảnh bot tự thêm (LEARNED_TITLES_DIR, đường dẫn tuyệt đối)."""
    learned = constants.LEARNED_TITLES_DIR
    added = sorted(learned.glob("*.png")) if learned.is_dir() else []
    return [EVENT_LIST_TITLE, *images_in(EVENT_LIST_TITLES_DIR),
            *(str(p) for p in added)]


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


def add_title(bot, screen, titles: list[str], folder, box) -> bool:
    """Cắt ô `box` (x, y, w, h) của `screen`; khác MỌI ảnh trong `titles` (đường dẫn dưới Images/ hoặc
    tuyệt đối, điểm < TITLE_SAME) thì lưu thành ảnh mới <n>.png trong thư mục `folder` (không ghi đè
    ảnh nào). True nếu đã lưu."""
    crop = bot.crop(screen, *box)
    if crop.size == 0 or float(crop.std()) < TITLE_MIN_STD:
        bot.log("Event: title area is blank, not saving")
        return False
    for template in titles:
        path = TEMPLATE_DIR / template
        old = read_image(path)
        if old is not None and old.shape == crop.shape \
                and float(cv2.matchTemplate(crop, old, cv2.TM_CCOEFF_NORMED).max()) >= TITLE_SAME:
            return False
    directory = Path(folder)
    directory.mkdir(parents=True, exist_ok=True)
    number = 1 + max((int(p.stem) for p in directory.glob("*.png") if p.stem.isdigit()), default=0)
    path = directory / f"{number}.png"
    cv2.imencode(".png", crop)[1].tofile(str(path))
    bot.record(f"Event: new title image {path}")
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
    cũng không đạt: None (không có ruy băng = không có event đang diễn ra; người gọi tự kiểm Event Center)."""
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
    return None


def _recheck_ribbon(bot):
    """Kiểm lại ruy băng cho đủ EVENT_ENDED_CHECKS lần (lần đầu đã làm ở người gọi). Mỗi lần: Back, rồi xác nhận game phản hồi:
    hiện hộp thoát game thì bấm Cancel; không có hộp mà màn đã đổi (popup đóng) cũng được; màn không đổi = game lag / đang load ->
    chờ rồi Back lại, KHÔNG tính lần kiểm đó (tối đa EVENT_ENDED_MAX_BACKS lần Back). Trả (nút event hoặc None, đã kiểm đủ chưa)."""
    checks = 1
    for _ in range(EVENT_ENDED_MAX_BACKS):
        if checks >= EVENT_ENDED_CHECKS:
            return None, True
        before = bot.screenshot()
        bot.back(delay=1.5)
        after = bot.screenshot()
        cancel = (bot.find(EXIT_CANCEL, threshold=EXIT_THRESHOLD, screen=after)
                  if bot.find(EXIT_DIALOG, threshold=EXIT_THRESHOLD, screen=after) is not None else None)
        if cancel is not None:
            bot.tap(*cancel, delay=1)
        elif before.shape != after.shape or float(np.abs(before.astype(np.int16) - after.astype(np.int16)).mean()) < EVENT_ENDED_SAME_DIFF:
            bot.log("Event: Back changed nothing, game may be lagging / loading, wait and Back again")
            bot.sleep(EVENT_ENDED_LAG_WAIT)
            continue
        checks += 1
        bot.log(f"Event: no ribbon, check {checks}/{EVENT_ENDED_CHECKS}")
        button = find_event_button(bot, bot.screenshot())
        if button is not None:
            return button, False
    return None, checks >= EVENT_ENDED_CHECKS


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
