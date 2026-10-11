"""
policy.py — luật chạy của nhóm Event (phía worker): đọc cấu hình tab Event, bỏ qua nhiệm vụ đã xong, ghi kết quả
nhiệm vụ vào daily_done, nhận thưởng event. Hàm làm việc trong game: bot/activities/event/.

Trạng thái lưu trong daily_done cho nhiệm vụ `key`:
- `key`                      xong hôm nay (hết lượt / hết tài nguyên cũng tính), hết hạn ở lần reset server;
- `key_complete`             hết nút Go: xong hẳn, mọi mục tiêu;
- `key_complete_<N>` + `key_reached_<N>`  đạt mục tiêu N người dùng chọn mà vẫn còn Go (tăng mục tiêu thì chạy lại);
- `key_locked`               Day / cấp lính còn khoá: bỏ qua tới lần reset server.
"""
from ...activities.event.common import EventState
from ...activities.event.run import claim_event, perform_task
from ...activities.result import TaskResult


# ---- Đọc cấu hình tab Event ----------------------------------------------------------------
def group_active(settings: dict, event: str) -> bool:
    """Ô tích ở tiêu đề group (settings "<event>_active"); thiếu = bật."""
    group = settings.get(f"{event}_active")
    return True if group is None else bool(group.get("enabled") if isinstance(group, dict) else group)


def task_enabled(settings: dict, key: str) -> bool:
    """Ô tích: đã tích. Ô chọn: giá trị khác 0."""
    task = settings.get(key)
    if not isinstance(task, dict):
        return False
    if "enabled" in task:
        return bool(task["enabled"])
    return str(task.get("value", 0)) not in ("", "0")


def task_target(settings: dict, key: str) -> int | None:
    """Mục tiêu người dùng chọn cho nhiệm vụ `key` (tab Event, "value"), hoặc None (ô tích)."""
    task = settings.get(key)
    value = task.get("value") if isinstance(task, dict) else None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ---- Key daily_done ------------------------------------------------------------------------
def complete_key(key: str, target: int | None = None) -> str:
    return f"{key}_complete" if target is None else f"{key}_complete_{target}"


def reached_key(key: str, target: int) -> str:
    return f"{key}_reached_{target}"


def locked_key(key: str) -> str:
    return f"{key}_locked"


def claim_key(event: str, done_count: int) -> str:
    """Key daily_done: đã nhận thưởng của `event` khi có `done_count` nhiệm vụ xong."""
    return f"{event}_claimed_{done_count}"


# ---- Nhiệm vụ đã xong? ---------------------------------------------------------------------
def is_complete(ctx, settings: dict, key: str) -> bool:
    """Xong cả vòng event: hết Go (xong hẳn), hoặc đã đạt mục tiêu HIỆN TẠI của nhiệm vụ."""
    target = task_target(settings, key)
    return bool(ctx.done_at(complete_key(key))
                or (target is not None and ctx.done_at(complete_key(key, target))))


def is_done_today(ctx, settings: dict, key: str) -> bool:
    """Nhiệm vụ đã xong hôm nay (daily_done `key`), TRỪ khi hôm nay xong là vì đạt một mục tiêu nhỏ hơn mục tiêu hiện
    tại (người dùng vừa tăng lên) -> chưa xong, chạy lại. Xong vì hết lượt / hết tài nguyên trong ngày (không có
    "<key>_reached_*" hôm nay) vẫn tính là xong."""
    if not ctx.is_daily_done(key):
        return False
    target = task_target(settings, key)
    if target is None or ctx.done_at(complete_key(key)):
        return True
    prefix = f"{key}_reached_"
    reached = [int(k[len(prefix):]) for k in ctx.daily_keys()
               if k.startswith(prefix) and k[len(prefix):].isdigit() and ctx.is_daily_done(k)]
    return not reached or max(reached) >= target


def skip_reason(ctx, settings: dict, key: str) -> str | None:
    """Lý do bỏ qua nhiệm vụ `key` lần này, hoặc None nếu phải chạy."""
    if is_complete(ctx, settings, key):
        return "target reached earlier"
    if is_done_today(ctx, settings, key):
        return "already done"
    if ctx.is_daily_done(locked_key(key)):
        return "day still locked, skipped until server reset"
    return None


# ---- Ghi kết quả ---------------------------------------------------------------------------
def record_outcome(ctx, settings: dict, outcome: TaskResult):
    """Ghi một kết quả nhiệm vụ (hoặc nhiệm vụ con) vào daily_done."""
    key = outcome.key
    if key is None:
        return
    if outcome.locked:
        ctx.mark_daily_done(locked_key(key))
        return
    if not outcome.done:
        return
    ctx.mark_daily_done(key)
    if outcome.complete:
        ctx.mark_daily_done(complete_key(key))
    elif outcome.target_reached:
        target = task_target(settings, key)
        if target is None:
            ctx.mark_daily_done(complete_key(key))
        else:
            ctx.mark_daily_done(complete_key(key, target))
            ctx.mark_daily_done(reached_key(key, target))


# ---- Hàm run của từng loại nhiệm vụ --------------------------------------------------------
def run_event_task(ctx, settings: dict, *, key: str, run_task):
    """Nhiệm vụ Event `key`: xong / đạt mục tiêu / Day khoá từ trước thì bỏ qua, không thì chạy
    `run_task(ctx, cấu hình riêng, EventState)` rồi ghi kết quả."""
    reason = skip_reason(ctx, settings, key)
    if reason:
        ctx.log(f"Event: {key} {reason}, skipped")
        return
    result = perform_task(ctx, key, run_task, settings.get(key))
    for outcome in result.outcomes:
        record_outcome(ctx, settings, outcome)
    if result.done:
        ctx.record(f"Event: xong {key}")


def maybe_claim(ctx, event: str, name: str, icon: str, keys: list[str]):
    """Nhận thưởng `event` nếu có nhiệm vụ trong `keys` xong hôm nay mà chưa nhận ứng với số nhiệm vụ xong hiện tại
    (bị ngắt giữa chừng thì lượt sau nhận lại)."""
    done_count = sum(1 for key in keys if ctx.is_daily_done(key))
    if done_count == 0:
        return
    key = claim_key(event, done_count)
    if ctx.is_daily_done(key):
        return
    ctx.record(f"{name}: {done_count} task(s) done, claiming rewards")
    claim_event(ctx, event, name, icon)
    ctx.mark_daily_done(key)


def run_claim(ctx, settings: dict, *, event: str, name: str, icon: str, keys: list[str]):
    """Nhận thưởng của `event` (chấm đỏ + rương mốc) nếu có nhiệm vụ trong `keys` xong hôm nay."""
    ctx.check()
    maybe_claim(ctx, event, name, icon, keys)
