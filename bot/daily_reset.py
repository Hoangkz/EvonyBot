"""daily_reset.py — mốc reset hằng ngày của server, theo giờ máy."""
from datetime import datetime, timedelta

DAY = timedelta(days=1)


def last_reset(server_time: str, now: datetime | None = None) -> datetime:
    """Mốc reset gần nhất (<= now). server_time là một lần reset bất kỳ (ISO);
    các lần reset cách nhau đúng 24 giờ. Chưa biết server_time thì dùng 0h giờ máy."""
    now = now or datetime.now()
    try:
        base = datetime.fromisoformat(server_time)
    except (TypeError, ValueError):
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    return base + (now - base) // DAY * DAY


def done_today(done_at: str | None, server_time: str, now: datetime | None = None) -> bool:
    """done_at (ISO) nằm sau mốc reset gần nhất -> đã làm trong ngày hiện tại."""
    if not done_at:
        return False
    try:
        return datetime.fromisoformat(done_at) >= last_reset(server_time, now)
    except ValueError:
        return False
