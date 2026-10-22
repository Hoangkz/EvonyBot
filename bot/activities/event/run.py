"""
run.py — nhiệm vụ của "Event" (Gather Troops, King's Path): chỉ làm thao tác trong game, trả TaskResult.

Không có hàm run của cả activity và không có phần phân phối: nhiệm vụ nào được chọn (ô tích), bỏ qua nhiệm vụ đã xong /
đã đạt mục tiêu / Day khoá, ghi kết quả, khi nào nhận thưởng event là nhiệm vụ tự lưu vào DB, worker (bot/worker/tasks.py) chỉ kiểm tra đã xong chưa. EVENTS liệt kê
nhiệm vụ của từng event theo thứ tự; perform_task chạy một nhiệm vụ, claim_event nhận thưởng của một event (claim.py).

Mỗi nhiệm vụ là một file riêng (gather_troops/..., kings_path/...) với hàm `run(bot, task, state)`; phần đi từ màn
hình chính tới nút event dùng chung ở common.py. `state` (EventState) giữ quà đăng nhập chỉ nhận 1 lần mỗi lượt.
"""
from . import claim, cycle
from ...common import to_city
from ..result import NOT_DONE, TaskResult, clear, save_errors, take_all
from .common import EventState
from .constants import GATHER_TROOPS_ICON, KINGS_PATH_ICON
from .gather_troops import cultivate_generals, ground_troop, mounted_troop, ranged_troop, siege_machine, trap_factory
from .kings_path import black_market, city_tax, donate, heal, patrol, refine, train_troop, wheel

# (key event, tên log, icon trong danh sách event, [(key nhiệm vụ trong settings / event.py,
# hàm chạy nhiệm vụ)] theo thứ tự chạy).
EVENTS = [
    ("gather_troops", "Gather Troops", GATHER_TROOPS_ICON, [
        (cultivate_generals.KEY, cultivate_generals.run),
        (ground_troop.KEY, ground_troop.run),
        (mounted_troop.KEY, mounted_troop.run),
        (ranged_troop.KEY, ranged_troop.run),
        (siege_machine.KEY, siege_machine.run),
        (trap_factory.KEY, trap_factory.run),
    ]),
    ("kings_path", "King's Path", KINGS_PATH_ICON, [
        (city_tax.KEY, city_tax.run),
        (patrol.KEY, patrol.run),
        (donate.KEY, donate.run),
        (train_troop.KEY, train_troop.run),
        (heal.KEY, heal.run),
        (wheel.KEY, wheel.run),
        (refine.KEY, refine.run),
        (black_market.KEY, black_market.run),
    ]),
]
# Mọi nhiệm vụ theo thứ tự chạy.
TASKS = [task for *_, tasks in EVENTS for task in tasks]


def perform_task(bot, key: str, run_task, config) -> TaskResult:
    """Chạy một nhiệm vụ Event `key`: `run_task(bot, cấu hình riêng của nhiệm vụ, EventState)`. done=True khi nhiệm vụ
    báo xong; mọi kết quả báo giữa chừng (xong / hết Go / đạt mục tiêu / Day khoá) nằm trong `outcomes` để worker ghi."""
    clear(bot)
    bot.check()
    state = EventState()
    run_task(bot, config, state)
    for event in state.absent:   # event không còn trong game: mọi nhiệm vụ của event đó bỏ qua tới lần reset server
        bot.mark_daily_done(absent_key(event))
        bot.record(f"Event: không thấy {event} trong game, đã lưu DB ({absent_key(event)}), bỏ qua tới lần reset server")
    outcomes = tuple(take_all(bot))
    done = any(o.done and o.key == key for o in outcomes)
    return TaskResult(done=done, outcomes=outcomes) if outcomes else NOT_DONE


def claim_event(bot, event: str, name: str, icon: str):
    """Nhận thưởng của `event` (chấm đỏ + rương mốc), vào bảng event nếu chưa ở đó."""
    bot.check()
    claim.run(bot, EventState(), name, icon, claim.CHESTS.get(event, ()), claim.TITLES.get(event))


# =============================================================================================
# Luật của các nhiệm vụ Event (bảng bot/worker/priority.py: "run": event_job(...) / claim_job(...)). Cấu hình ở đây là của tab
# Event. Trạng thái lưu trong daily_done cho nhiệm vụ `key`:
# - `key`                      xong hôm nay (hết lượt / hết tài nguyên cũng tính), hết hạn ở lần reset server;
# - `key_complete`             hết nút Go: xong hẳn, mọi mục tiêu;
# - `key_complete_<N>` + `key_reached_<N>`  đạt mục tiêu N người dùng chọn mà vẫn còn Go (tăng mục tiêu thì chạy lại);
# - `key_locked`               Day / cấp lính còn khoá: bỏ qua tới lần reset server;
# - `<event>_absent`           event không còn trong game: mọi nhiệm vụ của event bỏ qua tới lần reset server.
# "Xong" luôn tính lại từ các dấu đó (đọc DB) mỗi vòng lặp.
# =============================================================================================
_KEY_OF = {run: key for _, _, _, tasks in EVENTS for key, run in tasks}   # hàm làm việc -> key nhiệm vụ
_EVENT_OF = {key: event for event, _, _, tasks in EVENTS for key, _ in tasks}   # key nhiệm vụ -> key event
_EVENT_INFO = {event: (name, icon, [key for key, _ in tasks]) for event, name, icon, tasks in EVENTS}


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


def absent_key(event: str) -> str:
    """Key daily_done: event `event` không còn trong game (hết ruy băng / không thấy icon), bỏ qua tới lần reset server."""
    return f"{event}_absent"


