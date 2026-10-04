"""
run.py — Daily Activities "Trap Buiding": handler các action riêng của nhiệm vụ (công trình bẫy -> Build (nhãn Trap Buiding giữ như bản C# / tab UI)).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go): ../train.py train_after_go, giống Gather Troops Defense Force
(event/gather_troops/defense_force) — Trap Factory -> "Build" -> bẫy đang hiện khi vào (không tìm loại / cấp)
-> số mặc định của ô (không nhập) -> ceil(TRAP_GOAL / số mỗi mẻ) mẻ -> Trap Building Speedup -> Finish All -> xong hôm nay.
"""
import math

from ....common import delay
from ...event.city_building import DEFENSE_FORCE
from ...event.gather_troops.defense_force.constants import BUILD, SPEEDUP_TITLE
from ..common import Task, replace_text
from ..train import train_after_go
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL, TRAP_GOAL


def handle(bot, action, pos, screen):
    if action == "interface":
        # In 5.25 the four trap types are fixed buttons, not a troop carousel.
        # Pick the visible tier-I trap and submit the requested amount directly.
        bot.tap(95, 453, delay=1)
        bot.tap(336, 582)
        replace_text(bot, "150", 3)
        delay(bot, 2)
        bot.tap(300, 660)
    elif action == "build":
        bot.tap(336, 582)
        replace_text(bot, "150", 3)
        delay(bot, 2)
        bot.tap(300, 660)
    elif action == "speed":
        bot.tap(*pos, delay=2)
        bot.tap(100, 670, delay=2)
        bot.back(delay=2)
    return False


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: xây bẫy đang hiện khi vào màn Train bẫy cho đủ TRAP_GOAL (số mặc
    định mỗi mẻ, không nhập số). True nếu xong (đã đánh dấu xong hôm nay)."""
    return train_after_go(bot, TASK, DEFENSE_FORCE, BUILD, lambda batch: math.ceil(TRAP_GOAL / batch),
                          speedup_title=SPEEDUP_TITLE)


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
