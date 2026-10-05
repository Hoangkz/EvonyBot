"""
run.py — Daily Activities "Black Market": handler các action riêng của nhiệm vụ (Chợ -> Black Market, mua 3 món tài nguyên).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go): giống hệt King's Path Black Market sau Go
(event/kings_path/black_market) — Chợ -> "Black Market" -> buy_items (mua món không trả kim cương, mua hết bộ thì
Instant Refresh) cho đủ BUY_GOAL lần -> Back, đánh dấu xong hôm nay. Dừng giữa chừng -> không đánh dấu.
"""
from ...event.kings_path.black_market.run import buy_items, open_black_market
from ..common import Task, mark_task_done, tap_first
from .constants import ACTIONS, BUY_GOAL, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "market":
        bot.tap(*pos, delay=2)
    elif action == "buy":
        base = f"{FOLDER_PATH}/Buy"
        templates = tuple(f"{base}/{name}" for name in
                          ("food1.png", "lumber1.png", "ore1.png", "stone1.png"))

        def confirm():
            bot.tap(190, 415, delay=4)
        # (190, 575) used to change page in the C# era. In Evony 5.25 it is
        # "Instant Refresh" and costs gems, so never use it as a fallback.
        tap_first(bot, templates, 3, after=confirm)
        bot.back(delay=2)
        return True
    return False



def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: mua BUY_GOAL lần ở Black Market. True nếu xong (đã đánh dấu xong
    hôm nay)."""
    if not open_black_market(bot, LABEL):
        return False

    def finish(message: str):
        bot.log(f"{LABEL}: {message}")
        bot.back(delay=1)
        mark_task_done(bot, TASK)

    return buy_items(bot, 0, BUY_GOAL, finish, name=LABEL)


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
