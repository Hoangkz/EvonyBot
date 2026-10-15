"""
cycle.py — mốc reset của các event 7 ngày (Gather Troops, King's Path), dựa vào thời gian còn lại của event.

Sau khi event 7 ngày hết thì tới event 3 ngày (THREE_DAY_LENGTH ngày, Event Center > Limited); hết event 3 ngày mới có thể có event
7 ngày mới (chỉ là suy đoán, không chắc chắn). Nên bot đọc "Event Quest Countdown" trên màn event (OCR
bot/ocr/read_event_countdown.py) rồi mốc reset = bây giờ + thời gian còn lại + THREE_DAY_LENGTH ngày = lúc event 3 ngày hết, lưu vào DB.
Mốc nằm trong TÊN khoá daily_done `<event>_cycle_reset_<YYYY-MM-DD HH:MM>` (VD `kings_path_cycle_reset_2026-10-21 14:15`; giá trị là
giờ lưu, như mọi khoá khác nên không cần đổi cách lưu của DB). Qua mốc reset thì các dấu hết-Go / đạt-mục-tiêu của event cũ hết hiệu
lực -> nhiệm vụ được làm lại (nếu event mới chưa có thì nhiệm vụ không tìm thấy event, thử lại vô hại; có event thì đọc lại mốc mới);
tab Event trên UI cũng đọc mốc này để hiện thời gian còn lại. Event 3 ngày chỉ bắt đầu sau khi King's Path hết (three_day_window; Gather Troops không liên quan, nó thường có trước King's Path 3 ngày).

Chỉ kiểm tra khi event CHƯA có mốc reset hoặc ĐÃ QUÁ mốc reset (needs_check). Thời gian OCR phải chắc chắn: đọc 2 lần cách nhau
1 giây phải giống nhau (lệch tối đa 60 giây) và nằm trong khoảng hợp lý; đọc ra ? / không chắc thì ghi log, KHÔNG lưu DB, lần
vào event sau đọc lại.
"""
from datetime import datetime, timedelta

from ...ocr.read_event_countdown import read as read_countdown
from .constants import GATHER_TROOPS_ICON, KINGS_PATH_ICON

EVENT_DAYS = 7           # event có nhiệm vụ trong 7 ngày (chặn đọc sai thời gian còn lại)
THREE_DAY_LENGTH = 3     # event 3 ngày kéo dài 3 ngày ngay sau khi event 7 ngày hết; mốc reset = hết event + THREE_DAY_LENGTH
MAX_COUNTDOWN = EVENT_DAYS * 86400   # thời gian còn lại lớn hơn mức này = đọc sai
SAME_SECONDS = 60                    # hai lần đọc lệch nhau quá chừng này = đọc không chắc

# Icon event trong danh sách event -> key event (cùng key với EVENTS ở event/run.py).
EVENT_OF_ICON = {GATHER_TROOPS_ICON: "gather_troops", KINGS_PATH_ICON: "kings_path"}

_FORMAT = "%Y-%m-%d %H:%M"


def _prefix(event: str) -> str:
    return f"{event}_cycle_reset_"


# ---- Đọc mốc đã lưu (hàm thuần theo danh sách khoá, UI dùng chung) ------------------------------------------
def resets_from_keys(keys, event: str) -> list[datetime]:
    """Mọi mốc reset đã lưu của `event` trong các khoá daily_done `keys`, tăng dần."""
    prefix = _prefix(event)
    found = []
    for key in keys:
        if key.startswith(prefix):
            try:
                found.append(datetime.strptime(key[len(prefix):], _FORMAT))
            except ValueError:
                continue
    return sorted(found)


def event_end(reset: datetime) -> datetime:
    """Lúc event 7 ngày hết (event 3 ngày bắt đầu) = mốc reset - THREE_DAY_LENGTH ngày."""
    return reset - timedelta(days=THREE_DAY_LENGTH)


def _left(delta: timedelta) -> str:
    seconds = max(0, int(delta.total_seconds()))
    days, rest = divmod(seconds, 86400)
    hours, minutes = rest // 3600, rest % 3600 // 60
    return f"{days}d {hours:02d}:{minutes:02d}" if days else f"{hours:02d}:{minutes:02d}"


# ---- Event 3 ngày (Event Center > Limited): chỉ xuất hiện sau khi King's Path kết thúc (không phụ thuộc Gather Troops) ----------------
THREE_DAY = "three_day"


def three_day_window(keys, now: datetime | None = None) -> tuple[datetime, datetime] | None:
    """(bắt đầu, kết thúc) của event 3 ngày kế tiếp / đang diễn ra, CHỈ dựa vào King's Path (Gather Troops thường có trước King's
    Path 3 ngày nên không dùng): bắt đầu = lúc King's Path hết event, kết thúc = mốc reset King's Path. None nếu chưa có mốc King's
    Path, hoặc mốc đã qua (chưa đọc lại: không biết event 3 ngày kế tiếp khi nào)."""
    found = resets_from_keys(keys, "kings_path")
    if not found or (now or datetime.now()) >= found[-1]:
        return None
    return event_end(found[-1]), found[-1]


