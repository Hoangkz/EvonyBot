"""
run.py — Daily Activities "Greet Champion": phần sau Go (Thành chính -> trái tim / icon Champion -> Greet tới 10/10).
Mở Quests -> Activity, tìm dòng, bấm Go: ../common.py open_task_or_finish. Ảnh / hằng số: constants.py.
Đủ GREET_REQUIRED lần: lưu xong hôm nay ngay rồi chào tiếp; bị ngắt thì MORE_JOB (không qua Go) nối tiếp tới 10/10.

Sau Go về thành chính. Thấy trái tim trên đầu Keep -> bấm thẳng; không thấy -> open_menu (Keep -> icon "Champion").
Ra màn Champion: mỹ nữ chưa mở khoá (hiện nút Unlock) -> CHỈ lúc đó bấm mũi tên phải tới mỹ nữ có nút Greet; mũi tên phải
xám thì sang trái; cả hai xám -> hết mỹ nữ để chào. Tới 10/10, hoặc hết mỹ nữ chào được -> báo xong
hôm nay -> Back về thành.
"""
import time

import cv2

from ...event.city_building import KEEP
from ...event.kings_path.building import open_menu
from ....city.city_map import reach_building
from ....common import to_city
from ...result import save_errors
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
    GREET_MAX,
    GREET_REQUIRED,
    MORE_KEY,
    MORE_LABEL,
    greet_key,
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
    """Sau khi open_task bấm Go: vào màn Champion rồi chào (xem _greet_loop). Đủ GREET_REQUIRED lần thì lưu xong hôm nay (KEY)
    ngay rồi chào tiếp. True (và báo xong hôm nay) khi chào xong / hết giờ; False nếu không vào được màn Champion hoặc rời
    màn giữa chừng (đã đủ lần tối thiểu thì "xong hôm nay" đã lưu rồi)."""
    if not _open_champion(bot):
        return False
    outcome = _greet_loop(bot, on_greet=lambda n: n == GREET_REQUIRED and bot.mark_daily_done(KEY))
    if outcome == LOST:
        return False
    _leave(bot)
    mark_task_done(bot, TASK)
    if outcome in (FULL, NONE_LEFT):
        bot.mark_daily_done(MORE_KEY)
    return True


@save_errors(MORE_KEY)
def run_more(ctx, settings):
    """Việc nối tiếp: tới Keep (city_map.reach_building) -> trái tim / Keep -> Champion -> chào tiếp tới 10/10 (hoặc hết mỹ nữ), lưu MORE_KEY. Bị ngắt
    giữa chừng: không lưu, lượt sau làm tiếp (số lần chào đếm trong DB, màn Champion cho biết 10/10)."""
    ctx.log(f"Daily Activities: {MORE_LABEL}")
    to_city(ctx)
    if not reach_building(ctx, MORE_LABEL, KEEP):   # thấy Keep thì làm luôn; có route thì đi; chưa có route thì tìm + lưu DB
        return
    if not _open_champion(ctx):
        return
    outcome = _greet_loop(ctx)
    if outcome == LOST:
        return
    _leave(ctx)
    if outcome in (FULL, NONE_LEFT):
        ctx.mark_daily_done(MORE_KEY)


def more_done(ctx, settings) -> bool:
    """Bỏ qua khi: Daily Greet chưa xong (làm theo dòng Activity trước), hoặc đã chào đủ hôm nay."""
    return not ctx.is_daily_done(KEY) or ctx.is_daily_done(MORE_KEY) or greets_today(ctx) >= GREET_MAX


MORE_JOB = {"run": run_more, "enabled": lambda settings: settings.get(LABEL) is True, "done": more_done}


def greets_today(bot) -> int:
    return sum(1 for n in range(1, GREET_MAX + 1) if bot.is_daily_done(greet_key(n)))


FULL, NONE_LEFT, TIMEOUT, LOST = "full", "none_left", "timeout", "lost"


def _greet_loop(bot, on_greet=None) -> str:
    """Đang chờ / đã ở màn Champion: lặp (không chờ gì, trừ NEXT_WAIT sau khi bấm mũi tên): popup xác nhận -> tích + Confirm;
    Greet 10/10 -> FULL; Unlock -> đổi mỹ nữ (hết cả hai mũi tên -> NONE_LEFT); Greet sáng -> Greet + bấm giữa (đếm vào DB,
    gọi `on_greet(số lần hôm nay)`); Greet khoá -> bấm giữa. TIMEOUT khi quá TASK_MAX_SECONDS; LOST nếu không vào / rời màn
    Champion giữa chừng (đã Back về thành)."""
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
            return LOST
        entered = True
        if bot.find(GREET_FULL, screen=screen, threshold=GREET_FULL_THRESHOLD) is not None:
            bot.record(f"{LABEL}: Greet 10/10")
            return FULL
        if bot.find(UNLOCK_BUTTON, screen=screen, threshold=UNLOCK_THRESHOLD) is not None:
            direction = _next_champion(bot, screen, direction)
            if direction is None:
                bot.record(f"{LABEL}: both arrows greyed out, no champion left to greet")
                return NONE_LEFT
            continue
        button = bot.find(GREET_BUTTON, screen=screen, threshold=GREET_THRESHOLD)
        if button is None:   # Greet đang khoá: chỉ bấm giữa
            bot.tap_percent(*GREET_MIDDLE, delay=0)
            continue
        bot.tap(*button, delay=0)
        for _ in range(MIDDLE_TAPS):
            bot.tap_percent(*GREET_MIDDLE, delay=0)
        count = greets_today(bot) + 1
        bot.mark_daily_done(greet_key(count))
        if on_greet is not None:
            on_greet(count)
    bot.record(f"{LABEL}: time limit {TASK_MAX_SECONDS}s reached")
    return TIMEOUT


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
