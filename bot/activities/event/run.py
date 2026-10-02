"""
run.py — "Event" activity.

Chạy lần lượt từng event trong EVENTS (Gather Troops rồi King's Path). Mỗi event: làm lần lượt
các nhiệm vụ được bật ở tab Event, xong hết thì nhận thưởng của event đó theo chấm đỏ
(claim.py — chỉ khi event có nhiệm vụ đã xong hôm nay, mỗi khi số nhiệm vụ xong tăng lên),
rồi mới sang event kế tiếp.

Mỗi nhiệm vụ là một file riêng (gather_troops/..., kings_path/...) với hàm
`run(bot, task, state)`; phần đi từ màn hình chính tới nút event dùng chung ở common.py.
`state` giữ qua các nhiệm vụ để quà đăng nhập chỉ nhận 1 lần mỗi lượt.
"""
from . import claim
from .common import EventState
from .constants import GATHER_TROOPS_ICON, KINGS_PATH_ICON
from .gather_troops import cultivate_generals, ground_troop, mounted_troop, ranged_troop, siege_machine, defense_force
from .kings_path import city_tax, donate, heal, patrol, train_troop, wheel

# (key event, tên log, icon trong danh sách event, [(key nhiệm vụ trong settings / event.json,
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
    ]),
]
# Mọi nhiệm vụ theo thứ tự chạy.
TASKS = [task for *_, tasks in EVENTS for task in tasks]


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Event" tab's config:
    {key: {"enabled", "day"}} (ô tích) / {key: {"value", "level"?, "day"}} (ô chọn)."""
    state = EventState()
    for event, name, icon, tasks in EVENTS:
        for key, run_task in tasks:
            task = settings.get(key)
            if not _enabled(task):
                continue
            bot.check()
            bot.log(f"Event: task {key}")
            run_task(bot, task, state)
        bot.check()
        claim.maybe_claim(bot, state, event, name, icon, [key for key, _ in tasks])


def _enabled(task) -> bool:
    """Ô tích: đã tích. Ô chọn: giá trị khác 0."""
    if not isinstance(task, dict):
        return False
    if "enabled" in task:
        return bool(task["enabled"])
    return str(task.get("value", 0)) not in ("", "0")
