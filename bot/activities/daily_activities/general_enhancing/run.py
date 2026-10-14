"""
run.py — Daily Activities "General Enhancing": handler các action riêng của nhiệm vụ (tướng -> Cultivate 5 lần (sau Go bấm (30, 50) như bản C#)).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go) — giống Gather Troops Cultivate Generals
(event/gather_troops/cultivate_generals, dùng lại ảnh / ngưỡng / vùng / `_open_last_general`) cho tới màn Cultivate:
1. Danh sách Generals: tim lọc yêu thích chưa tích -> bấm; đã tích -> kéo nhanh xuống cuối, mở tướng cuối.
2. Màn tướng: "Cultivate" -> màn Cultivate (mở ở tab Cultivate Once).
3. Phải ở tab **Cultivate Once**: đang ở tab Quick Cultivate thì bấm sang Cultivate Once.
4. Thấy "Cancel" (kết quả lần trước) -> bấm Cancel; thấy "Gold Cultivate" -> bấm, chờ kết quả (Cancel), +1.
   Đủ GOLD_GOAL = 5 lần -> bấm Cancel bỏ kết quả rồi đánh dấu xong hôm nay (True).
"""
from ....common import find_first
from ...event.gather_troops.cultivate_generals.constants import (
    CANCEL,
    CULTIVATE_BUTTONS,
    FAVORITE_OFF,
    FAVORITE_ON,
    OPEN_CULTIVATE,
    ON_GENERALS_LIST,
    ON_QUICK_CULTIVATE,
    QUICK_CULTIVATE_SELECTED,
    REGIONS as EVENT_REGIONS,
    THRESHOLDS,
    TICK_FAVORITE,
)
from ...event.gather_troops.cultivate_generals.run import _open_last_general
from ..common import Task, mark_task_done, tap_first
from .constants import (
    ACTIONS,
    AFTER_OPEN_TAP,
    DONE_IMAGES,
    FOLDER,
    FOLDER_PATH,
    GOLD_CULTIVATE,
    GOLD_GOAL,
    GOLD_REGION,
    KEY,
    LABEL,
    MAX_STEPS,
    RESULT_WAIT,
)


def handle(bot, action, pos, screen):
    if action == "cultivate":
        bot.tap(*pos, delay=3)
    elif action == "cultivate_loop":
        base = f"{FOLDER_PATH}/TapEnhancing"
        templates = (f"{base}/Agree.png", f"{base}/Disagree.png")
        if tap_first(bot, templates, 5):
            bot.tap(110, 666)
            bot.back(delay=2)
        return True
    return False


_CANCEL, _GOLD = "cancel", "gold"
# Màn sau trước, màn trước sau. Tab Quick Cultivate "đang chọn" xét trước (nó khớp 0,90 khi chưa chọn, dưới ngưỡng 0,95).
_TARGETS = [
    (QUICK_CULTIVATE_SELECTED, ON_QUICK_CULTIVATE),
    (CANCEL, _CANCEL),
    (GOLD_CULTIVATE, _GOLD),
    *[(path, OPEN_CULTIVATE) for path in CULTIVATE_BUTTONS],
    (FAVORITE_OFF, TICK_FAVORITE),
    (FAVORITE_ON, ON_GENERALS_LIST),
]
_REGIONS = {**EVENT_REGIONS, GOLD_CULTIVATE: GOLD_REGION}


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: tới màn Cultivate (như Event), ở tab Cultivate Once: Cancel thì bấm, Gold
    Cultivate thì bấm; đủ GOLD_GOAL lần thì Cancel rồi đánh dấu xong hôm nay, True."""
    done = 0
    for _ in range(MAX_STEPS):
        bot.check()
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, _TARGETS, regions=_REGIONS, thresholds=THRESHOLDS)
        if action == ON_QUICK_CULTIVATE:
            # Đang ở tab Quick Cultivate: sang tab Cultivate Once (đối xứng qua giữa màn).
            bot.log(f"{LABEL}: on Quick Cultivate tab, switch to Cultivate Once")
            bot.tap(screen.shape[1] - pos[0], pos[1], delay=2)
        elif action == _CANCEL:
            bot.tap(*pos, delay=1)
            if done >= GOLD_GOAL:
                bot.record(f"{LABEL}: Gold Cultivate x{done}, done")
                mark_task_done(bot, TASK)
                return True
        elif action == _GOLD:
            bot.tap(*pos, delay=1)
            if bot.wait_for(CANCEL, timeout=RESULT_WAIT) is None:
                bot.record(f"{LABEL}: Gold Cultivate gave no result (not enough gold?), stop ({done} done)")
                return False
            done += 1
            bot.log(f"{LABEL}: Gold Cultivate {done}/{GOLD_GOAL}")
        elif action == OPEN_CULTIVATE:
            bot.tap(*pos, delay=2)
        elif action == TICK_FAVORITE:
            bot.tap(*pos, delay=1)
        elif action == ON_GENERALS_LIST:
            _open_last_general(bot)
        else:
            bot.sleep(1)
    bot.record(f"{LABEL}: not finished after {MAX_STEPS} steps ({done} done)")
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
