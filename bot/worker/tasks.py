"""
tasks.py — danh sách nhiệm vụ của bộ chọn (scheduler.py) và độ ưu tiên đọc từ priority.py.

Khi bấm Start, build_tasks lấy mọi nhiệm vụ trong bảng bot/worker/registry.py có nhóm (activity) được chọn và đã
được tích, sắp theo độ ưu tiên của chính nhiệm vụ; mỗi Task mang hàm `run` riêng để worker gọi thẳng. Activity chỉ
dùng để chia loại. Nhiệm vụ có "must_finish": true trong priority.py: đã bắt đầu thì chạy tới xong, không bị Bubble /
Join Boss / giới hạn 120 giây ngắt (chỉ Stop). Bubble và Join Boss có luật riêng trong BotWorker.
"""
import json
from collections.abc import Callable
from dataclasses import dataclass

from .priority import DATA as PRIORITY

DEFAULT_PRIORITY = 1

def _read(path) -> dict:
    """Dữ liệu ưu tiên: mặc định từ priority.py (Nuitka compile cùng code, không cần
    ship file riêng); `path` (file .json riêng, test) thiếu / lỗi file thì {}."""
    if path is None:
        return PRIORITY
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@dataclass
class Task:
    key: str        # VD "Event" (bước 1: tên activity)
    group: str      # activity chứa nhiệm vụ = tên chạy qua ACTIVITIES / tab settings
    priority: int
    must_finish: bool = False   # bắt đầu rồi thì chạy tới xong, không bị ngắt (trừ Stop)
    once: bool = False          # xong rồi thì không tới lượt lại khi qua mốc reset server
    repeat: bool = False        # hẹn chạy lại thì vẫn giữ độ ưu tiên của nó
    run: Callable | None = None  # hàm riêng của nhiệm vụ: run(bot, cấu hình tab của group); worker gọi thẳng


def load_priorities(path=None) -> dict[str, dict[str, int]]:
    """{nhóm: {key nhiệm vụ: độ ưu tiên}} từ priority.py (hoặc file .json ở `path`); thiếu /
    lỗi file thì {} (mọi nhiệm vụ dùng DEFAULT_PRIORITY)."""
    data = _read(path)
    result = {}
    for group, tasks in data.items():
        if group.startswith("_") or not isinstance(tasks, list):
            continue
        result[group] = {t["key"]: int(t.get("priority", DEFAULT_PRIORITY))
                         for t in tasks if isinstance(t, dict) and "key" in t}
    return result


def load_must_finish(path=None) -> dict[str, set[str]]:
    """{nhóm: {key nhiệm vụ có "must_finish": true}}; nhóm có ít nhất 1 nhiệm vụ mới có mặt.
    Thiếu / lỗi file thì {}."""
    data = _read(path)
    result = {}
    for group, tasks in data.items():
        if group.startswith("_") or not isinstance(tasks, list):
            continue
        keys = {t["key"] for t in tasks if isinstance(t, dict) and "key" in t and t.get("must_finish")}
        if keys:
            result[group] = keys
    return result


def build_tasks(activities: list[str], skip: set[str], priorities: dict, must_finish: dict | None = None,
                settings: dict | None = None, registry=None) -> list[Task]:
    """Danh sách nhiệm vụ khi bấm Start: mọi nhiệm vụ trong `registry` (bot/worker/registry.py) có group nằm
    trong `activities` (activity chỉ dùng để chia loại; `skip`: VD Join Boss) và đã được tích (`enabled` nhận cấu
    hình tab của group, lấy từ `settings`). Mỗi nhiệm vụ theo độ ưu tiên của chính nó (priority.py, số lớn làm
    trước); ưu tiên < 0 không được đưa vào danh sách. Cùng ưu tiên thì theo thứ tự trong registry."""
    must_keys = set().union(*(must_finish or {}).values())
    by_key = {key: priority for group in priorities.values() for key, priority in group.items()}
    settings = settings or {}
    tasks = []
    for definition in registry or []:
        if definition.group not in activities or definition.group in skip:
            continue
        if not definition.enabled(settings.get(definition.group, {})):
            continue
        priority = by_key.get(definition.key, DEFAULT_PRIORITY)
        if priority < 0:
            continue
        tasks.append(Task(key=definition.key, group=definition.group, priority=priority,
                          must_finish=definition.key in must_keys, once=definition.once,
                          repeat=definition.repeat, run=definition.run))
    return tasks
