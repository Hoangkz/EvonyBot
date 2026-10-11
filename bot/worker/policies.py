"""
policies.py — luật chạy của mọi nhiệm vụ (phía worker). Bảng nhiệm vụ nằm ở priority.py: mỗi dòng có `policy` chọn một luật ở
đây; registry.py dựng TaskDef từ bảng đó. Hàm làm việc trong game nằm ở bot/activities/ (chỉ thao tác, trả TaskResult).

Các luật (BUILDERS):
- daily / hourly / buy_general / rewards                   Daily Activities
- event / event_claim                                      Event (Gather Troops, King's Path)
- crazy_eggs / three_day                                   Event Center
- open_gift_box / plain                                    nhóm chỉ có một nhiệm vụ
"""
from datetime import datetime
from functools import partial

from ..activities.alliance_capacity.run import run as alliance_capacity_run
from ..activities.battlefield_shop.run import run as battlefield_shop_run
from ..activities.black_market.run import run as black_market_run
from ..activities.daily_activities import alliance_donation, alliance_help
from ..activities.daily_activities.common import collect_activity_rewards, run_task
from ..activities.daily_activities.constants import GENERAL, HAMMER_DONE, REWARDS, REWARDS_KEY, STAMINA_REACHED
from ..activities.daily_activities.offering.constants import KEY as OFFERING_KEY
from ..activities.daily_activities.offering.constants import OFFER_GEMS_DEFAULT, OFFER_GEMS_KEY
from ..activities.daily_activities.run import HOURLY, TASKS as DAILY_TASKS, buy_general
from ..activities.event.run import EVENTS, claim_event, perform_task
from ..activities.event_center import crazy_eggs, three_day
from ..activities.event_center.crazy_eggs import constants as eggs
from ..activities.event_center.three_day import constants as three
from ..activities.open_gift_box.constants import KEY as OPEN_GIFT_BOX_KEY
from ..activities.open_gift_box.run import run as open_gift_box_run
from ..activities.result import TaskResult
from . import gifts
from .task_def import TaskDef, always

# =============================================================================================
# Daily Activities
# =============================================================================================
RETRY_AFTER = 300     # giây: nhiệm vụ Daily chưa xong thì hẹn thử lại (ưu tiên thấp nhất)
MAX_ATTEMPTS = 5      # số lần thử tối đa mỗi ngày cho một nhiệm vụ chưa xong (như 5 lượt của bản C#)

# key nhiệm vụ theo giờ -> module constants của nó (INTERVAL_KEY / INTERVAL_DEFAULT: ô chọn giờ ở tab UI).
HOURLY_CONSTS = {
    alliance_donation.KEY: alliance_donation.constants,
    alliance_help.KEY: alliance_help.constants,
}


def _offering_target(settings: dict) -> int:
    """Số lần Offer Gems chọn ở tab Daily Activities."""
    try:
        return max(0, int(settings.get(OFFER_GEMS_KEY, OFFER_GEMS_DEFAULT)))
    except (TypeError, ValueError):
        return OFFER_GEMS_DEFAULT


# key nhiệm vụ có mục tiêu theo số lượng chọn ở tab UI -> hàm đọc mục tiêu từ cấu hình tab. Xong với mục tiêu nhỏ hơn
# mục tiêu đang chọn thì chưa xong (xem is_complete).
TARGETS = {OFFERING_KEY: _offering_target}


def daily_complete(ctx, task, settings: dict) -> bool:
    """Nhiệm vụ đã xong hôm nay VỚI mục tiêu đang chọn. Chưa xong hôm nay -> False. Có mục tiêu (TARGETS): đã lưu mục
    tiêu đạt được (`<key>_reached_<N>`) thì phải đạt >= mục tiêu đang chọn (tăng số lượng ở tab UI thì chưa xong);
    mục tiêu 0 = dòng nhiệm vụ không còn Go -> xong dù chọn bao nhiêu; chưa lưu mục tiêu nào (xong theo ảnh Finish) -> xong."""
    if not ctx.is_daily_done(task.label):
        return False
    target = TARGETS.get(task.key)
    times = target(settings) if target else 0
    if times <= 0:
        return True
    prefix = f"{task.key}_reached_"
    reached = [int(k[len(prefix):]) for k in ctx.daily_keys()
               if k.startswith(prefix) and k[len(prefix):].isdigit() and ctx.is_daily_done(k)]
    return not reached or 0 in reached or max(reached) >= times


