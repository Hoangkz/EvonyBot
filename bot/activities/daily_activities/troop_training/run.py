"""
run.py — Daily Activities "Troop Training": handler các action riêng của nhiệm vụ (doanh trại -> Train).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go) giống King's Path Train Troop (event/kings_path/train_troop),
dùng lại các bước chung của event/gather_troops/train_troop:
1. Công trình train ngẫu nhiên 1 trong 4 loại ở giữa -> bấm -> menu: "Train" (đang có mẻ train thì "Speed Up"
   -> Training Speedup -> Finish All mẻ đó trước, không tính, rồi mở lại menu).
2. Màn Train: còn mẻ đang train -> Training Speedup trước. Chọn cấp I (kings_path/train_troop/tier.py). Không
   nhập số: số mặc định của ô (tối đa một lần train, OCR) -> số mẻ = ceil(TRAIN_GOAL / số mỗi mẻ).
3. Mỗi mẻ: Train -> nút thành "Training Speedup" -> bấm -> (lần đầu: Speedup Settings -> tích ô -> Confirm)
   -> Finish All -> về màn Train. Đủ mẻ và nút Train hiện lại -> xong hôm nay (mark_task_done).
"""
import math

from ....common import delay, find_first
from ....ocr import read_train_count
from ...event.city_building import TROOP, TROOP_BUILDINGS
from ...event.gather_troops.train_troop.constants import (
    BUTTON_WAIT,
    FINISH_ALL,
    FINISH_ALL_POS,
    FINISH_ALL_TITLE,
    FINISH_WAIT,
    SPEED_UP,
    SPEEDUP_SETTINGS,
    SPEEDUP_SETTINGS_POS,
    SPEEDUP_TITLE,
    TRAIN,
    TRAIN_BUTTON,
    TRAIN_BUTTON_POS,
    TRAIN_BUTTON_REGION,
    TRAIN_COUNT_BOX,
    TRAIN_INFO,
    TRAIN_INFO_REGION,
    TRAIN_THRESHOLD,
    TRAIN_WAIT,
)
from ...event.gather_troops.train_troop.run import (
    _confirm_finish_all,
    _find_training_speedup,
    _open_building_menu,
    _pos_of,
)
from ...event.kings_path.train_troop.tier import choose_first_tier
from ..common import Task, mark_task_done, replace_text
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL, MAX_STEPS, TRAIN_GOAL


def handle(bot, action, pos, screen):
    if action == "interface":
        bot.swipe_percent(30, 65, 80, 65, duration=0.3, delay=1)
    elif action == "soldier":
        bot.tap(336, 582)
        replace_text(bot, "500", 3)
        delay(bot, 5)
        bot.tap(300, 660)
    elif action == "speed":
        bot.tap(*pos, delay=4)
        bot.tap(100, 670)
    return False


# Màn sau trước, màn trước sau (giống King's Path); SPEED_UP trước TRAIN (icon "View" khớp nhầm TRAIN).
_FINISH_DIALOG, _SPEEDUP, _TRAIN_SCREEN, _SPEED_UP_MENU, _TRAIN_MENU = (
    "finish_dialog", "speedup", "train_screen", "speed_up_menu", "train_menu")
_TARGETS = [
    (FINISH_ALL_TITLE, _FINISH_DIALOG),
    (SPEEDUP_TITLE, _SPEEDUP),
    (TRAIN_INFO, _TRAIN_SCREEN),
    (SPEED_UP, _SPEED_UP_MENU),
    (TRAIN, _TRAIN_MENU),
]
_REGIONS = {TRAIN_INFO: TRAIN_INFO_REGION}
_THRESHOLDS = {TRAIN: TRAIN_THRESHOLD, SPEED_UP: TRAIN_THRESHOLD}


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: train cấp I cho đủ TRAIN_GOAL lính (số mặc định mỗi mẻ, không
    nhập số). True nếu xong (đã đánh dấu xong hôm nay); False nếu lỗi / hết MAX_STEPS vòng."""
    _open_building_menu(bot, LABEL, TROOP, TRAIN, also=TROOP_BUILDINGS)
    times = None        # số mẻ cần bấm Train (None = chưa chọn cấp / tính)
    started = 0         # số mẻ đã bấm Train
    settings_done = False
    from_menu = False   # màn speedup mở từ menu công trình (mẻ có sẵn, không tính)
    for _ in range(MAX_STEPS):
        bot.check()
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, _TARGETS, regions=_REGIONS, thresholds=_THRESHOLDS)
        if action == _FINISH_DIALOG:
            _confirm_finish_all(bot, screen)
            settings_done = True
        elif action == _SPEEDUP:
            if not settings_done:
                bot.tap(*_pos_of(bot, screen, SPEEDUP_SETTINGS, SPEEDUP_SETTINGS_POS), delay=BUTTON_WAIT)
            else:
                bot.log(f"{LABEL}: Finish All (batch {started}/{times})")
                bot.tap(*_pos_of(bot, screen, FINISH_ALL, FINISH_ALL_POS), delay=FINISH_WAIT)
                if from_menu:
                    from_menu = False
                    _open_building_menu(bot, LABEL, TROOP, TRAIN, also=TROOP_BUILDINGS)
        elif action == _SPEED_UP_MENU:
            bot.log(f"{LABEL}: building already training, Speed Up from menu (not counted)")
            bot.tap(*pos, delay=BUTTON_WAIT)
            from_menu = True
        elif action == _TRAIN_MENU:
            bot.tap(*pos, delay=TRAIN_WAIT)
        elif action == _TRAIN_SCREEN:
            speedup = _find_training_speedup(bot, screen)
            if speedup is not None:
                # Mẻ đang train (có sẵn trước khi làm, hoặc mẻ vừa bấm): mở màn speedup.
                bot.tap(*speedup, delay=BUTTON_WAIT)
                continue
            if times is None:
                if choose_first_tier(bot) is None:
                    bot.record(f"{LABEL}: ERROR cannot choose tier 1 on Train screen")
                    return False
                batch = read_train_count(bot.crop(bot.screenshot(), *TRAIN_COUNT_BOX))
                if not batch:
                    bot.record(f"{LABEL}: cannot read train count")
                    return False
                times = math.ceil(TRAIN_GOAL / batch)
                bot.log(f"{LABEL}: tier 1, {batch} per batch -> {times} batch(es) (goal {TRAIN_GOAL})")
            if started >= times:
                bot.record(f"{LABEL}: trained {started} batch(es), done")
                mark_task_done(bot, TASK)
                bot.back(delay=1)   # đóng màn Train
                return True
            train = bot.find(TRAIN_BUTTON, screen=screen, region=TRAIN_BUTTON_REGION)
            started += 1
            bot.log(f"{LABEL}: Train batch {started}/{times}")
            bot.tap(*(train or TRAIN_BUTTON_POS), delay=BUTTON_WAIT)
        else:
            bot.sleep(1)
    bot.record(f"{LABEL}: not finished after {MAX_STEPS} steps")
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
