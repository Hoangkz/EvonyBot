"""
run.py — Daily Activities (port từ DailyActivities1234.cs): điểm vào `run(bot, settings)`.

Mỗi nhiệm vụ là một thư mục con (giống activity Event): constants.py (ảnh) + run.py (handler, TASK).
Vòng lặp chung của một nhiệm vụ: common.run_task. File này chỉ lo thứ tự chạy:
1. General (Buy Stamina / Buy All Hammers, general.py).
2. Các nhiệm vụ được tích, theo thứ tự TASKS (thứ tự bản C#, cũng là thứ tự ô tích ở tab UI), 5
   lượt; nhiệm vụ đã thấy ảnh xong / dòng hết Go từ lần reset server gần nhất thì bỏ qua.
   Monster Killing: đánh 2 lần, nhận dòng đầu rồi hoãn; quay lại sau 5 nhiệm vụ khác xong (hoặc cuối
   lượt sau 4 nhiệm vụ / khi mọi nhiệm vụ khác đã xong) để đánh 3 lần còn lại.
3. Nhận thưởng Activity (common.collect_activity_rewards); chỉ lưu "đã nhận" khi mọi nhiệm vụ xong.
4. Nhiệm vụ theo giờ (không ưu tiên, cuối cùng; HOURLY): Alliance Donation, Alliance Help — ô chọn giờ ở tab UI
   (0 = không làm). Chưa xong hôm nay và đã qua số giờ đó kể từ lần thử trước -> một lần thử (hourly.try_task).
   Chưa xong -> hẹn worker chạy lại Daily Activities sau phần giờ còn lại ngắn nhất (bot.again_after, ưu tiên
   thấp — bot/worker/scheduler.py).
"""
from datetime import datetime

from . import alliance_donation, alliance_help
from .alliance_donation import TASK as ALLIANCE_DONATION
from .alliance_donation.run import donate_free
from .alliance_help import TASK as ALLIANCE_HELP
from .alliance_help.run import help_all
from .black_market import TASK as BLACK_MARKET
from .common import MONSTER_KILLING, Task, collect_activity_rewards, run_task
from .constants import BUY_HAMMERS, BUY_STAMINA, GENERAL, REWARDS
from .general import buy_all_hammers, buy_stamina
from .general_enhancing import TASK as GENERAL_ENHANCING
from .gold_levy import TASK as GOLD_LEVY
from .material_composing import TASK as MATERIAL_COMPOSING
from .monster_killing import TASK as MONSTER
from .offering import TASK as OFFERING
from .patrol import TASK as PATROL
from .resource_collecting import TASK as RESOURCE_COLLECTING
from .resource_gathering import TASK as RESOURCE_GATHERING
from .resource_tax import TASK as RESOURCE_TAX
from .trap_building import TASK as TRAP_BUILDING
from .troop_healing import TASK as TROOP_HEALING
from .troop_training import TASK as TROOP_TRAINING
from .wheel_of_fortune import TASK as WHEEL_OF_FORTUNE
from .. import gift_claims

# Thứ tự chạy (= thứ tự bản C#; tab UI SUPPORTED_TASKS chỉ khác ở chỗ đưa Offering lên đầu).
# Resource Gathering phải ngay sau Offering: cả hai đưa về thành, bàn tay nổi thu mọi mỏ một lần.
TASKS: tuple[Task, ...] = (
    MONSTER,
    RESOURCE_COLLECTING,
    OFFERING,
    RESOURCE_GATHERING,
    RESOURCE_TAX,
    GOLD_LEVY,
    TROOP_TRAINING,
    TROOP_HEALING,
    TRAP_BUILDING,
    ALLIANCE_DONATION,
    ALLIANCE_HELP,
    BLACK_MARKET,
    GENERAL_ENHANCING,
    WHEEL_OF_FORTUNE,
    PATROL,
    MATERIAL_COMPOSING,
)


def run(bot, settings: dict):
    """Run enabled tasks in the exact order used by the C# implementation."""
    enabled = {name for name, value in settings.items()
               if name != GENERAL and isinstance(value, bool) and value}
    # Nhiệm vụ theo giờ không phải ô tích: chạy ở _run_hourly (cấu hình cũ True vẫn bỏ qua ở đây).
    hourly = {task.label for task, *_ in HOURLY}
    selected = [task for task in TASKS if task.label in enabled and task.label not in hourly]
    unsupported = sorted(enabled - {task.label for task in TASKS})
    if unsupported:
        bot.log("Daily Activities not implemented by DailyActivities1234.cs: "
                + ", ".join(unsupported))

    _run_general(bot, settings.get(GENERAL, {}))

    if not selected:
        bot.log("Daily Activities: no implemented daily task selected")
    elif all(bot.is_daily_done(task.label) for task in selected) and bot.is_daily_done(REWARDS):
        bot.log("Daily Activities: all done today")
    else:
        _run_selected(bot, selected)
    _run_hourly(bot, settings)


