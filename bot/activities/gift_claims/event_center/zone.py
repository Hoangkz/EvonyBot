"""Hoạt động Event Center: các event con trong danh sách Limited của Event Center."""
from .. import back_to_territory, scan
from ..common import open_event_center, return_home
from ..screens import GiftScreen, identify
from .run import (EVENT_POLICIES, POLICY_CATEGORIES, SCAN_COMPLETE_ATTR,
                  SCANNED_CATEGORIES_ATTR, SEEN_POLICIES_ATTR,
                  PENDING_THIS_RUN_ATTR, run_opened)

KEY = "gift_event_center"
HANDLED_ATTR = "_gift_claims_event_center_handled"
TASKS = ((back_to_territory.KEY, back_to_territory.TASK.label),
         *((policy.key, policy.label) for policy in EVENT_POLICIES))


def _handled(bot) -> set[bytes]:
    """Rows already scanned in the current worker, retained across Boss yields."""
    handled = getattr(bot, HANDLED_ATTR, None)
    if not isinstance(handled, set):
        handled = set()
        setattr(bot, HANDLED_ATTR, handled)
    return handled


def _sweep(bot, pending: list[str]) -> set[str]:
    """Mở Event Center một lần, duyệt danh sách; event nào mở được thì tự đánh dấu xong (xem ``_finish_event``)."""
    inspected: set[str] = set()
    if back_to_territory.KEY in pending:
        # Icon ngoài Event Center được tìm bằng ảnh/tên; không mở ra trang của
        # nó = hôm nay không có.
        back_to_territory.TASK.run(bot)
        inspected.add(back_to_territory.KEY)
    # scan.run_zone may perform three Limited checks followed by three
    # Activities checks. Stay inside Event Center between those sweeps instead
    # of returning home and reopening the same page every time.
    current = (identify(bot, bot.screenshot())
               if hasattr(bot, "screenshot") else None)
    if current != GiftScreen.EVENT_CENTER:
        if open_event_center(bot) is None:
            bot.record("Gift Claims: không mở được Event Center; chưa tính là không thấy")
            return inspected
    handled = _handled(bot)
    if not handled:
        setattr(bot, SEEN_POLICIES_ATTR, set())
    setattr(bot, SCAN_COMPLETE_ATTR, False)
    setattr(bot, SCANNED_CATEGORIES_ATTR, set())
    run_opened(bot, handled)
    scanned_categories = getattr(bot, SCANNED_CATEGORIES_ATTR, set())
    scan_complete = bool(scanned_categories)
    # A complete top-to-bottom pass may leave a policy pending only when its
    # own exact completion contract failed.  Clear row checkpoints so the next
    # pass can deliberately retry that event.  If BotInterrupted is raised,
    # this line is never reached and the mutated set survives the 120 s yield.
    if scan_complete:
        handled.clear()
        seen = getattr(bot, SEEN_POLICIES_ATTR, set())
        # A complete list scan proves only that an unseen rotating event is
        # absent in this pass.  Let scan.run_zone persist miss 1/2/3 and mark
        # it DONE only after the third full pass.  A visible but unfinished
        # event stays out of inspected, so it remains PENDING and is retried.
        inspected.update(
            key for key in pending
            if key != back_to_territory.KEY
            and POLICY_CATEGORIES.get(key, "limited") in scanned_categories
            and key not in seen
            and not bot.is_daily_done(key)
        )
    # ``run_opened`` writes DONE for both exhausted events and events absent
    # from a complete Limited scan.  A key still pending afterwards was seen
    # but failed its own completion contract; do not count that as a
    # "not found" miss or the third pass would incorrectly close it.
    return inspected | {key for key in pending if bot.is_daily_done(key)}


def run(bot) -> bool:
    """Chạy hoạt động Event Center; True khi mọi event con đã xong hôm nay."""
    setattr(bot, PENDING_THIS_RUN_ATTR, set())
    # Two independently verified categories: up to three complete Limited
    # passes, then up to three Activities passes, all in the same opened page.
    try:
        done = scan.run_zone(bot, KEY, TASKS, _sweep,
                             max_sweeps=scan.MAX_MISSES * 2)
    finally:
        if hasattr(bot, PENDING_THIS_RUN_ATTR):
            delattr(bot, PENDING_THIS_RUN_ATTR)
    return_home(bot)
    if done and hasattr(bot, HANDLED_ATTR):
        delattr(bot, HANDLED_ATTR)
    return done
