"""
run.py — Daily Activities "Material Composing": phần sau Go (màn Items -> chọn vật phẩm có mũi tên xanh -> Compose, 3 lần).
Mở Quests -> Activity, tìm dòng, bấm Go: ../common.py open_task_or_finish. Ảnh / hằng số: constants.py.

Sau Go ra màn Items. Tìm vật phẩm có mũi tên xanh hướng lên (nhận bằng màu) phía trên LIST_BOTTOM % màn hình, chọn cái gần
nhất (y nhỏ nhất, rồi x nhỏ nhất); không có thì cuộn (~2 hàng, giống Open Gift Box) tối đa SCROLLS lần, vẫn không có thì báo xong hôm nay. Chọn ô -> nút Compose nhỏ -> màn Compose -> bấm Compose
đủ COMPOSE_GOAL lần -> báo xong hôm nay. Nút Compose xám -> Back 2 lần, chọn vật phẩm khác, chỉ bấm nốt số lần còn thiếu
(số đã bấm chỉ giữ trong bộ nhớ, không lưu DB).
"""
import cv2
import numpy as np

from ..common import Task, mark_task_done
from .constants import (
    ARROW_AREA,
    ARROW_HSV,
    ARROW_SIZE,
    BACKS_AFTER,
    COMPOSE_BIG,
    COMPOSE_BIG_REGION,
    COMPOSE_BOX,
    COMPOSE_GOAL,
    COMPOSE_MIN_SATURATION,
    COMPOSE_SMALL,
    COMPOSE_TITLE,
    COMPOSE_WAIT,
    FOLDER,
    ITEMS_TITLE,
    ITEM_TAP_OFFSET,
    KEY,
    LABEL,
    LIST_BOTTOM,
    LIST_SWIPE,
    LIST_SWIPE_DURATION,
    LIST_TOP,
    MAX_ROUNDS,
    ROW_HEIGHT,
    SCREEN_WAIT,
    SCROLLS,
    SELECT_TRIES,
    SELECT_WAITS,
)


def after_go(bot) -> bool:
    """Sau khi open_task bấm Go (màn Items): chọn vật phẩm có mũi tên xanh -> Compose nhỏ -> màn Compose -> bấm Compose đủ
    COMPOSE_GOAL lần -> báo xong hôm nay. Không còn vật phẩm ghép được (sau SCROLLS lần cuộn) cũng báo xong. Nút Compose xám
    -> Back 2 lần, chọn vật phẩm khác, chỉ bấm nốt số lần còn thiếu. True nếu xong."""
    composed = 0
    for _ in range(MAX_ROUNDS):
        state = _pick_item(bot)
        if state == "none":
            bot.record(f"{LABEL}: no item can be composed, done")
            return _finish(bot)
        if state != "compose":
            return False
        composed, ok = _compose(bot, composed)
        if composed >= COMPOSE_GOAL:
            bot.record(f"{LABEL}: composed {composed} times, done")
            return _finish(bot)
        if not ok:
            return False
    bot.record(f"{LABEL}: not finished after {MAX_ROUNDS} rounds ({composed} composed)")
    return False


def _finish(bot) -> bool:
    """Báo xong hôm nay rồi Back tới khi rời màn Items / Compose."""
    mark_task_done(bot, TASK)
    for _ in range(BACKS_AFTER):
        screen = bot.screenshot()
        if bot.find(ITEMS_TITLE, screen=screen) is None and bot.find(COMPOSE_TITLE, screen=screen) is None:
            break
        bot.back(delay=1)
    return True


