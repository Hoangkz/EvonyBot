"""
stamina_wait.py — mốc "hết thể lực, tới giờ này mới Join Boss lại" lưu trong DB (daily_done).

Hết thể lực thì Join Boss báo rảnh và lưu mốc = bây giờ + STAMINA_WAIT_MINUTES. Mốc nằm trong TÊN khoá daily_done
`join_boss_stamina_until_<YYYY-MM-DD HH:MM:SS>` (giá trị là giờ lưu, như `<event>_cycle_reset_...` ở event/cycle.py nên DB không đổi
cách lưu). Worker mỗi vòng so mốc với giờ hiện tại: chưa tới thì làm nhiệm vụ, qua mốc thì Join Boss lại.
"""
from datetime import datetime, timedelta

STAMINA_WAIT_MINUTES = 20
PREFIX = "join_boss_stamina_until_"
_FORMAT = "%Y-%m-%d %H:%M:%S"


def until_from_keys(keys) -> datetime | None:
    """Mốc muộn nhất đã lưu trong các khoá daily_done `keys`, None nếu chưa có."""
    found = []
    for key in keys:
        if key.startswith(PREFIX):
            try:
                found.append(datetime.strptime(key[len(PREFIX):], _FORMAT))
            except ValueError:
                continue
    return max(found, default=None)


def waiting(keys, now: datetime | None = None) -> bool:
    """Còn trong thời gian chờ thể lực hồi (chưa tới mốc đã lưu)."""
    until = until_from_keys(keys)
    return until is not None and (now or datetime.now()) < until


def save(ctx, now: datetime | None = None) -> datetime:
    """Lưu mốc mới = bây giờ + STAMINA_WAIT_MINUTES vào DB, bỏ các mốc cũ. Trả mốc vừa lưu."""
    now = now or datetime.now()
    until = (now + timedelta(minutes=STAMINA_WAIT_MINUTES)).replace(microsecond=0)
    old = [key for key in ctx.daily_keys() if key.startswith(PREFIX)]
    ctx.mark_daily_done(f"{PREFIX}{until.strftime(_FORMAT)}")
    for key in old:
        ctx.forget_daily(key)
    return until