def hourly_hours(settings: dict, consts) -> int:
    """Số giờ giữa hai lần thử một nhiệm vụ theo giờ (ô chọn ở tab UI, luôn lưu khoá; thiếu khoá -> 0 = không làm,
    mặc định 4h do UI đặt). Cấu hình cũ (ô tích): True -> INTERVAL_DEFAULT, False -> 0."""
    value = settings.get(consts.INTERVAL_KEY, 0)
    if isinstance(value, bool):
        return consts.INTERVAL_DEFAULT if value else 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def selected_labels(settings: dict) -> set[str]:
    """Nhãn các nhiệm vụ Daily (không phải nhiệm vụ theo giờ) đã tích."""
    hourly = {task.label for task, _ in HOURLY}
    return {name for name, value in settings.items()
            if name != GENERAL and name not in hourly and isinstance(value, bool) and value}


def _parse_time(value) -> datetime | None:
    try:
        return datetime.fromisoformat(value) if value else None
    except (TypeError, ValueError):
        return None


def record_result(ctx, key: str, label: str, result: TaskResult):
    """Ghi kết quả nhiệm vụ: xong thì lưu "xong hôm nay" (nhãn) và mục tiêu đã đạt (`<key>_reached_<mục tiêu>`)."""
    if not result.done:
        return
    ctx.mark_daily_done(label)
    if result.reached is not None:
        ctx.mark_daily_done(f"{key}_reached_{result.reached}")


def _retry(ctx, key: str):
    """Chưa xong: hẹn thử lại sau RETRY_AFTER giây, tối đa MAX_ATTEMPTS lần mỗi ngày."""
    attempts = ctx.__dict__.setdefault("daily_attempts", {})
    day = datetime.now().date()
    count = attempts.get((key, day), 0) + 1
    attempts[(key, day)] = count
    if count < MAX_ATTEMPTS:
        ctx.again_after = RETRY_AFTER
    else:
        ctx.log(f"Daily Activities: {key} not finished after {count} tries, give up for now")


def run_daily_task(ctx, settings: dict, *, task):
    """Một nhiệm vụ Daily: đã xong hôm nay thì bỏ qua; không thì làm, chưa xong thì hẹn thử lại."""
    if daily_complete(ctx, task, settings):
        return
    ctx.log(f"Daily Activities: {task.label}")
    result = run_task(ctx, task)
    if result.done:
        record_result(ctx, task.key, task.label, result)
    else:
        _retry(ctx, task.key)


def stamina_reached(ctx) -> int:
    """Số Stamina đã mua tới hôm nay (lớn nhất trong các dấu `General: Stamina reached <N>`), 0 nếu chưa mua."""
    prefix = f"{STAMINA_REACHED} "
    return max((int(k[len(prefix):]) for k in ctx.daily_keys()
                if k.startswith(prefix) and k[len(prefix):].isdigit() and ctx.is_daily_done(k)), default=0)


