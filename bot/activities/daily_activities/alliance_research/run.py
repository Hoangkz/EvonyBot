"""
run.py — Daily Activities "Research technologies": phần sau Go (Học viện -> Research -> 1 công nghệ xanh).
Mở Quests -> Activity, tìm dòng, bấm Go: ../common.py open_task_or_finish. Ảnh / hằng số: constants.py.

Sau Go: Học viện ở giữa -> open_menu (nhận ra / tự học ảnh công trình, icon "Research") -> màn Academy ->
nút công nghệ có nhãn Lv xanh đầu tiên (tab đầu trước, cuộn cây TREE_SCROLLS lần, không có thì sang tab kế bên)
-> Research. Tốn thời gian thì Speed Up xanh -> Finish All -> Confirm (không dùng kim cương). Xong -> báo xong
hôm nay -> Back về thành.
"""
import cv2
import numpy as np

from ...event.city_building import ACADEMY
from ...event.kings_path.building import open_menu
from ..common import Task, mark_task_done
from .constants import (
    ACADEMY_TITLE,
    BACKS_AFTER,
    COMMON_THRESHOLD,
    COMMON_UNCHECKED,
    CONFIRM,
    FINISH_ALL,
    FOLDER,
    GREEN_HIGH,
    GREEN_LOW,
    KEY,
    LABEL,
    CHANGED_PIXELS,
    INFO_BOX,
    LEVEL_SIZE,
    PIXEL_DIFF,
    MENU_RESEARCH,
    MENU_SPEED_UP,
    MENU_WAIT,
    POPUP_WAIT,
    RESEARCH_BUTTON,
    RESULT_WAIT,
    SPEED_UP,
    SPEEDUP_SETTINGS,
    SPEED_UP_REGION,
    SPEEDUP_TITLE,
    TAB_TAPS,
    TECH_TITLE,
    TREE_END_DIFF,
    TREE_SCROLLS,
    TREE_SWIPE_BACK,
    TREE_SWIPE,
    TREE_Y,
)


