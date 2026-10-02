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
    """Activity phụ vừa xong một nhiệm vụ (bot.yield_to_boss()): nhường ngay để worker kiểm tra
    boss, không làm tiếp nhiệm vụ sau trong lượt OTHERS_WINDOW. Activity vẫn ở danh sách chờ,
    lượt sau gọi lại từ đầu (nhiệm vụ đã xong tự bỏ qua)."""


class BubbleDue(BotInterrupted):
    """Bubble sắp hết: dừng activity đang chạy (kể cả Join Boss) để gia hạn trước."""
