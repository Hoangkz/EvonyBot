"""
run.py — "Event" activity.

Chạy lần lượt từng event trong EVENTS (Gather Troops rồi King's Path), cuối cùng là event 3 ngày
của Event Center (event_center/three_day). Group nào bỏ tích "active" ở tab Event thì bỏ qua. Mỗi event: làm lần lượt
các nhiệm vụ được bật ở tab Event, xong hết thì nhận thưởng của event đó theo chấm đỏ
(claim.py — chỉ khi event có nhiệm vụ đã xong hôm nay, mỗi khi số nhiệm vụ xong tăng lên),
rồi mới sang event kế tiếp.

Nhiệm vụ nào vừa xong trong lượt này (daily_done chuyển sang có) thì bot.yield_to_boss(): đang
chạy theo lịch ưu tiên boss thì nhường ngay cho worker kiểm tra boss; lượt sau Event chạy lại từ
đầu, nhiệm vụ đã xong tự bỏ qua.

Mỗi nhiệm vụ là một file riêng (gather_troops/..., kings_path/...) với hàm
`run(bot, task, state)`; phần đi từ màn hình chính tới nút event dùng chung ở common.py.
`state` giữ qua các nhiệm vụ để quà đăng nhập chỉ nhận 1 lần mỗi lượt.
"""
from . import claim
from .common import EventState, is_complete
from .constants import GATHER_TROOPS_ICON, KINGS_PATH_ICON
from .gather_troops import cultivate_generals, ground_troop, mounted_troop, ranged_troop, siege_machine, defense_force
from ..event_center import three_day
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
        (defense_force.KEY, defense_force.run),
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


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Event" tab's config:
    {key: {"enabled", "day"}} (ô tích) / {key: {"value", "level"?, "day"}} (ô chọn)."""
    state = EventState()
    for event, name, icon, tasks in EVENTS:
        if not _group_active(settings, event):
            bot.log(f"Event: {name} not active, skipped")
            continue
        for key, run_task in tasks:
            task = settings.get(key)
            if not _enabled(task):
                continue
            if is_complete(bot, key):
                bot.log(f"Event: {key} target reached earlier, skipped")
                continue
            bot.check()
            was_done = bot.is_daily_done(key)
            bot.record(f"Event: bắt đầu {key}")
            run_task(bot, task, state)
            if not was_done and bot.is_daily_done(key):
                bot.record(f"Event: xong {key}")
                bot.yield_to_boss()
        bot.check()
        claim.maybe_claim(bot, state, event, name, icon, [key for key, _ in tasks])
    # Event 3 ngày (Event Center > Limited): tự kiểm group bật và "đã xong hôm nay".
    bot.check()
    three_day.run(bot, settings)


def _group_active(settings: dict, event: str) -> bool:
    """Ô tích ở tiêu đề group (settings "<event>_active"); thiếu = bật."""
    group = settings.get(f"{event}_active")
    return True if group is None else bool(group.get("enabled") if isinstance(group, dict) else group)


def _enabled(task) -> bool:
    """Ô tích: đã tích. Ô chọn: giá trị khác 0."""
    if not isinstance(task, dict):
        return False
    if "enabled" in task:
        return bool(task["enabled"])
    return str(task.get("value", 0)) not in ("", "0")
