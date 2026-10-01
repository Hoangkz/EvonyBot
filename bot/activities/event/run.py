"""
run.py — "Event" activity.

Chạy lần lượt các nhiệm vụ trong TASKS (từ nhiệm vụ đầu tới hết), chỉ những nhiệm vụ
được bật ở tab Event. Mỗi nhiệm vụ là một file riêng (gather_troops/..., kings_path/...)
với hàm `run(bot, task, state)`; phần đi từ màn hình chính tới nút event dùng chung ở
common.py. `state` giữ qua các nhiệm vụ để quà đăng nhập chỉ nhận 1 lần mỗi lượt.
"""
from .common import EventState
from .gather_troops import cultivate_generals, ground_troop, mounted_troop

# (key trong settings / event.json, hàm chạy nhiệm vụ) theo thứ tự chạy.
TASKS = [
    (cultivate_generals.KEY, cultivate_generals.run),
    (ground_troop.KEY, ground_troop.run),
    (mounted_troop.KEY, mounted_troop.run),
]


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Event" tab's config:
    {key: {"enabled", "day"}} (ô tích) / {key: {"value", "level"?, "day"}} (ô chọn)."""
    state = EventState()
    for key, run_task in TASKS:
        task = settings.get(key)
        if not _enabled(task):
            continue
        bot.check()
        bot.log(f"Event: task {key}")
        run_task(bot, task, state)


def _enabled(task) -> bool:
    """Ô tích: đã tích. Ô chọn: giá trị khác 0."""
    if not isinstance(task, dict):
        return False
    if "enabled" in task:
        return bool(task["enabled"])
    return str(task.get("value", 0)) not in ("", "0")