def run_buy_general_task(ctx, settings: dict):
    """General: mua Stamina và Hammer (món nào đã tích) trong MỘT nhiệm vụ, chỉ phần chưa mua hôm nay. Mỗi món xong thì lưu
    dấu riêng: Stamina `General: Stamina reached <mốc>` (nâng mốc thì chỉ mua phần còn lại), Hammer `General: Hammer`."""
    general = _general(settings)
    quantity = _stamina_quantity(general)
    need_stamina = quantity > stamina_reached(ctx)
    need_hammers = bool(general.get("buy_all_hammers")) and not ctx.is_daily_done(HAMMER_DONE)
    if not need_stamina and not need_hammers:
        return
    ctx.log(f"Daily General: Buy Stamina to {quantity if need_stamina else 0}, Hammers {need_hammers}")
    result = buy_general(ctx, quantity if need_stamina else 0, need_hammers)
    for outcome in result.outcomes:
        if outcome.done:
            ctx.mark_daily_done(outcome.key)


def run_rewards(ctx, settings: dict):
    """Nhận thưởng Activity; chỉ lưu "đã nhận" khi mọi nhiệm vụ đã tích đều xong, rồi nhận quà cuối (gift claims)."""
    labels = selected_labels(settings)
    selected = [task for task in DAILY_TASKS if task.label in labels]
    if not ctx.is_daily_done(REWARDS):
        collect_activity_rewards(ctx)
        if all(ctx.is_daily_done(task.label) for task in selected):
            ctx.mark_daily_done(REWARDS)
    if all(ctx.is_daily_done(task.label) for task in selected) and ctx.is_daily_done(REWARDS):
        gifts.run_gift_claims(ctx)
    else:
        _retry(ctx, REWARDS_KEY)


def run_hourly_task(ctx, settings: dict, *, key: str):
    """Nhiệm vụ theo giờ (Alliance Donation / Help): tới giờ thì thử một lần; chưa xong hoặc chưa tới giờ thì hẹn
    lại (ctx.again_after) sau phần giờ còn lại."""
    task, attempt = next((task, attempt) for task, attempt in HOURLY if task.key == key)
    hours = hourly_hours(settings, HOURLY_CONSTS[key])
    if hours <= 0 or ctx.is_daily_done(task.label):
        return
    tried_key = HOURLY_CONSTS[key].TRIED_KEY
    wait = hours * 3600
    tried = _parse_time(ctx.done_at(tried_key))
    left = wait - (datetime.now() - tried).total_seconds() if tried else 0
    if left <= 0:
        ctx.log(f"Daily Activities: {task.label} (every {hours}h)")
        ctx.mark_daily_done(tried_key)   # lưu giờ thử trước khi làm: bị ngắt giữa chừng vẫn tính là đã thử
        result = attempt(ctx)
        if result.done:
            record_result(ctx, key, task.label, result)
            return
        left = wait
    ctx.log(f"Daily Activities: {task.label} again in {left / 3600:.1f}h")
    ctx.again_after = left

# =============================================================================================
# Event (Gather Troops, King's Path)
# =============================================================================================
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
def run_event_task(ctx, settings: dict, *, key: str, run):
    """Nhiệm vụ Event `key`: xong / đạt mục tiêu / Day khoá từ trước thì bỏ qua, không thì chạy
    `run(ctx, cấu hình riêng, EventState)` rồi ghi kết quả."""
    reason = skip_reason(ctx, settings, key)
    if reason:
        ctx.log(f"Event: {key} {reason}, skipped")
        return
    result = perform_task(ctx, key, run, settings.get(key))
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

# =============================================================================================
# Event Center (Crazy Eggs, event 3 ngày)
# =============================================================================================
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


# =============================================================================================
# Nhóm chỉ có một nhiệm vụ
# =============================================================================================
def run_open_gift_box(ctx, settings: dict):
    """Mở mọi hộp quà đã chọn; mở hết (run trả done=True) thì lưu "xong hôm nay"."""
    if open_gift_box_run(ctx, settings).done:
        ctx.mark_daily_done(OPEN_GIFT_BOX_KEY)


