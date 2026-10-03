"""
scheduler.py — Scheduler: chọn nhiệm vụ tiếp theo cho BotWorker.

- Nhiệm vụ tới lượt: chưa làm xong lần nào, hoặc đã qua mốc reset server kể từ lần bắt đầu lượt làm
  xong gần nhất (sang ngày mới thì làm lại).
- Chọn nhiệm vụ tới lượt có độ ưu tiên cao nhất (số lớn hơn làm trước); cùng ưu tiên thì xoay vòng
  (nhiệm vụ lâu chưa được bắt đầu nhất đi trước, chưa từng chạy thì theo thứ tự danh sách).
"""
from collections.abc import Callable
from datetime import datetime

from .tasks import Task


class Scheduler:
    def __init__(self, tasks: list[Task], last_reset: Callable[[], datetime]):
        self.tasks = list(tasks)
        self._last_reset = last_reset
        self._done_for: dict[str, datetime] = {}      # key -> mốc reset lúc bắt đầu lượt làm xong
        self._started_reset: dict[str, datetime] = {}  # key -> mốc reset lúc bắt đầu lượt đang chạy
        self._last_start: dict[str, int] = {}          # key -> số thứ tự lần bắt đầu gần nhất
        self._counter = 0

    def is_due(self, task: Task) -> bool:
        done_for = self._done_for.get(task.key)
        return done_for is None or self._last_reset() > done_for

    def pick(self) -> Task | None:
        """Nhiệm vụ tới lượt nên làm tiếp, hoặc None nếu không còn nhiệm vụ nào tới lượt."""
        due = [(i, task) for i, task in enumerate(self.tasks) if self.is_due(task)]
        if not due:
            return None
        return min(due, key=lambda item: (-item[1].priority, self._last_start.get(item[1].key, -1), item[0]))[1]

    def started(self, task: Task):
        self._counter += 1
        self._last_start[task.key] = self._counter
        self._started_reset[task.key] = self._last_reset()

    def finished(self, task: Task):
        """Nhiệm vụ chạy tới cuối: xong tới mốc reset kế tiếp (tính theo lúc bắt đầu lượt này)."""
        self._done_for[task.key] = self._started_reset.pop(task.key, self._last_reset())