def green_levels(screen) -> list[tuple[int, int]]:
    """Tâm các nhãn "Lv N / M" màu xanh (công nghệ học được) trong vùng cây, từ trên xuống, trái sang phải.
    Chữ được nối thành một khối bằng phép giãn ngang; khối quá to / nhỏ (icon xanh, mũi tên) bị loại."""
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, GREEN_LOW, GREEN_HIGH)
    mask[:TREE_Y[0]] = 0
    mask[TREE_Y[1]:] = 0
    mask = cv2.dilate(mask, np.ones((3, 9), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    (min_w, max_w), (min_h, max_h) = LEVEL_SIZE
    found = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if min_w <= w <= max_w and min_h <= h <= max_h:
            found.append((x + w // 2, y + h // 2))
    return sorted(found, key=lambda p: (p[1], p[0]))


def changed_pixels(before, after) -> int:
    """Số điểm ảnh đổi mức xám (> PIXEL_DIFF) giữa hai ảnh cắt cùng vùng."""
    diff = cv2.absdiff(cv2.cvtColor(before, cv2.COLOR_BGR2GRAY), cv2.cvtColor(after, cv2.COLOR_BGR2GRAY))
    return int((diff > PIXEL_DIFF).sum())


def after_go(bot) -> bool:
    """Sau khi open_task bấm Go: vào Học viện. Menu có icon Speed Up (Học viện đang nghiên cứu sẵn) -> chỉ tăng
    tốc (Speedup Settings -> Finish All), không chọn công nghệ mới. Không thì Research -> nghiên cứu 1 công
    nghệ. True (và báo xong hôm nay) khi xong; cũng True khi cả 4 tab không còn công nghệ nào nghiên cứu được
    (không còn gì để làm hôm nay). False nếu không vào được Học viện hoặc Research không chạy."""
    key, pos = open_menu(bot, LABEL, ACADEMY, {"speed": MENU_SPEED_UP, "research": MENU_RESEARCH})
    if pos is None:
        return False
    bot.tap(*pos, delay=1)   # rồi chờ màn đích bằng wait_for ở từng nhánh (như tap_tab của train troop)
    if key == "speed":
        bot.record(f"{LABEL}: Academy already researching, using Speed Up items")
        researched = _speed_up(bot, None)
    else:
        if bot.wait_for(ACADEMY_TITLE, timeout=MENU_WAIT) is None:
            bot.record(f"{LABEL}: Academy screen not shown")
            return False
        researched = _research_one(bot)
        if researched is None:
            bot.record(f"{LABEL}: nothing to research in {len(TAB_TAPS) + 1} tabs, done for today")
            researched = True
    if researched:
        mark_task_done(bot, TASK)
    _leave(bot)
    return researched


def _research_one(bot) -> bool | None:
    """Bốn tab, tab hiện tại trước. Mỗi tab: thử từng nhãn xanh; hết nhãn xanh (còn lại vàng = tối đa, trắng =
    chưa mở khoá) thì cuộn cây xuống (tối đa TREE_SCROLLS lần, dừng sớm khi cây hết). Sang tab mới thì cuộn cây
    về đầu (tab mới có thể giữ vị trí cuộn). True: đã nghiên cứu; False: bấm Research mà không chạy (thiếu tài
    nguyên...); None: cả 4 tab không có công nghệ nào nghiên cứu được."""
    for tab in range(len(TAB_TAPS) + 1):
        for scroll in range(TREE_SCROLLS + 1):
            tried = set()
            for _ in range(8):   # mỗi nhãn xanh một lần; màn đổi sau khi đóng popup nên quét lại
                levels = [p for p in green_levels(bot.screenshot())
                          if all(abs(p[0] - q[0]) > 20 or abs(p[1] - q[1]) > 20 for q in tried)]
                if not levels:
                    break
                tried.add(levels[0])
                state = _try_technology(bot, levels[0])
                if state is not None:
                    return state
            if scroll == TREE_SCROLLS or not _scroll_tree(bot):
                break
        if tab < len(TAB_TAPS):
            bot.tap_percent(*TAB_TAPS[tab], delay=1.5)
            for _ in range(TREE_SCROLLS):
                bot.swipe_percent(*TREE_SWIPE_BACK, duration=0.6, delay=1)
    return None


def _scroll_tree(bot) -> bool:
    """Cuộn cây công nghệ xuống một lần. False nếu cây không đổi (đã hết)."""
    top, bottom = TREE_Y
    before = bot.screenshot()[top:bottom]
    bot.swipe_percent(*TREE_SWIPE, duration=0.6, delay=1.5)
    after = bot.screenshot()[top:bottom]
    return cv2.absdiff(before, after).mean() >= TREE_END_DIFF


def _try_technology(bot, pos) -> bool | None:
    """Bấm nhãn xanh -> màn Technology. Không có nút Research (đã tối đa...) -> đóng, None (thử cái khác).
    Có -> bấm Research, True/False theo kết quả."""
    bot.tap(*pos, delay=1)
    if bot.wait_for(TECH_TITLE, timeout=POPUP_WAIT) is None:
        bot.record(f"{LABEL}: Technology screen not shown")
        return None
    screen = bot.screenshot()
    button = bot.find(RESEARCH_BUTTON, screen=screen)
    if button is None:
        bot.log(f"{LABEL}: no Research button, trying next technology")
        bot.back(delay=1)
        return None
    before = bot.crop(screen, *INFO_BOX)
    bot.tap(*button, delay=RESULT_WAIT)
    screen = bot.screenshot()
    speed = bot.find(SPEED_UP, screen=screen, region=SPEED_UP_REGION)
    if speed is not None:
        bot.record(f"{LABEL}: researching, using Speed Up items")
        _speed_up(bot, speed)
        return True   # nghiên cứu đã bắt đầu từ lúc bấm Research, tăng tốc được hay không vẫn là đã làm
    if bot.find(TECH_TITLE, screen=screen) is None:
        bot.record(f"{LABEL}: researched (popup closed)")
        return True
    if changed_pixels(before, bot.crop(screen, *INFO_BOX)) >= CHANGED_PIXELS:
        bot.record(f"{LABEL}: researched instantly")
        return True
    bot.record(f"{LABEL}: Research did not start (not enough resources?)")
    return False


def _speed_up(bot, speed) -> bool:
    """Màn Research Speedup: Speedup Settings (_speedup_settings) -> Finish All. `speed`: nút Speed Up xanh của
    popup Researching (bấm để vào màn Speedup); None nếu đã ở / đang vào màn Speedup (từ icon Speed Up của menu
    Học viện). True khi đã bấm Finish All và màn Speedup không còn (hết thời gian) hoặc popup Finish All đã Confirm."""
    if speed is not None:
        bot.tap(*speed, delay=2)
    if bot.wait_for(SPEEDUP_TITLE, timeout=POPUP_WAIT) is None:
        bot.record(f"{LABEL}: Research Speedup screen not shown")
        return False
    if not _speedup_settings(bot):
        return False
    finish = bot.find(FINISH_ALL)
    if finish is None:
        bot.record(f"{LABEL}: Finish All not found")
        return False
    bot.tap(*finish, delay=1.5)
    confirm = bot.wait_for(CONFIRM, timeout=POPUP_WAIT)
    if confirm is not None:   # Finish All còn hỏi xác nhận
        bot.tap(*confirm, delay=RESULT_WAIT)
    if bot.find(SPEEDUP_TITLE) is not None and bot.find(CONFIRM) is None and bot.find(TECH_TITLE) is None:
        bot.record(f"{LABEL}: Finish All did not finish")
        return False
    bot.record(f"{LABEL}: speed up finished")
    return True


def _speedup_settings(bot) -> bool:
    """Lần đầu vào màn Research Speedup phải qua Speedup Settings: bấm "Speedup Settings >>" -> popup có ô tích
    "You can use corresponding common speedups when special speedups are insufficient" -> tích nếu chưa -> Confirm.
    Không thấy nút Speedup Settings hay popup thì bỏ qua (đã cài rồi). False khi popup mở mà không Confirm được."""
    settings = bot.find(SPEEDUP_SETTINGS)
    if settings is None:
        return True
    bot.tap(*settings, delay=1.5)
    confirm = bot.wait_for(CONFIRM, timeout=POPUP_WAIT)
    if confirm is None:
        return True
    unchecked = bot.find(COMMON_UNCHECKED, threshold=COMMON_THRESHOLD)
    if unchecked is not None:
        bot.tap(*unchecked, delay=1)
        bot.record(f"{LABEL}: ticked common speedups option")
    bot.tap(*confirm, delay=RESULT_WAIT)
    if bot.find(CONFIRM) is not None:
        bot.record(f"{LABEL}: speedup settings popup did not close")
        return False
    return True


def _leave(bot):
    """Back tới khi không còn màn Technology / Researching / Speedup / Academy (về thành)."""
    for _ in range(BACKS_AFTER):
        screen = bot.screenshot()
        if (bot.find(TECH_TITLE, screen=screen) is None and bot.find(SPEEDUP_TITLE, screen=screen) is None
                and bot.find(ACADEMY_TITLE, screen=screen) is None
                and bot.find(SPEED_UP, screen=screen, region=SPEED_UP_REGION) is None):
            break
        bot.back(delay=1.5)


TASK = Task(LABEL, FOLDER, key=KEY)
