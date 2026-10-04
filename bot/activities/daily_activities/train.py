"""
train.py — phần sau Go dùng chung của các nhiệm vụ Daily train ở công trình (Troop Training, Trap Building),
giống King's Path Train Troop / Gather Troops (event/gather_troops/train_troop): dùng lại ảnh, toạ độ và các
bước của nó (menu công trình, Training Speedup, Finish All).

1. Công trình ở giữa -> bấm -> menu: icon `menu_icon` ("Train" / "Build"); công trình đang có mẻ thì menu có
   "Speed Up" -> màn speedup -> Finish All mẻ đó trước (không tính) -> mở lại menu.
2. Màn Train (nút "i" góc trên): còn mẻ đang train ("Training Speedup") -> bấm, Finish All trước.
3. Lần đầu ở màn Train: `first_tier` thì chọn cấp I (kings_path/train_troop/tier.py), không thì giữ loại / cấp
   đang hiện. Không nhập số: giữ số mặc định của ô (tối đa một lần train). Số mẻ = `batches(số mỗi mẻ)`.
4. Mỗi mẻ: Train -> nút thành "Training Speedup" -> bấm -> (lần đầu Speedup Settings -> tích ô -> Confirm) ->
   Finish All -> về màn Train. Đủ mẻ, nút Train hiện lại -> đánh dấu xong hôm nay, Back đóng màn Train.
"""
from typing import Callable

from ...common import find_first
from ...ocr import read_train_count
from ..event.gather_troops.train_troop.constants import (
    BUTTON_WAIT,
    FINISH_ALL,
    FINISH_ALL_POS,
    FINISH_ALL_TITLE,
    FINISH_WAIT,
    SPEED_UP,
    SPEEDUP_SETTINGS,
    SPEEDUP_SETTINGS_POS,
    SPEEDUP_TITLE,
    TRAIN_BUTTON,
    TRAIN_BUTTON_POS,
    TRAIN_BUTTON_REGION,
    TRAIN_COUNT_BOX,
    TRAIN_INFO,
    TRAIN_INFO_REGION,
    TRAIN_THRESHOLD,
    TRAIN_WAIT,
)
from ..event.gather_troops.train_troop.run import (
    _confirm_finish_all,
    _find_training_speedup,
    _open_building_menu,
    _pos_of,
)
from ..event.kings_path.train_troop.tier import choose_first_tier
from .common import Task, mark_task_done

MAX_STEPS = 60   # số vòng quét màn hình tối đa sau Go

_FINISH_DIALOG, _SPEEDUP, _TRAIN_SCREEN, _SPEED_UP_MENU, _MENU = (
    "finish_dialog", "speedup", "train_screen", "speed_up_menu", "menu")


def train_after_go(bot, task: Task, building: str, menu_icon: str, batches: Callable[[int], int], *,
                   also=(), speedup_title: str = SPEEDUP_TITLE, first_tier: bool = False) -> bool:
    """Sau khi open_task bấm Go: train ở công trình `building` (`also`: công trình khác cũng được) qua icon
    menu `menu_icon`; số mẻ = `batches(số mỗi mẻ)`. True nếu xong (đã đánh dấu xong hôm nay)."""
    name = task.label
    # Màn sau trước, màn trước sau; SPEED_UP trước icon menu (icon "View" khớp nhầm "Train").
    targets = [
        (FINISH_ALL_TITLE, _FINISH_DIALOG),
        (speedup_title, _SPEEDUP),
        (TRAIN_INFO, _TRAIN_SCREEN),
        (SPEED_UP, _SPEED_UP_MENU),
        (menu_icon, _MENU),
    ]
    regions = {TRAIN_INFO: TRAIN_INFO_REGION}
    thresholds = {menu_icon: TRAIN_THRESHOLD, SPEED_UP: TRAIN_THRESHOLD}
    _open_building_menu(bot, name, building, menu_icon, also=also)
    times = None        # số mẻ cần bấm Train (None = chưa tính)
    started = 0         # số mẻ đã bấm Train
    settings_done = False
    from_menu = False   # màn speedup mở từ menu công trình (mẻ có sẵn, không tính)
    for _ in range(MAX_STEPS):
        bot.check()
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets, regions=regions, thresholds=thresholds)
        if action == _FINISH_DIALOG:
            _confirm_finish_all(bot, screen)
            settings_done = True
        elif action == _SPEEDUP:
            if not settings_done:
                bot.tap(*_pos_of(bot, screen, SPEEDUP_SETTINGS, SPEEDUP_SETTINGS_POS), delay=BUTTON_WAIT)
            else:
                bot.log(f"{name}: Finish All (batch {started}/{times})")
                bot.tap(*_pos_of(bot, screen, FINISH_ALL, FINISH_ALL_POS), delay=FINISH_WAIT)
                if from_menu:
                    from_menu = False
                    _open_building_menu(bot, name, building, menu_icon, also=also)
        elif action == _SPEED_UP_MENU:
            bot.log(f"{name}: building busy, Speed Up from menu (not counted)")
            bot.tap(*pos, delay=BUTTON_WAIT)
            from_menu = True
        elif action == _MENU:
            bot.tap(*pos, delay=TRAIN_WAIT)
        elif action == _TRAIN_SCREEN:
            speedup = _find_training_speedup(bot, screen)
            if speedup is not None:
                # Mẻ đang train (có sẵn trước khi làm, hoặc mẻ vừa bấm): mở màn speedup.
                bot.tap(*speedup, delay=BUTTON_WAIT)
                continue
            if times is None:
                if first_tier and choose_first_tier(bot) is None:
                    bot.record(f"{name}: ERROR cannot choose tier 1 on Train screen")
                    return False
                batch = read_train_count(bot.crop(bot.screenshot(), *TRAIN_COUNT_BOX))
                if not batch:
                    bot.record(f"{name}: cannot read train count")
                    return False
                times = max(1, batches(batch))
                bot.log(f"{name}: {batch} per batch -> {times} batch(es)")
            if started >= times:
                bot.record(f"{name}: trained {started} batch(es), done")
                mark_task_done(bot, task)
                bot.back(delay=1)   # đóng màn Train
                return True
            train = bot.find(TRAIN_BUTTON, screen=screen, region=TRAIN_BUTTON_REGION)
            started += 1
            bot.log(f"{name}: Train batch {started}/{times}")
            bot.tap(*(train or TRAIN_BUTTON_POS), delay=BUTTON_WAIT)
        else:
            bot.sleep(1)
    bot.record(f"{name}: not finished after {MAX_STEPS} steps")
    return False