def claim_key(event: str, done_count: int) -> str:
    """Key daily_done: đã nhận thưởng của `event` khi có `done_count` nhiệm vụ xong."""
    return f"{event}_claimed_{done_count}"


# ---- Nhiệm vụ đã xong? (đọc DB) ------------------------------------------------------------
def _fresh(ctx, key: str, done_key: str) -> bool:
    """Dấu hoàn thành `done_key` còn hiệu lực trong chu kỳ hiện tại của event chứa nhiệm vụ `key` (xem cycle.py): quá ngày
    reset của event thì dấu cũ hết hiệu lực, nhiệm vụ được làm lại."""
    return cycle.valid(ctx, _EVENT_OF[key], ctx.done_at(done_key))


def is_complete(ctx, settings: dict, key: str) -> bool:
    """Xong cả vòng event: hết Go (xong hẳn), hoặc đã đạt mục tiêu HIỆN TẠI của nhiệm vụ."""
    target = task_target(settings, key)
    return _fresh(ctx, key, complete_key(key)) or (target is not None and _fresh(ctx, key, complete_key(key, target)))


def is_done_today(ctx, settings: dict, key: str) -> bool:
    """Nhiệm vụ đã xong hôm nay (daily_done `key`), TRỪ khi hôm nay xong là vì đạt một mục tiêu nhỏ hơn mục tiêu hiện
    tại (người dùng vừa tăng lên) -> chưa xong, chạy lại. Xong vì hết lượt / hết tài nguyên trong ngày (không có
    "<key>_reached_*" hôm nay) vẫn tính là xong."""
    if not ctx.is_daily_done(key):
        return False
    target = task_target(settings, key)
    if target is None or _fresh(ctx, key, complete_key(key)):
        return True
    prefix = f"{key}_reached_"
    reached = [int(k[len(prefix):]) for k in ctx.daily_keys()
               if k.startswith(prefix) and k[len(prefix):].isdigit() and ctx.is_daily_done(k)]
    return not reached or max(reached) >= target


def skip_reason(ctx, settings: dict, key: str) -> str | None:
    """Lý do nhiệm vụ `key` không cần chạy nữa (hôm nay), hoặc None nếu còn phải chạy."""
    if is_complete(ctx, settings, key):
        return "target reached earlier"
    if is_done_today(ctx, settings, key):
        return "already done"
    if ctx.is_daily_done(locked_key(key)):
        return "day still locked, skipped until server reset"
    if ctx.is_daily_done(absent_key(_EVENT_OF[key])):
        return "event not in game, skipped until server reset"
    return None


# ---- Lưu kết quả ---------------------------------------------------------------------------
def record_outcome(ctx, settings: dict, outcome: TaskResult):
    """Lưu một kết quả nhiệm vụ (hoặc nhiệm vụ con) vào daily_done."""
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


# ---- Dict luật của việc ({run, enabled, done}) cho bảng priority.py -----------------------------------------------------------------------------------
def event_job(event: str, run_task) -> dict:
    """Nhiệm vụ Event: `run_task(ctx, cấu hình riêng, EventState)` là hàm làm việc của nhiệm vụ (khai trong EVENTS)."""
    key = _KEY_OF[run_task]

    @save_errors(key)   # lỗi thì lưu `<key>_error` vào DB
    def run(ctx, settings):
        to_city(ctx)   # đang ở bản đồ thế giới thì về thành chính trước
        result = perform_task(ctx, key, run_task, settings.get(key))   # kết quả báo giữa chừng (xong / hết Go / đạt mục tiêu / khoá)
        # Lưu từng kết quả vào DB ngay tại đây (record_outcome); worker không ghi gì.
        for outcome in result.outcomes:
            record_outcome(ctx, settings, outcome)
        if result.done:
            ctx.record(f"Event: xong {key}")

    return {"run": run, "enabled": lambda settings: group_active(settings, event) and task_enabled(settings, key),
            "done": lambda ctx, settings: skip_reason(ctx, settings, key) is not None}


def claim_job(event: str) -> dict:
    """Nhận thưởng của `event` (chấm đỏ + rương mốc) khi có nhiệm vụ xong hôm nay mà chưa nhận ứng với số nhiệm vụ xong
    hiện tại (bị ngắt giữa chừng thì lượt sau nhận lại)."""
    name, icon, keys = _EVENT_INFO[event]

    def done_count(ctx):
        count = sum(1 for key in keys if ctx.is_daily_done(key))
        return count, claim_key(event, count)

    @save_errors(f"{event}_claim")   # lỗi thì lưu `<event>_claim_error` vào DB
    def run(ctx, settings):
        ctx.check()
        count, key = done_count(ctx)
        if count == 0 or ctx.is_daily_done(key):
            return
        ctx.record(f"{name}: {count} task(s) done, claiming rewards")
        claim_event(ctx, event, name, icon)
        ctx.mark_daily_done(key)

    def done(ctx, settings):
        """Đã nhận thưởng ứng với số nhiệm vụ xong hiện tại; chưa nhiệm vụ nào xong thì chỉ coi là xong khi mọi nhiệm vụ đã
        tích của event này không còn phải chạy (VD Day khoá), để không chờ vô ích."""
        if ctx.is_daily_done(absent_key(event)):
            return True   # event không còn trong game: không có gì để nhận
        count, key = done_count(ctx)
        if count:
            return ctx.is_daily_done(key)
        return all(skip_reason(ctx, settings, k) is not None for k in keys if task_enabled(settings, k))

    return {"run": run, "done": done,
            "enabled": lambda settings: group_active(settings, event) and any(task_enabled(settings, k) for k in keys)}
