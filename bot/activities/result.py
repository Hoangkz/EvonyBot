"""
result.py — TaskResult: kết quả một nhiệm vụ trả cho worker (không import gì, để mọi gói dùng được).

Nhiệm vụ chỉ làm thao tác trong game rồi báo đã xong hay chưa; việc ghi "xong hôm nay", hẹn thử lại, bỏ qua nhiệm vụ đã
xong, chọn nhiệm vụ nào chạy tiếp là của worker (bot/worker/). Hàm vào của nhiệm vụ trả TaskResult. Luồng sâu bên trong
(handler đã xong giữa chừng rồi còn Back đóng popup) báo bằng `report()` / `done()`; hàm vào gom lại bằng `take()` /
`take_all()`.

Trạng thái "đã làm tới đâu" mà nhiệm vụ tự nhớ giữa các bước nhỏ của chính nó (VD đã patrol lượt thứ n, đã nhận rương
đăng nhập hôm nay) không phải kết quả nhiệm vụ: vẫn lưu bằng bot.is_daily_done / bot.mark_daily_done.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TaskResult:
    done: bool = False                   # nhiệm vụ đã xong (trong ngày)
    reached: int | None = None           # mục tiêu đã đạt hôm nay (0 = không còn gì để làm); None = không có
    retry_after: float | None = None     # giây: nhiệm vụ muốn được thử lại sau chừng đó (worker quyết định có hẹn không)
    complete: bool = False               # Event: hết nút Go, xong hẳn cả vòng event (mọi mục tiêu)
    target_reached: bool = False         # Event: đạt số lượng người dùng chọn mà vẫn còn Go
    locked: bool = False                 # Event: Day / cấp lính còn khoá, chưa thể làm tới lần reset server
    label: str | None = None             # nhãn / key của nhiệm vụ (hoặc nhiệm vụ con) báo kết quả giữa chừng: chỉ để
    key: str | None = None               # nhận diện, worker ghi theo TaskDef / cấu hình của chính nó
    outcomes: tuple["TaskResult", ...] = ()   # kết quả báo giữa chừng (report), kể cả của nhiệm vụ con

    def __bool__(self) -> bool:
        return self.done


NOT_DONE = TaskResult()
_ATTR = "_task_results"


def report(bot, result: TaskResult) -> TaskResult:
    """Luồng bên trong báo một kết quả (kèm `label` / `key` của nhiệm vụ); hàm vào lấy lại bằng take() / take_all()."""
    pending = getattr(bot, _ATTR, None)
    if pending is None:
        pending = []
        setattr(bot, _ATTR, pending)
    pending.append(result)
    return result


def done(bot, reached: int | None = None, *, label: str | None = None, key: str | None = None) -> TaskResult:
    """Luồng bên trong báo: nhiệm vụ đã xong (kèm mục tiêu `reached` nếu có)."""
    return report(bot, TaskResult(done=True, reached=reached, label=label, key=key))


def take_all(bot) -> list[TaskResult]:
    """Lấy và xoá mọi kết quả đã báo giữa chừng (theo thứ tự báo)."""
    pending = getattr(bot, _ATTR, None) or []
    setattr(bot, _ATTR, [])
    return list(pending)


def take(bot) -> TaskResult | None:
    """Lấy và xoá mọi kết quả đã báo giữa chừng, trả kết quả báo sau cùng (None nếu chưa có)."""
    pending = take_all(bot)
    return pending[-1] if pending else None


def clear(bot):
    """Bỏ kết quả báo dở của lần chạy trước (gọi ở đầu hàm vào)."""
    setattr(bot, _ATTR, [])
