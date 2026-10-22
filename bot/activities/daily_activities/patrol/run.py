"""
run.py — Daily Activities "Patrol": phần làm nhiệm vụ sau Go (after_go) (Tường thành -> Patrol 3 lần) và việc nối tiếp
`MORE_JOB` (patrol tiếp cho đủ 10 lượt). Mở dòng Activity + bấm Go: ../common.py (open_task_or_finish, daily_job).

after_go (sau khi open_task bấm Go): giống hệt King's Path Patrol sau Go (event/kings_path/patrol) —
Tường thành -> "Patrol" -> màn Patrol -> patrol_rounds (Select All -> Patrol -> Refresh). Đủ PATROL_REQUIRED lượt thì lưu
"xong hôm nay" vào DB ngay rồi patrol tiếp (tới khi bị ngắt hoặc đủ 10 lượt / hết Refresh).
MORE_JOB: bị ngắt thì việc này nối tiếp — tìm thành, Tường thành, Patrol cho tới đủ 10 lượt trong ngày.
"""
from ...event.city_building import WALLS
from ...event.kings_path.building import open_building
from ...event.kings_path.patrol.constants import MENU_PATROL, PATROL_TITLE, ROUNDS_PER_DAY
from ...event.kings_path.patrol.run import patrol_rounds, rounds_today
from ....city.city_map import reach_building
from ....common import to_city
from ...result import save_errors
from ..common import Task, mark_task_done
from .constants import FOLDER, KEY, LABEL, MORE_KEY, MORE_LABEL, PATROL_GOAL, PATROL_REQUIRED


def after_go(bot) -> bool:
    """Luồng sau khi open_task bấm Go: patrol; đủ PATROL_REQUIRED lượt -> lưu xong hôm nay (KEY) rồi patrol tiếp tới đủ lượt
    trong ngày (hoặc hết Refresh -> Back, xong cả việc nối tiếp). True nếu chạy hết; False nếu không mở được màn Patrol /
    lỗi giữa chừng (nếu đã đủ lượt tối thiểu thì "xong hôm nay" đã lưu rồi)."""
    if not open_building(bot, LABEL, WALLS, MENU_PATROL, PATROL_TITLE):
        return False

    def finish(message: str, _complete: bool):
        bot.log(f"{LABEL}: {message}")
        bot.back(delay=1)
        mark_task_done(bot, TASK)
        bot.mark_daily_done(MORE_KEY)

    def on_round(today: int):
        if today == PATROL_REQUIRED:
            bot.mark_daily_done(KEY)

    return patrol_rounds(bot, 0, PATROL_GOAL, finish, name=LABEL, key=KEY, on_round=on_round)


@save_errors(MORE_KEY)
def run_more(ctx, settings):
    """Việc nối tiếp: tới Tường thành (city_map.reach_building: đang thấy thì làm luôn; có route thì đi; chưa có route thì tìm route, lưu DB,
    rồi đi) -> Patrol tiếp (đếm lượt chung với Daily, daily_patrol_round_<n>) tới đủ 10 lượt / hết Refresh -> Back, lưu MORE_KEY.
    Bị ngắt giữa chừng: không lưu, lượt sau làm tiếp từ lượt đã đếm."""
    ctx.log(f"Daily Activities: {MORE_LABEL}")
    to_city(ctx)
    if not reach_building(ctx, MORE_LABEL, WALLS):
        return
    if not open_building(ctx, MORE_LABEL, WALLS, MENU_PATROL, PATROL_TITLE):
        return

    def finish(message: str, _complete: bool):
        ctx.log(f"{MORE_LABEL}: {message}")
        ctx.back(delay=1)
        ctx.mark_daily_done(MORE_KEY)

    patrol_rounds(ctx, 0, PATROL_GOAL, finish, name=MORE_LABEL, key=KEY)


def more_done(ctx, settings) -> bool:
    """Bỏ qua khi: Daily Patrol chưa xong (làm theo dòng Activity trước), hoặc đã đủ 10 lượt / hết Refresh hôm nay."""
    return (not ctx.is_daily_done(KEY) or ctx.is_daily_done(MORE_KEY)
            or rounds_today(ctx, KEY) >= ROUNDS_PER_DAY)


MORE_JOB = {"run": run_more, "enabled": lambda settings: settings.get(LABEL) is True, "done": more_done}

TASK = Task(LABEL, FOLDER, key=KEY)
