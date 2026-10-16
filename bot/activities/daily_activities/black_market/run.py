"""
run.py — Daily Activities "Black Market": phần làm nhiệm vụ sau Go (after_go) (Chợ -> Black Market, mua 3 món tài nguyên).
Mở dòng Activity + bấm Go: ../common.py (open_task_or_finish, daily_job).

Luồng mới (after_go, sau khi open_task bấm Go): giống hệt King's Path Black Market sau Go
(event/kings_path/black_market) — Chợ -> "Black Market" -> buy_items (mua món không trả kim cương, mua hết bộ thì
Instant Refresh) cho đủ BUY_GOAL lần -> Back, đánh dấu xong hôm nay. Dừng giữa chừng -> không đánh dấu.
"""
from ...event.kings_path.black_market.run import buy_items, open_black_market
from ..common import Task, mark_task_done
from .constants import BUY_GOAL, FOLDER, KEY, LABEL


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


TASK = Task(LABEL, FOLDER, key=KEY)
