"""Hoạt động Event Center: các event con trong danh sách Limited của Event Center."""
from .. import back_to_territory, scan
from ..common import mark_task_done, open_event_center, return_home
from ..screens import GiftScreen, identify
from .run import (EVENT_POLICIES, POLICY_CATEGORIES, SCAN_COMPLETE_ATTR,
                  SCANNED_CATEGORIES_ATTR, SEEN_POLICIES_ATTR,
                  PENDING_THIS_RUN_ATTR, clear_resume_category, run_opened)

KEY = "gift_event_center"
HANDLED_ATTR = "_gift_claims_event_center_handled"
TASKS = ((back_to_territory.KEY, back_to_territory.TASK.label),
         *((policy.key, policy.label) for policy in EVENT_POLICIES))


def _limited_miss_keys(key: str) -> list[str]:
    """Durable absence checkpoints owned only by Event Center/Limited."""
    return [f"{key}_miss_done_{index}"
            for index in range(1, scan.MAX_MISSES + 1)]


def _limited_misses(bot, key: str) -> int:
    return sum(bot.is_daily_done(miss_key)
               for miss_key in _limited_miss_keys(key))


def _add_limited_miss(bot, key: str) -> int:
    count = min(_limited_misses(bot, key) + 1, scan.MAX_MISSES)
    bot.mark_daily_done(_limited_miss_keys(key)[count - 1])
    return count


def _reset_limited_misses(bot, key: str) -> None:
    for miss_key in _limited_miss_keys(key):
        if bot.done_at(miss_key) is not None:
            bot.forget_daily(miss_key)


def _handled(bot) -> set[bytes]:
    """Rows already scanned in the current worker, retained across Boss yields."""
    handled = getattr(bot, HANDLED_ATTR, None)
    if not isinstance(handled, set):
        handled = set()
        setattr(bot, HANDLED_ATTR, handled)
    return handled


def _checkpoint_categories(bot, pending: list[str]) -> None:
    """Persist each completed category pass before a later 120 s interruption.

    ``run_opened`` updates ``SCANNED_CATEGORIES_ATTR`` immediately after a
    category reaches its verified edge.  Reading it in ``finally`` means a
    completed Limited pass still writes one ``miss_done_*`` checkpoint even
    if Activities is then interrupted.  Activities never uses this absence
    rule. Seen Limited rows reset old absence counters; only unseen rows accrue
    exactly one durable miss in this 120-second window.
    """
    scanned = getattr(bot, SCANNED_CATEGORIES_ATTR, set())
    seen = getattr(bot, SEEN_POLICIES_ATTR, set())
    if not isinstance(scanned, set) or not isinstance(seen, set):
        return
    labels = dict(TASKS)
    for key in pending:
        if key == back_to_territory.KEY:
            continue
        category = POLICY_CATEGORIES.get(key, "limited")
        if category != "limited":
            continue
        if category not in scanned:
            continue
        if bot.is_daily_done(key) or key in seen:
            _reset_limited_misses(bot, key)
            continue
        label = labels.get(key, key)
        attempt = min(_limited_misses(bot, key) + 1, scan.MAX_MISSES)
        bot.record(f"Gift Claims: kiểm tra {label} không xuất hiện "
                   f"(lượt {attempt}/{scan.MAX_MISSES})")
        count = _add_limited_miss(bot, key)
        bot.record(f"Gift Claims: không thấy {label} "
                   f"(miss_done_{count}/{scan.MAX_MISSES})")
        if count >= scan.MAX_MISSES:
            bot.record(f"Gift Claims: {label} không có hôm nay; đánh dấu xong")
            mark_task_done(bot, key)


def _sweep(bot, pending: list[str]) -> set[str]:
    """Mở Event Center một lần, duyệt danh sách; event nào mở được thì tự đánh dấu xong (xem ``_finish_event``)."""
    inspected: set[str] = set()
    if back_to_territory.KEY in pending:
        # Icon ngoài Event Center được tìm bằng ảnh/tên; không mở ra trang của
        # nó = hôm nay không có.
        back_to_territory.TASK.run(bot)
        inspected.add(back_to_territory.KEY)
    # Stay inside Event Center while this 120-second window checks Limited and
    # Activities. Each completed category pass is checkpointed immediately.
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
    completed_call = False
    try:
        run_opened(bot, handled)
        completed_call = True
    finally:
        # Persist a completed Limited/Activities pass even when the following
        # category is cut off by the worker's 120-second deadline.
        _checkpoint_categories(bot, pending)
    scanned_categories = getattr(bot, SCANNED_CATEGORIES_ATTR, set())
    scan_complete = bool(scanned_categories)
    # A complete top-to-bottom pass may leave a policy pending only when its
    # own exact completion contract failed.  Clear row checkpoints so the next
    # pass can deliberately retry that event.  If BotInterrupted is raised,
    # this line is never reached and the mutated set survives the 120 s yield.
    if scan_complete and completed_call:
        handled.clear()
    # ``run_opened`` writes DONE for both exhausted events and events absent
    # from a complete Limited scan.  A key still pending afterwards was seen
    # but failed its own completion contract; do not count that as a
    # "not found" miss or the third pass would incorrectly close it.
    return inspected | {key for key in pending if bot.is_daily_done(key)}


def run(bot) -> bool:
    """Chạy hoạt động Event Center; True khi mọi event con đã xong hôm nay."""
    setattr(bot, PENDING_THIS_RUN_ATTR, set())
    # One durable 1/3 pass per 120-second eligibility window. Category misses
    # are checkpointed inside _sweep, including before a later interruption.
    try:
        done = scan.run_zone(bot, KEY, TASKS, _sweep, max_sweeps=1)
    finally:
        if hasattr(bot, PENDING_THIS_RUN_ATTR):
            delattr(bot, PENDING_THIS_RUN_ATTR)
    return_home(bot)
    if done and hasattr(bot, HANDLED_ATTR):
        delattr(bot, HANDLED_ATTR)
    if done:
        clear_resume_category(bot)
    return done
