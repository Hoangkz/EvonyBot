"""
run.py — Daily Activities "General Enhancing": handler các action riêng của nhiệm vụ (tướng -> Cultivate 5 lần (sau Go bấm (30, 50) như bản C#)).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go) — như Gather Troops Cultivate Generals
(event/gather_troops/cultivate_generals, dùng lại ảnh / bước tới màn tướng) nhưng Gold Cultivate thay Quick
Cultivate x100 (không tốn kim cương), đúng CULTIVATE_GOAL lần ("Cultivate Generals for 5 time(s)"):
1. Danh sách Generals: tim lọc yêu thích chưa tích -> bấm; đã tích -> kéo xuống cuối, mở tướng cuối.
2. Màn tướng: "Cultivate" -> màn Cultivate (giao diện cũ).
3. Mỗi lần: "Gold Cultivate" -> chờ kết quả (nút Cancel) -> +1 -> Cancel (bỏ kết quả như Event).
4. Đủ CULTIVATE_GOAL lần -> Back về thành, đánh dấu xong hôm nay. Bấm mà không ra kết quả (thiếu vàng / game
   chậm) -> không tính, dừng, không đánh dấu.
"""
from ....common import find_first
from ...event.gather_troops.cultivate_generals.constants import (
    CULTIVATE_BUTTONS,
    CULTIVATE_REGION,
    FAVORITE_OFF,
    FAVORITE_ON,
    FAVORITE_REGION,
)
from ...event.gather_troops.cultivate_generals.run import _open_last_general
from ..common import Task, mark_task_done, tap_first
from .constants import (
    ACTIONS,
    AFTER_OPEN_TAP,
    BACKS_AFTER,
    CANCEL_REGION,
    CULTIVATE_CANCEL,
    CULTIVATE_GOAL,
    DONE_IMAGES,
    FAVORITE_OFF_THRESHOLD,
    FOLDER,
    FOLDER_PATH,
    GOLD_CULTIVATE,
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


_CANCEL, _GOLD, _OPEN_CULTIVATE, _LIST, _TICK = "cancel", "gold", "open_cultivate", "list", "tick"
# Màn sau trước, màn trước sau.
_TARGETS = [
    (CULTIVATE_CANCEL, _CANCEL),
    (GOLD_CULTIVATE, _GOLD),
    *[(path, _OPEN_CULTIVATE) for path in CULTIVATE_BUTTONS],
    (FAVORITE_ON, _LIST),
    (FAVORITE_OFF, _TICK),
]
_REGIONS = {
    CULTIVATE_CANCEL: CANCEL_REGION,
    FAVORITE_ON: FAVORITE_REGION,
    FAVORITE_OFF: FAVORITE_REGION,
    **{path: CULTIVATE_REGION for path in CULTIVATE_BUTTONS},
}
_THRESHOLDS = {FAVORITE_OFF: FAVORITE_OFF_THRESHOLD}


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: Gold Cultivate tướng cuối (lọc yêu thích) CULTIVATE_GOAL lần. True nếu
    xong (đã đánh dấu xong hôm nay)."""
    done = 0
    for _ in range(MAX_STEPS):
        bot.check()
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, _TARGETS, regions=_REGIONS, thresholds=_THRESHOLDS)
        if action == _CANCEL:
            bot.tap(*pos, delay=1)
        elif action == _GOLD:
            if done >= CULTIVATE_GOAL:
                bot.record(f"{LABEL}: Gold Cultivate x{done}, done")
                for _ in range(BACKS_AFTER):
                    bot.back(delay=1)
                mark_task_done(bot, TASK)
                return True
            bot.tap(*pos, delay=1)
            if bot.wait_for(CULTIVATE_CANCEL, timeout=RESULT_WAIT) is None:
                bot.record(f"{LABEL}: Gold Cultivate gave no result (not enough gold?), stop ({done} done)")
                return False
            done += 1
            bot.log(f"{LABEL}: Gold Cultivate {done}/{CULTIVATE_GOAL}")
        elif action == _OPEN_CULTIVATE:
            bot.tap(*pos, delay=2)
        elif action == _LIST:
            _open_last_general(bot)
        elif action == _TICK:
            bot.tap(*pos, delay=1)
        else:
            bot.sleep(1)
    bot.record(f"{LABEL}: not finished after {MAX_STEPS} steps ({done} done)")
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
