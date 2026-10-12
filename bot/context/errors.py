"""
errors.py — the exceptions that end a run early (not an error).
"""


class BotInterrupted(Exception):
    """Base for the exceptions that end a run early (not an error)."""


class StopRequested(BotInterrupted):
    pass


class TimedOut(BotInterrupted):
    pass


class BossAvailable(BotInterrupted):
    """Yield a secondary activity to a new boss on the same server."""


class YieldToBoss(BotInterrupted):
    """Nhiệm vụ tự nhường lượt cho Join Boss tại điểm an toàn (kể cả nhiệm vụ must_finish); chưa xong, làm tiếp lần sau."""


class BubbleDue(BotInterrupted):
    """Bubble sắp hết: dừng activity đang chạy (kể cả Join Boss) để gia hạn trước."""


class RestartDue(BotInterrupted):
    """Tới giờ "Auto Times Out" (màn Home): dừng activity đang chạy để đóng game (bot tự mở lại khi chạy tiếp).
    Xét sau BubbleDue: bubble vẫn được lo trước."""


class ResetDue(BotInterrupted):
    """Tới mốc reset server (giờ chọn ở màn Home): dừng việc đang chạy, kể cả nhiệm vụ must_finish, để tắt game bật lại. Việc
    đang dở làm lại từ đầu sau khi game mở lại (sang ngày mới các dấu "xong" của hôm qua đã hết hiệu lực)."""

