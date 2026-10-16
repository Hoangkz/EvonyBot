"""Hoạt động Event Center: các event con trong danh sách Limited của Event Center."""
from .. import scan
from ..common import open_event_center, return_home
from .run import EVENT_POLICIES, run_opened

KEY = "gift_event_center"
TASKS = tuple((policy.key, policy.label) for policy in EVENT_POLICIES)


def _sweep(bot, pending: list[str]) -> set[str]:
    """Mở Event Center một lần, duyệt danh sách; event nào mở được thì tự đánh dấu xong (xem ``_finish_event``)."""
    if open_event_center(bot) is None:
        bot.record("Gift Claims: không mở được Event Center; chưa tính là không thấy")
        return set()
    run_opened(bot, set())
    return_home(bot)
    return set(pending)


def run(bot) -> bool:
    """Chạy hoạt động Event Center; True khi mọi event con đã xong hôm nay."""
    return scan.run_zone(bot, KEY, TASKS, _sweep)
