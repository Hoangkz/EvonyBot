"""daily_reset.py — mốc reset hằng ngày của server, theo giờ máy.

Giờ reset do người dùng chọn ở màn Home (dạng "HH:MM", mặc định DEFAULT_RESET_TIME), lưu ở bảng
`settings` của DB, dùng chung mọi thiết bị. Vẫn đọc được giá trị cũ dạng ISO (một lần reset bất kỳ).
"""
from datetime import datetime, time, timedelta

DAY = timedelta(days=1)
DEFAULT_RESET_TIME = "14:00"


def reset_clock(server_time: str | None) -> str:
    """Giờ reset dạng "HH:MM" từ giá trị đã lưu ("HH:MM" hoặc ISO cũ); rỗng / sai -> DEFAULT_RESET_TIME."""
    parsed = _parse_clock(server_time)
    return parsed.strftime("%H:%M") if parsed is not None else DEFAULT_RESET_TIME


def _parse_clock(server_time: str | None) -> time | None:
    if not server_time:
        return None
    try:
        return datetime.strptime(server_time.strip(), "%H:%M").time()
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(server_time).time()
    except (TypeError, ValueError):
        return None


def last_reset(server_time: str, now: datetime | None = None) -> datetime:
    """Mốc reset gần nhất (<= now): hôm nay lúc giờ reset, hoặc hôm qua nếu chưa tới giờ.
    server_time là "HH:MM" (hoặc ISO cũ); rỗng / sai thì dùng DEFAULT_RESET_TIME."""
    now = now or datetime.now()
    clock = _parse_clock(server_time) or _parse_clock(DEFAULT_RESET_TIME)
    today = now.replace(hour=clock.hour, minute=clock.minute, second=0, microsecond=0)
    return today if today <= now else today - DAY


def done_today(done_at: str | None, server_time: str, now: datetime | None = None) -> bool:
    """done_at (ISO) nằm sau mốc reset gần nhất -> đã làm trong ngày hiện tại."""
    if not done_at:
        return False
    try:
        return datetime.fromisoformat(done_at) >= last_reset(server_time, now)
    except ValueError:
        return False
