"""
stamina_wait.py — mốc "hết thể lực, tới lúc này mới Join Boss lại", chỉ giữ trong một lượt chạy (Start -> Stop), không lưu DB.

Hết thể lực thì Join Boss báo rảnh và đặt mốc = bây giờ + STAMINA_WAIT_MINUTES lên BotContext (`ctx.stamina_until`, sống cùng
BotContext như boss_memory). Mốc đo bằng time.monotonic() nên đổi giờ Windows không làm lệch; Stop / Start lại thì mốc mất, Join Boss
thử lại ngay. Worker mỗi vòng hỏi `waiting`: chưa tới mốc thì làm nhiệm vụ, qua mốc thì Join Boss lại.
"""
import time
from datetime import datetime, timedelta

STAMINA_WAIT_MINUTES = 20


def save(ctx, now: float | None = None) -> datetime:
    """Đặt mốc mới = bây giờ + STAMINA_WAIT_MINUTES (thay mốc cũ). Trả giờ đồng hồ của mốc để ghi log."""
    ctx.stamina_until = (time.monotonic() if now is None else now) + STAMINA_WAIT_MINUTES * 60
    return (datetime.now() + timedelta(minutes=STAMINA_WAIT_MINUTES)).replace(microsecond=0)


def remaining(ctx, now: float | None = None) -> float:
    """Số giây còn phải chờ thể lực hồi (0 nếu không chờ)."""
    until = getattr(ctx, "stamina_until", None)
    if not isinstance(until, (int, float)):   # chưa hết thể lực lần nào trong lượt chạy này
        return 0.0
    return max(until - (time.monotonic() if now is None else now), 0.0)


def waiting(ctx, now: float | None = None) -> bool:
    """Còn trong thời gian chờ thể lực hồi (chưa tới mốc)."""
    return remaining(ctx, now) > 0