def _run_selected(bot, selected):
    """Các nhiệm vụ được tích (5 lượt, Monster Killing hoãn), rồi nhận thưởng Activity."""
    # DailyActivities1234.DailyActivities made five passes. Completed tasks
    # return immediately when their Finish template is found; a task whose
    # Finish template was seen since the last server reset is skipped.
    monster = next((task for task in selected if task.label == MONSTER_KILLING), None)
    completed_after_monster = 0
    for _ in range(5):
        monster_retried_this_pass = False
        for task in selected:
            if bot.is_daily_done(task.label):
                continue
            if (task.label == MONSTER_KILLING
                    and getattr(bot, "_daily_monster_deferred", False)):
                continue
            bot.check()
            bot.log(f"Daily Activities: {task.label}")
            finished = run_task(bot, task)
            if finished:
                bot.mark_daily_done(task.label)
            if (task.label != MONSTER_KILLING and finished
                    and getattr(bot, "_daily_monster_deferred", False)):
                completed_after_monster += 1
                if completed_after_monster >= 5 and monster is not None:
                    bot.check()
                    bot.log("Daily Activities: returning to Monster Killing after 5 tasks")
                    if run_task(bot, monster):
                        bot.mark_daily_done(monster.label)
                    completed_after_monster = 0
                    monster_retried_this_pass = True

        if (monster is not None and not bot.is_daily_done(monster.label)
                and getattr(bot, "_daily_monster_deferred", False)
                and not monster_retried_this_pass
                and (completed_after_monster >= 4
                     or all(t.label == MONSTER_KILLING or bot.is_daily_done(t.label)
                            for t in selected))):
            bot.check()
            bot.log("Daily Activities: returning to Monster Killing after 4 tasks")
            if run_task(bot, monster):
                bot.mark_daily_done(monster.label)
            completed_after_monster = 0
    if not bot.is_daily_done(REWARDS):
        collect_activity_rewards(bot)
        # Chỉ coi là nhận xong khi mọi task đã xong, để lần chạy sau trong ngày còn nhận tiếp.
        if all(bot.is_daily_done(task.label) for task in selected):
            bot.mark_daily_done(REWARDS)
    # Gift flows are intentionally last: never leave Daily Activities to claim an
    # event reward while a selected daily task or Activity Rewards is unfinished.
    if (all(bot.is_daily_done(task.label) for task in selected)
            and bot.is_daily_done(REWARDS)):
        _run_gift_claims(bot)


def _run_gift_claims(bot):
    """Worker-only post phase; flow tests opt in explicitly when needed."""
    if getattr(bot, "post_daily_gifts_enabled", False) is True:
        gift_claims.run(bot)


# (nhiệm vụ, module constants (INTERVAL_KEY / INTERVAL_DEFAULT / TRIED_KEY), hàm một lần thử) — theo thứ tự chạy.
HOURLY = (
    (ALLIANCE_DONATION, alliance_donation.constants, donate_free),
    (ALLIANCE_HELP, alliance_help.constants, help_all),
)


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


def donation_hours(settings: dict) -> int:
    """Số giờ của Alliance Donation (giữ cho chỗ gọi cũ)."""
    return hourly_hours(settings, alliance_donation.constants)


def _run_hourly(bot, settings):
    """Các nhiệm vụ theo giờ (không ưu tiên): tới giờ thì thử một lần; còn nhiệm vụ chưa xong hôm nay thì hẹn
    worker chạy lại Daily Activities sau phần giờ còn lại ngắn nhất (bot.again_after, giây)."""
    again = None
    for task, consts, attempt in HOURLY:
        hours = hourly_hours(settings, consts)
        if hours <= 0 or bot.is_daily_done(task.label):
            continue
        wait = hours * 3600
        tried = _parse_time(bot.done_at(consts.TRIED_KEY))
        left = wait - (datetime.now() - tried).total_seconds() if tried else 0
        if left <= 0:
            bot.check()
            bot.log(f"Daily Activities: {task.label} (every {hours}h)")
            if attempt(bot):
                continue
            left = wait
        bot.log(f"Daily Activities: {task.label} again in {left / 3600:.1f}h")
        again = left if again is None else min(again, left)
    if again is not None:
        bot.again_after = again


def _parse_time(value) -> datetime | None:
    try:
        return datetime.fromisoformat(value) if value else None
    except (TypeError, ValueError):
        return None


def _run_general(bot, settings):
    if not isinstance(settings, dict):
        return
    quantity = int(settings.get("stamina_quantity", 10))
    if settings.get("buy_stamina") and quantity > 0 and not bot.is_daily_done(BUY_STAMINA):
        bot.log(f"Daily General: Buy Stamina x{quantity}")
        if buy_stamina(bot, quantity):
            bot.mark_daily_done(BUY_STAMINA)
    if settings.get("buy_all_hammers") and not bot.is_daily_done(BUY_HAMMERS):
        bot.log("Daily General: Buy All Hammers")
        if buy_all_hammers(bot):
            bot.mark_daily_done(BUY_HAMMERS)
