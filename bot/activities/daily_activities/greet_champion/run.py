"""
run.py — Daily Activities "Greet Champion": phần sau Go (Thành chính -> trái tim / icon Champion -> Greet tới 10/10).
Mở Quests -> Activity, tìm dòng, bấm Go: ../common.py open_task_or_finish. Ảnh / hằng số: constants.py.

Sau Go về thành chính. Thấy trái tim trên đầu Keep -> bấm thẳng; không thấy -> open_menu (Keep -> icon "Champion").
Ra màn Champion: mỹ nữ chưa mở khoá (hiện nút Unlock) -> CHỈ lúc đó bấm mũi tên phải tới mỹ nữ có nút Greet; mũi tên phải
xám thì sang trái; cả hai xám -> hết mỹ nữ để chào. Tới 10/10, hoặc hết mỹ nữ chào được -> báo xong
hôm nay -> Back về thành.
"""
import time

import cv2

from ...event.city_building import KEEP
from ...event.kings_path.building import open_menu
from ..common import Task, mark_task_done
from ..constants import MAIN_MORE
from .constants import (
    ARROW_BOX_LEFT,
    ARROW_BOX_RIGHT,
    ARROW_BRIGHT,
    ARROW_LEFT,
    ARROW_MIN_SATURATION,
    ARROW_RIGHT,
    BACKS_AFTER,
    CHAMPION_TITLE,
    CONFIRM,
    DONT_SHOW,
    FOLDER,
    GREET_FULL,
    GREET_FULL_THRESHOLD,
    GREET_MIDDLE,
    GREET_BUTTON,
    GREET_THRESHOLD,
    HEART,
    KEY,
    LABEL,
    MENU_CHAMPION,
    MIDDLE_TAPS,
    NEXT_WAIT,
    SCREEN_WAIT,
    TASK_MAX_SECONDS,
    UNLOCK_BUTTON,
    UNLOCK_THRESHOLD,
)

def after_go(bot) -> bool:
    """Sau khi open_task bấm Go: vào màn Champion rồi lặp (không chờ gì, trừ 3 giây sau khi bấm mũi tên): popup xác
    nhận -> tích + Confirm; Greet 10/10 -> xong; Unlock -> đổi mỹ nữ; Greet sáng -> Greet + bấm giữa; Greet khoá -> bấm giữa. True (và báo xong hôm nay) khi xong; False nếu không vào được màn Champion, rời màn Champion giữa
    chừng, hoặc không vào được sau SCREEN_WAIT giây."""
    if not _open_champion(bot):
        return False
    start = time.monotonic()
    end = start + TASK_MAX_SECONDS
    direction = ARROW_RIGHT   # đã bấm hết mũi tên phải thì sang trái
    entered = False
    while time.monotonic() < end:
        screen = bot.screenshot()
        confirm = bot.find(CONFIRM, screen=screen)
        if confirm is not None:   # popup "Are you sure you want to interact with ...?"
            dont_show = bot.find(DONT_SHOW, screen=screen)
            if dont_show is not None:
                bot.tap(*dont_show, delay=0)
            bot.tap(*confirm, delay=0)
            continue
        if bot.find(CHAMPION_TITLE, screen=screen) is None:
            if not entered and time.monotonic() - start < SCREEN_WAIT:
                continue   # màn Champion đang mở
            bot.record(f"{LABEL}: not on the Champion screen")
            _leave(bot)
            return False
        entered = True
        if bot.find(GREET_FULL, screen=screen, threshold=GREET_FULL_THRESHOLD) is not None:
            bot.record(f"{LABEL}: Greet 10/10")
            break
        if bot.find(UNLOCK_BUTTON, screen=screen, threshold=UNLOCK_THRESHOLD) is not None:
            direction = _next_champion(bot, screen, direction)
            if direction is None:
                bot.record(f"{LABEL}: both arrows greyed out, no champion left to greet")
                break
            continue
        button = bot.find(GREET_BUTTON, screen=screen, threshold=GREET_THRESHOLD)
        if button is None:   # Greet đang khoá: chỉ bấm giữa
            bot.tap_percent(*GREET_MIDDLE, delay=0)
            continue
        bot.tap(*button, delay=0)
        for _ in range(MIDDLE_TAPS):
            bot.tap_percent(*GREET_MIDDLE, delay=0)
    else:
        bot.record(f"{LABEL}: time limit {TASK_MAX_SECONDS}s reached")
    _leave(bot)
    mark_task_done(bot, TASK)
    return True


def _next_champion(bot, screen, direction):
    """Mỹ nữ chưa mở khoá: bấm mũi tên `direction` (phải trước), chờ NEXT_WAIT giây. Mũi tên đó xám thì đổi sang
    trái (trả hướng mới, chưa bấm); trái cũng xám -> None."""
    box = ARROW_BOX_RIGHT if direction == ARROW_RIGHT else ARROW_BOX_LEFT
    if _arrow_active(screen, box):
        bot.tap_percent(*direction, delay=NEXT_WAIT)
        return direction
    return ARROW_LEFT if direction == ARROW_RIGHT else None


def _open_champion(bot) -> bool:
    """Trái tim trên đầu Keep thì bấm thẳng, không thì Keep -> icon Champion (không chờ; after_go tự đợi màn
    Champion hiện). False nếu không thấy trái tim lẫn icon."""
    heart = bot.find(HEART)
    if heart is not None:
        bot.tap(*heart, delay=0)
        return True
    _, pos = open_menu(bot, LABEL, KEEP, {"champion": MENU_CHAMPION})
    if pos is None:
        return False
    bot.tap(*pos, delay=0)
    return True


def _arrow_active(screen, box) -> bool:
    """Mũi tên còn bấm được (vàng) hay đã xám: độ bão hoà trung bình của các điểm sáng trong hình thoi."""
    x0, y0, x1, y1 = box
    hsv = cv2.cvtColor(screen[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    bright = hsv[..., 2] > ARROW_BRIGHT
    return bool(bright.any()) and hsv[..., 1][bright].mean() >= ARROW_MIN_SATURATION


def _leave(bot):
    """Về màn thành sạch (thấy nút "•••"), không chờ: Back một lần rồi xét ảnh liên tục tới khi màn đổi. Màn thành
    sạch thì không Back (sẽ hỏi thoát game)."""
    for _ in range(BACKS_AFTER):
        screen = bot.screenshot()
        if bot.find(MAIN_MORE, screen=screen) is not None:
            return
        on_champion = bot.find(CHAMPION_TITLE, screen=screen) is not None
        bot.back(delay=0)
        end = time.monotonic() + SCREEN_WAIT
        while time.monotonic() < end:   # chờ màn đổi bằng cách xét ảnh, không ngủ
            screen = bot.screenshot()
            if bot.find(MAIN_MORE, screen=screen) is not None:
                return
            if (bot.find(CHAMPION_TITLE, screen=screen) is not None) != on_champion:
                break


TASK = Task(LABEL, FOLDER, key=KEY)