# =============================================================================================
# Dựng TaskDef từ bảng nhiệm vụ (priority.py)
# =============================================================================================
# Dòng của bảng: key, priority, [must_finish], policy (tên luật ở BUILDERS), [group: nhóm chọn nhiệm vụ nếu khác nhóm
# chứa dòng], [once / repeat], và tham số riêng của luật (event: tên event; plain: tên hàm ở PLAIN).
_DAILY_BY_KEY = {task.key: task for task in DAILY_TASKS}
_EVENT_BY_KEY = {key: run for _, _, _, tasks in EVENTS for key, run in tasks}
_EVENT_INFO = {event: (name, icon) for event, name, icon, _ in EVENTS}
PLAIN = {
    "alliance_capacity": alliance_capacity_run,
    "black_market": black_market_run,
    "battlefield_shop": battlefield_shop_run,
}


def _stamina_quantity(general: dict) -> int:
    """Số lần mua Stamina chọn ở mục General (0 = không mua)."""
    try:
        return max(0, int(general.get("stamina_quantity", 10))) if general.get("buy_stamina") else 0
    except (TypeError, ValueError):
        return 0


def _buy_general_enabled(settings: dict) -> bool:
    general = _general(settings)
    return _stamina_quantity(general) > 0 or bool(general.get("buy_all_hammers"))


def _task(entry: dict, group: str, enabled, run) -> TaskDef:
    return TaskDef(entry["key"], entry.get("group", group), enabled, run,
                   once=bool(entry.get("once")), repeat=bool(entry.get("repeat")))


def _build_daily(entry, group, events):
    task = _DAILY_BY_KEY[entry["key"]]
    return _task(entry, group, lambda s, label=task.label: label in selected_labels(s),
                 partial(run_daily_task, task=task))


def _build_hourly(entry, group, events):
    key = entry["key"]
    consts = HOURLY_CONSTS[key]
    return _task(entry, group, lambda s: hourly_hours(s, consts) > 0, partial(run_hourly_task, key=key))


def _build_event(entry, group, events):
    key, event = entry["key"], entry["event"]
    return _task(entry, group, lambda s: group_active(s, event) and task_enabled(s, key),
                 partial(run_event_task, key=key, run=_EVENT_BY_KEY[key]))


def _build_event_claim(entry, group, events):
    event = entry["event"]
    name, icon = _EVENT_INFO[event]
    keys = events[event]   # nhiệm vụ của event này trong bảng
    return _task(entry, group, lambda s: group_active(s, event) and any(task_enabled(s, k) for k in keys),
                 partial(run_claim, event=event, name=name, icon=icon, keys=keys))


BUILDERS = {
    "daily": _build_daily,
    "hourly": _build_hourly,
    "buy_general": lambda e, g, ev: _task(e, g, _buy_general_enabled, run_buy_general_task),
    "rewards": lambda e, g, ev: _task(e, g, lambda s: bool(selected_labels(s)), run_rewards),
    "event": _build_event,
    "event_claim": _build_event_claim,
    "crazy_eggs": lambda e, g, ev: _task(e, g, lambda s: crazy_eggs_hours(_general(s)) > 0, run_crazy_eggs),
    "three_day": lambda e, g, ev: _task(e, g, _three_day_active, run_three_day),
    "open_gift_box": lambda e, g, ev: _task(e, g, always, run_open_gift_box),
    "plain": lambda e, g, ev: _task(e, g, always, PLAIN[e["run"]]),
}


def build_registry(data: dict) -> list[TaskDef]:
    """TaskDef của mọi dòng có `policy` trong bảng `data` (priority.DATA), theo thứ tự trong bảng. Dòng không có
    `policy` (Bubble, Join Monster War, gift_*) không phải nhiệm vụ của bộ chọn."""
    groups = [(group, entries) for group, entries in data.items()
              if not group.startswith("_") and isinstance(entries, list)]
    events: dict[str, list[str]] = {}
    for _, entries in groups:
        for entry in entries:
            if entry.get("policy") == "event":
                events.setdefault(entry["event"], []).append(entry["key"])
    return [BUILDERS[entry["policy"]](entry, group, events)
            for group, entries in groups for entry in entries if entry.get("policy")]
