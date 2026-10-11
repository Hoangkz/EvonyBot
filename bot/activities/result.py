"""
result.py — TaskResult: kết quả một nhiệm vụ trả cho worker (không import gì, để mọi gói dùng được).

Nhiệm vụ chỉ làm thao tác trong game rồi báo đã xong hay chưa; việc ghi "xong hôm nay", bỏ qua nhiệm vụ đã
xong, chọn nhiệm vụ nào chạy tiếp là của worker (bot/worker/). Hàm vào của nhiệm vụ trả TaskResult. Luồng sâu bên trong
(handler đã xong giữa chừng rồi còn Back đóng popup) báo bằng `report()` / `done()`; hàm vào gom lại bằng `take()` /
`take_all()`.

Trạng thái "đã làm tới đâu" mà nhiệm vụ tự nhớ giữa các bước nhỏ của chính nó (VD đã patrol lượt thứ n, đã nhận rương
đăng nhập hôm nay) không phải kết quả nhiệm vụ: vẫn lưu bằng bot.is_daily_done / bot.mark_daily_done.
"""
import functools
from contextlib import contextmanager
from dataclasses import dataclass

from ..context.errors import BotInterrupted


@dataclass(frozen=True)
class TaskResult:
    done: bool = False                   # nhiệm vụ đã xong (trong ngày)
    reached: int | None = None           # mục tiêu đã đạt hôm nay (0 = không còn gì để làm); None = không có
    complete: bool = False               # Event: hết nút Go, xong hẳn cả vòng event (mọi mục tiêu)
    target_reached: bool = False         # Event: đạt số lượng người dùng chọn mà vẫn còn Go
    locked: bool = False                 # Event: Day / cấp lính còn khoá, chưa thể làm tới lần reset server
    label: str | None = None             # nhãn / key của nhiệm vụ (hoặc nhiệm vụ con) báo kết quả giữa chừng: chỉ để
    key: str | None = None               # nhận diện, worker ghi theo dòng priority.py / cấu hình của chính nó
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


# ---- Lưu LỖI của nhiệm vụ vào DB ngay tại chỗ chạy --------------------------------------------------------------------
# Quy ước: mỗi nhiệm vụ trong bot/activities tự lưu kết quả vào DB (daily_done) ngay chỗ biết kết quả:
# - xong: bot.mark_daily_done(<key>) (hoặc các dấu mục tiêu, VD "<key>_reached_N");
# - lỗi: `<key>_error` (giờ gặp lỗi) + một dòng History (bảng logs) ghi tên nhiệm vụ và lỗi, rồi báo lỗi lên tiếp;
# - bị ngắt (Stop, hết 120 giây, có boss, bubble) không phải lỗi, không lưu gì: chưa xong, lượt sau làm tiếp.
# Worker (bot/worker) không ghi gì: chỉ lấy danh sách nhiệm vụ, kiểm tra đã xong chưa (đọc DB), chưa xong thì chạy.
@contextmanager
def saving_status(ctx, key: str):
    """Chạy một nhiệm vụ `key`; lỗi thật thì lưu `<key>_error` + History vào DB rồi ném lỗi lên tiếp."""
    try:
        yield
    except BotInterrupted:
        raise
    except Exception as error:
        ctx.mark_daily_done(f"{key}_error")
        ctx.record(f"{key}: lỗi {type(error).__name__}: {error}")
        raise


def save_errors(key: str):
    """Decorator cho hàm run(ctx, ...) của nhiệm vụ `key`: lỗi thì lưu vào DB (xem saving_status)."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(ctx, *args, **kwargs):
            with saving_status(ctx, key):
                return fn(ctx, *args, **kwargs)
        return wrapper
    return decorator
