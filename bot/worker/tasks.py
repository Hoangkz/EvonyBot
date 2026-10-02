"""
tasks.py — nhiệm vụ của bộ chọn (scheduler.py) và độ ưu tiên đọc từ priority.json.

Bước 1 (bot/worker/TODO.md): mỗi activity đã chọn (trừ Join Boss) được bọc thành 1 nhiệm vụ chạy nguyên
khối; độ ưu tiên của nhiệm vụ đó = cao nhất trong các nhiệm vụ của nhóm (activity) trong priority.json.
Các bước sau tách activity thành từng nhiệm vụ con. Bubble và Join Boss có luật riêng trong BotWorker.
"""
import json
from dataclasses import dataclass

from ..context import TEMPLATE_DIR

# priority.json nằm cạnh file này; đọc theo thư mục gốc của app (giống ui/tabs/event.json) để bản
# build (Nuitka) cũng tìm được.
PRIORITY_FILE = TEMPLATE_DIR.parent / "bot" / "worker" / "priority.json"
DEFAULT_PRIORITY = 1


@dataclass
class Task:
    key: str        # VD "Event" (bước 1: tên activity)
    group: str      # activity chứa nhiệm vụ = tên chạy qua ACTIVITIES / tab settings
    priority: int


def load_priorities(path=PRIORITY_FILE) -> dict[str, dict[str, int]]:
    """{nhóm: {key nhiệm vụ: độ ưu tiên}} từ priority.json; thiếu / lỗi file thì {} (mọi nhiệm vụ
    dùng DEFAULT_PRIORITY)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    result = {}
    for group, tasks in data.items():
        if group.startswith("_") or not isinstance(tasks, list):
            continue
        result[group] = {t["key"]: int(t.get("priority", DEFAULT_PRIORITY))
                         for t in tasks if isinstance(t, dict) and "key" in t}
    return result


def group_priority(priorities: dict, group: str) -> int:
    """Độ ưu tiên của cả nhóm = cao nhất trong các nhiệm vụ của nhóm (nhóm không có trong file:
    DEFAULT_PRIORITY)."""
    values = priorities.get(group, {}).values()
    return max(values) if values else DEFAULT_PRIORITY


def build_tasks(activities: list[str], skip: set[str], priorities: dict) -> list[Task]:
    """Mỗi activity đã chọn (trừ `skip`, VD Join Boss) -> 1 nhiệm vụ, theo thứ tự đã chọn."""
    return [Task(key=activity, group=activity, priority=group_priority(priorities, activity))
            for activity in activities if activity not in skip]
