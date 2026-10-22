"""
tasks.py — danh sách nhiệm vụ của worker, dựng từ bảng priority.py.

Mỗi dòng của bảng có `run` (một hàm trơn `run(ctx, cấu hình tab)`, hoặc một dict `{"run", "enabled", "done", "every"}` do code của
nhiệm vụ dựng sẵn, VD daily_job(...), event_job(...)), `priority`, và tuỳ chọn `must_finish`, `once`,
`group` (nhóm chọn nhiệm vụ, nếu khác nhóm chứa dòng), `idle_only` (chỉ chạy khi không còn nhiệm vụ nào khác), `saves` (hàm `run` tự lưu key của dòng vào DB khi làm xong:
xong hôm nay = key đó có trong DB). Luật của từng nhiệm vụ (được tích chưa, hôm nay xong chưa — đọc từ DB —
bao lâu làm một lần) nằm trong dict đó, cạnh code của nhiệm vụ; ở đây chỉ ghép lại thành `Task` cho vòng lặp ở bot_worker.py.
"""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from .priority import DATA

DEFAULT_PRIORITY = 1


def always(settings: dict) -> bool:
    """enabled cho nhiệm vụ không có ô tích riêng (chọn activity là chạy)."""
    return True


@dataclass
class Task:
    key: str        # key nhiệm vụ trong priority.py / settings / daily_done
    group: str      # activity chứa nhiệm vụ = tên chạy qua ACTIVITIES / tab settings
    priority: int
    must_finish: bool = False   # bắt đầu rồi thì chạy tới xong, không bị ngắt (trừ Stop)
    tail: bool = False          # nhiệm vụ nhận thưởng cuối chuỗi: nhiệm vụ cùng nhóm bị chuyển xuống cuối thì dừng trước nó
    once: bool = False          # xong rồi thì không đưa lại vào danh sách khi sang ngày mới (chỉ chạy lại khi Start lại)
    idle_only: bool = False     # chỉ chạy khi RẢNH: không còn nhiệm vụ nào khác tới lượt (kể cả việc theo giờ chưa tới giờ); không bị giới hạn 120 giây
    needs_city_map: bool = False  # cần route công trình: chưa có bản đồ thành trong DB thì worker quét trước khi chạy
    run: Callable | None = None  # run(ctx, cấu hình tab của group): làm nhiệm vụ rồi lưu kết quả vào DB
    enabled: Callable[[dict], bool] = always       # enabled(cấu hình tab của group) -> nhiệm vụ này đã được tích?
    done: Callable | None = None                   # done(ctx, cấu hình tab của group) -> hôm nay đã xong chưa? (đọc DB)
    due: Callable | None = None                    # due(ctx, cấu hình tab của group) -> việc theo giờ: đã tới giờ làm chưa?


def _hours_since(ctx, key: str) -> float | None:
    """Số giờ kể từ lần làm trước (giờ lưu trong daily_done `key`), None nếu chưa làm lần nào."""
    try:
        return (datetime.now() - datetime.fromisoformat(ctx.done_at(key))).total_seconds() / 3600
    except (TypeError, ValueError):
        return None


def build_task(row: dict, group: str) -> Task:
    """Một dòng của bảng -> Task. Worker KHÔNG ghi gì vào DB: nhiệm vụ (bot/activities) tự lưu kết quả của nó. Việc theo giờ
    (dict có "every"): nhiệm vụ tự lưu giờ vừa làm vào DB (`<key>_tried`); `due` chỉ so giờ đó với số giờ trên tab."""
    key = row["key"]
    job = row["run"] if isinstance(row["run"], dict) else {"run": row["run"]}
    every = job.get("every")
    due = None
    if every is not None:
        tried_key = f"{key}_tried"

        def due(ctx, settings, every=every, tried_key=tried_key):
            hours = every(settings)
            since = _hours_since(ctx, tried_key)
            return hours > 0 and (since is None or since >= hours)

    return Task(key, row.get("group", group), int(row.get("priority", DEFAULT_PRIORITY)),
                must_finish=bool(row.get("must_finish")), once=bool(row.get("once")), tail=bool(row.get("tail")), idle_only=bool(row.get("idle_only")), needs_city_map=bool(row.get("needs_city_map")),
                run=job["run"], enabled=job.get("enabled", always), due=due,
                done=job.get("done") or ((lambda ctx, settings: ctx.is_daily_done(key)) if row.get("saves") else None))


def sink(order: list[Task], task: Task):
    """Nhiệm vụ chưa xong: chuyển xuống cuối chuỗi cùng nhóm, nhưng trên các nhiệm vụ `tail` (nhận thưởng) của nhóm đó. Nhiệm
    vụ `tail` thì xuống cuối danh sách. Nhóm không có nhiệm vụ `tail` thì cuối nhóm."""
    order.remove(task)
    if task.tail:
        order.append(task)
        return
    last = max((i for i, t in enumerate(order) if t.group == task.group and not t.tail), default=None)
    order.insert(len(order) if last is None else last + 1, task)


def build_registry(data: dict) -> list[Task]:
    """Mọi nhiệm vụ (dòng có `run`) của bảng `data` (priority.DATA), theo thứ tự trong bảng."""
    return [build_task(row, group) for group, rows in data.items()
            if not group.startswith("_") and isinstance(rows, list) for row in rows if "run" in row]


REGISTRY: list[Task] = build_registry(DATA)


def build_tasks(activities: list[str], skip: set[str], settings: dict | None = None,
                registry: list[Task] | None = None) -> list[Task]:
    """Danh sách nhiệm vụ khi bấm Start: mọi nhiệm vụ có group nằm trong `activities` (activity chỉ dùng để chia loại;
    `skip`: VD Join Boss) và đã được tích (`enabled` nhận cấu hình tab của group, lấy từ `settings`), xếp theo độ ưu tiên
    (số lớn làm trước; cùng ưu tiên thì theo thứ tự trong bảng). Độ ưu tiên < 0 không được đưa vào danh sách."""
    settings = settings or {}
    tasks = [task for task in (REGISTRY if registry is None else registry)
             if task.group in activities and task.group not in skip
             and task.enabled(settings.get(task.group, {})) and task.priority >= 0]
    return sorted(tasks, key=lambda task: -task.priority)