def three_day_waiting(ctx, now: datetime | None = None) -> bool:
    """Event 3 ngày chưa bắt đầu (King's Path còn đang diễn ra): chưa cần vào Event Center tìm."""
    window = three_day_window(ctx.daily_keys(), now)
    return window is not None and (now or datetime.now()) < window[0]


def describe(keys, event: str, now: datetime | None = None) -> str | None:
    """Dòng chữ cho tab Event: thời gian còn lại của event / ngày event mới. None nếu chưa có mốc nào (chưa đọc được)."""
    now = now or datetime.now()
    if event == THREE_DAY:
        window = three_day_window(keys, now)
        if window is None:
            return None
        start, end = window
        if now < start:
            return f"bắt đầu sau {_left(start - now)} ({start:%d/%m/%Y %H:%M})"
        return f"còn {_left(end - now)}"
    found = resets_from_keys(keys, event)
    if not found:
        return None
    reset = found[-1]
    end = event_end(reset)
    if now < end:
        return f"còn {_left(end - now)}"
    if now < reset:
        return f"hết event, event 3 ngày tới {reset:%d/%m/%Y %H:%M}"
    return "đã quá mốc reset, chờ đọc lại"


# ---- Dùng trong bot (ctx = BotContext) ----------------------------------------------------------------------
def resets(ctx, event: str) -> list[datetime]:
    return resets_from_keys(ctx.daily_keys(), event)


def current_reset(ctx, event: str) -> datetime | None:
    """Mốc reset gần nhất đã lưu (cuối chu kỳ hiện tại), None nếu chưa lưu lần nào."""
    found = resets(ctx, event)
    return found[-1] if found else None


def needs_check(ctx, event: str, now: datetime | None = None) -> bool:
    """Chưa có mốc reset, hoặc hiện tại đã quá mốc reset: phải đọc lại thời gian còn lại của event."""
    reset = current_reset(ctx, event)
    return reset is None or (now or datetime.now()) >= reset


def fresh_since(ctx, event: str, now: datetime | None = None) -> datetime:
    """Dấu hoàn thành của event chỉ còn hiệu lực nếu được lưu từ mốc này: đã quá mốc reset -> chính mốc đó (mọi dấu cũ hết
    hiệu lực); chưa quá -> mốc reset của chu kỳ trước (chưa có thì không giới hạn)."""
    found = resets(ctx, event)
    if not found:
        return datetime.min
    if (now or datetime.now()) >= found[-1]:
        return found[-1]
    return found[-2] if len(found) > 1 else datetime.min


def valid(ctx, event: str, done_at: str | None, now: datetime | None = None) -> bool:
    """Dấu hoàn thành (giờ ISO, lấy từ ctx.done_at) còn hiệu lực trong chu kỳ hiện tại của `event`."""
    if not done_at:
        return False
    try:
        return datetime.fromisoformat(done_at) >= fresh_since(ctx, event, now)
    except ValueError:
        return False


def read_remaining(bot) -> int | None:
    """Thời gian còn lại của event (giây) trên màn event, đọc 2 lần cách nhau 1 giây phải giống nhau. None (và ghi log) nếu
    đọc ra ? / không chắc."""
    first = read_countdown(bot, bot.screenshot())
    bot.sleep(1)
    second = read_countdown(bot, bot.screenshot())
    if first is None or second is None:
        bot.record(f"Event: cannot read event countdown ({first}, {second}), not saved, will retry next time")
        return None
    if abs(first - second) > SAME_SECONDS or not 0 < second <= MAX_COUNTDOWN:
        bot.record(f"Event: event countdown not reliable ({first}s, {second}s), not saved, will retry next time")
        return None
    return second


def record(bot, event: str, remaining: int, now: datetime | None = None) -> datetime:
    """Lưu mốc reset của `event` (bây giờ + thời gian còn lại + THREE_DAY_LENGTH ngày (lúc event 3 ngày hết), làm tròn tới phút) vào DB."""
    now = now or datetime.now()
    when = (now + timedelta(seconds=remaining, days=THREE_DAY_LENGTH)).replace(second=0, microsecond=0)
    bot.mark_daily_done(f"{_prefix(event)}{when:{_FORMAT}}")
    bot.record(f"Event: {event} ends in {remaining // 86400}d {remaining % 86400 // 3600:02d}:{remaining % 3600 // 60:02d}, "
               f"tasks reset at {when:%d/%m/%Y %H:%M}")
    return when


def observe(bot, icon: str) -> None:
    """Gọi khi vừa mở event có icon `icon`: chỉ khi event chưa có mốc reset hoặc đã quá mốc reset thì đọc thời gian còn lại
    và lưu mốc reset mới (chỉ lưu khi OCR chắc chắn)."""
    event = EVENT_OF_ICON.get(icon)
    if event is None or not needs_check(bot, event):
        return
    remaining = read_remaining(bot)
    if remaining is not None:
        record(bot, event, remaining)
