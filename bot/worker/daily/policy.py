"""
policy.py — luật chạy của nhóm Daily Activities (phía worker): hàm run của từng loại nhiệm vụ. Mỗi hàm nhận
(ctx, cấu hình tab Daily Activities) + tham số riêng (functools.partial trong tasks.py), gọi hàm làm việc trong
bot/activities/daily_activities/ rồi tự ghi kết quả (xong hôm nay, hẹn thử lại).
"""
from datetime import datetime

from ...activities.daily_activities import alliance_donation, alliance_help
from ...activities.daily_activities.common import collect_activity_rewards, run_task
from ...activities.daily_activities.constants import BUY_HAMMERS, BUY_STAMINA, GENERAL, REWARDS, REWARDS_KEY
from ...activities.daily_activities.offering.constants import KEY as OFFERING_KEY
from ...activities.daily_activities.offering.constants import OFFER_GEMS_DEFAULT, OFFER_GEMS_KEY
from ...activities.daily_activities.run import HOURLY, TASKS as DAILY_TASKS, run_buy_hammers, run_buy_stamina
from ...activities.result import TaskResult
from . import gifts

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


def is_complete(ctx, task, settings: dict) -> bool:
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
    if is_complete(ctx, task, settings):
        return
    ctx.log(f"Daily Activities: {task.label}")
    result = run_task(ctx, task)
    if result.done:
        record_result(ctx, task.key, task.label, result)
    else:
        _retry(ctx, task.key)


def run_buy_stamina_task(ctx, settings: dict):
    if ctx.is_daily_done(BUY_STAMINA):
        return
    quantity = int(settings.get(GENERAL, {}).get("stamina_quantity", 10))
    ctx.log(f"Daily General: Buy Stamina x{quantity}")
    if run_buy_stamina(ctx, quantity).done:
        ctx.mark_daily_done(BUY_STAMINA)


def run_buy_hammers_task(ctx, settings: dict):
    if ctx.is_daily_done(BUY_HAMMERS):
        return
    ctx.log("Daily General: Buy All Hammers")
    if run_buy_hammers(ctx).done:
        ctx.mark_daily_done(BUY_HAMMERS)


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
