"""
tasks.py — khai báo nhiệm vụ Event Center cho worker (TaskDef, xem bot/worker/task_def.py); registry.py gom lại.
Chọn nhiệm vụ, bỏ qua nhiệm vụ đã xong, ghi kết quả, hẹn chạy lại đều ở đây; bot/activities/event_center/ chỉ làm thao tác
trong game rồi trả TaskResult.

- crazy_eggs: ô chọn giờ nằm ở mục General của tab Daily Activities (nên group là "Daily Activities"): đập trứng, rồi
  hẹn đập lại sau số giờ đã chọn cho tới khi đủ 4 quả vỡ.
- three_day_event: event 3 ngày; cấu hình nằm ở tab Event (group "Event").
"""
from ...activities.event_center import crazy_eggs, three_day
from ...activities.event_center.crazy_eggs import constants as eggs
from ...activities.event_center.three_day import constants as three
from ..task_def import TaskDef
from ..event.policy import record_outcome

DAILY = "Daily Activities"
EVENT = "Event"
GENERAL = "General"          # mục General của tab Daily Activities
CRAZY_EGGS_KEY = "crazy_eggs"
THREE_DAY_KEY = "three_day_event"


def crazy_eggs_hours(general) -> int:
    """Số giờ giữa hai lần đập trứng (ô chọn ở mục General của tab UI; thiếu khoá / sai kiểu -> 0 = không làm)."""
    if not isinstance(general, dict):
        return 0
    try:
        return max(0, int(general.get(eggs.INTERVAL_KEY, 0)))
    except (TypeError, ValueError):
        return 0


def _general(settings: dict) -> dict:
    general = settings.get(GENERAL, {})
    return general if isinstance(general, dict) else {}


def run_crazy_eggs(ctx, settings: dict):
    """Crazy Eggs: đập một lần, rồi hẹn đập lại sau số giờ đã chọn (ctx.again_after) cho tới khi đủ 4 quả vỡ
    (crazy_eggs.run trả done=True)."""
    hours = crazy_eggs_hours(_general(settings))
    if hours <= 0 or ctx.is_daily_done(eggs.DONE_KEY):
        return
    ctx.log(f"Daily General: Crazy Eggs (every {hours}h)")
    result = crazy_eggs.run(ctx, {})
    ctx.mark_daily_done(eggs.TRIED_KEY)   # sau khi chạy xong: bị ngắt giữa chừng thì lượt sau đập tiếp
    if result.done:
        ctx.mark_daily_done(eggs.DONE_KEY)
    else:
        ctx.log(f"Daily General: Crazy Eggs again in {hours}h")
        ctx.again_after = hours * 3600


def _three_day_active(settings: dict) -> bool:
    """Tab Event có group 3-Day Event và group đó đang bật (thiếu ô bật = bật)."""
    if not any(key.startswith(three.GROUP_KEY) for key in settings):
        return False
    group = settings.get(f"{three.GROUP_KEY}_active")
    return True if group is None else bool(group.get("enabled") if isinstance(group, dict) else group)


def run_three_day(ctx, settings: dict):
    """Event 3 ngày của Event Center: hôm nay xong rồi thì bỏ qua; không thì làm, xong thì lưu DONE_KEY."""
    ctx.check()
    if ctx.is_daily_done(three.DONE_KEY):
        ctx.log("3-Day Event: done today, skip")
        return
    result = three_day.run(ctx, settings)
    for outcome in result.outcomes:
        record_outcome(ctx, settings, outcome)
    if result.done:
        ctx.mark_daily_done(three.DONE_KEY)


TASKS = [
    TaskDef(CRAZY_EGGS_KEY, DAILY, lambda s: crazy_eggs_hours(_general(s)) > 0, run_crazy_eggs, repeat=True),
    TaskDef(THREE_DAY_KEY, EVENT, _three_day_active, run_three_day),
]