def _arrows(screen) -> list[tuple[int, int]]:
    """Tâm các mũi tên xanh hướng lên trong lưới vật phẩm, từ LIST_TOP tới LIST_BOTTOM % màn hình, theo thứ tự: hàng trên
    trước, cùng hàng thì trái trước."""
    (h0, h1), s_min, v_min = ARROW_HSV
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    mask = ((hsv[..., 0] >= h0) & (hsv[..., 0] <= h1) & (hsv[..., 1] > s_min) & (hsv[..., 2] > v_min)).astype(np.uint8)
    mask[:LIST_TOP] = 0
    mask[screen.shape[0] * LIST_BOTTOM // 100:] = 0
    _, _, stats, centers = cv2.connectedComponentsWithStats(mask)
    w0, w1, h_min, h_max = ARROW_SIZE
    found = [(int(cx), int(cy)) for (x, y, w, h, area), (cx, cy) in zip(stats[1:], centers[1:])
             if w0 <= w <= w1 and h_min <= h <= h_max and ARROW_AREA[0] <= area <= ARROW_AREA[1]]
    return sorted(found, key=lambda p: (p[1] // ROW_HEIGHT, p[0]))


def _pick_item(bot) -> str:
    """Màn Items: chọn vật phẩm có mũi tên xanh gần nhất rồi bấm Compose nhỏ. "compose" khi tới màn Compose; "none" khi hết
    vật phẩm ghép được (sau SCROLLS lần cuộn); "fail" khi không vào được màn / chọn SELECT_TRIES vật phẩm vẫn không ra Compose."""
    if bot.wait_for(ITEMS_TITLE, timeout=SCREEN_WAIT) is None:
        bot.record(f"{LABEL}: Items screen not shown")
        return "fail"
    tried: list[tuple[int, int]] = []
    scrolls = 0
    attempts = 0
    while True:
        bot.check()
        screen = bot.screenshot()
        arrows = [p for p in _arrows(screen) if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) > 8 for q in tried)]
        if not arrows:
            if scrolls >= SCROLLS:
                return "none"
            bot.swipe_percent(*LIST_SWIPE, duration=LIST_SWIPE_DURATION, delay=1)
            scrolls += 1
            tried.clear()
            continue
        x, y = arrows[0]
        tried.append((x, y))
        attempts += 1
        tap = (x + ITEM_TAP_OFFSET[0], y + ITEM_TAP_OFFSET[1])
        bot.log(f"{LABEL}: select item at {tap}")
        bot.tap(*tap)
        for _ in range(1 + SELECT_WAITS):
            bot.sleep(1)
            button = bot.find(COMPOSE_SMALL)
            if button is not None:
                bot.tap(*button, delay=1)
                if bot.wait_for(COMPOSE_TITLE, timeout=SCREEN_WAIT) is not None:
                    return "compose"
                bot.record(f"{LABEL}: Compose screen not shown")
                return "fail"
        if attempts >= SELECT_TRIES:
            bot.record(f"{LABEL}: no Compose button after selecting {attempts} items")
            return "fail"


def _compose_enabled(bot, screen) -> bool:
    """Nút Compose lớn còn xanh (xám = hết nguyên liệu): độ bão hoà màu trong khung nút."""
    x, y, w, h = COMPOSE_BOX
    box = bot.crop(screen, x, y, w, h)
    return float(cv2.cvtColor(box, cv2.COLOR_BGR2HSV)[..., 1].mean()) >= COMPOSE_MIN_SATURATION


def _compose(bot, composed: int) -> tuple[int, bool]:
    """Màn Compose: bấm Compose tới khi đủ COMPOSE_GOAL lần; mỗi lần kiểm tra lại nút không xám. Xám -> Back 2 lần (về
    Items). Trả (số lần đã bấm, True nếu còn đi tiếp được: đủ lần hoặc đã Back về Items)."""
    while composed < COMPOSE_GOAL:
        bot.check()
        screen = bot.screenshot()
        if bot.find(COMPOSE_TITLE, screen=screen) is None:
            bot.record(f"{LABEL}: not on Compose screen ({composed} composed), stop")
            return composed, False
        button = bot.find(COMPOSE_BIG, screen=screen, region=COMPOSE_BIG_REGION)
        if button is None or not _compose_enabled(bot, screen):
            bot.log(f"{LABEL}: Compose button gray ({composed} composed), back twice and choose another item")
            bot.back(delay=1)
            bot.back(delay=1)
            return composed, True
        bot.tap(*button, delay=COMPOSE_WAIT)
        composed += 1
        bot.log(f"{LABEL}: Compose {composed}/{COMPOSE_GOAL}")
    return composed, True


TASK = Task(LABEL, FOLDER, key=KEY)
