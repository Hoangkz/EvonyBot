"""One resumable, low-priority DB-first task for every post-daily gift flow.

Every named reward location has a durable child key.  ``KEY`` is written only
after all locations in both outer zones have a current server-day checkpoint.
"""
from dataclasses import dataclass, field
from functools import wraps
from importlib import import_module

from . import event_center, lobby, registry, valuable_event
# Compatibility aliases for callers that previously imported a specific
# non-Event-Center claim flow from ``gift_claims``.  Implementations live in
# ``valuable_event/``; only the public entry points remain here.
back_to_territory = import_module(f"{__name__}.valuable_event.back_to_territory.run")
empire_depot = import_module(f"{__name__}.valuable_event.empire_depot.run")
limited_offer = import_module(f"{__name__}.valuable_event.limited_offer.run")
login_gifts = import_module(f"{__name__}.valuable_event.login_gifts.run")
super_value_return = import_module(f"{__name__}.valuable_event.super_value_return.run")
from .common import (TEXT_CLAIM_CONTROLS, back_if_close_x,
                     claim_fixed_controls, claim_sparkles, return_home)
from .screens import GiftScreen

KEY = "gift_claims"
LABEL = "Nhận toàn bộ quà"


def _without_join_boss_interrupt(func):
    """Keep one gift run intact while preserving Stop/reset safety checks."""
    @wraps(func)
    def wrapped(bot, *args, **kwargs):
        missing = object()
        saved_boss = getattr(bot, "_boss_interrupt_enabled", missing)
        saved_deadline = getattr(bot, "_deadline", missing)
        if saved_boss is not missing:
            bot._boss_interrupt_enabled = False
        if saved_deadline is not missing:
            bot._deadline = None
        try:
            return func(bot, *args, **kwargs)
        finally:
            if saved_boss is not missing:
                bot._boss_interrupt_enabled = saved_boss
            if saved_deadline is not missing:
                bot._deadline = saved_deadline
    return wrapped


@dataclass
class GiftProgress:
    boundary_index: int = 0
    attempted: dict[str, list[tuple[int, int]]] = field(
        default_factory=lambda: {name: [] for name in lobby.BOUNDARIES}
    )
    valuable_done: set[str] = field(default_factory=set)
    super_value_done: set[str] = field(default_factory=set)
    completed_parents: set[GiftScreen] = field(default_factory=set)
    unresolved_parents: set[GiftScreen] = field(default_factory=set)
    seen_parents: set[GiftScreen] = field(default_factory=set)
    back_to_territory_done: set[bytes] = field(default_factory=set)
    event_center_done: set[bytes] = field(default_factory=set)
    outcomes: list[str] = field(default_factory=list)


def _progress(bot) -> GiftProgress:
    progress = getattr(bot, "_gift_claims_progress", None)
    if not isinstance(progress, GiftProgress):
        progress = GiftProgress()
        # Child keys are durable checkpoints.  They survive a Boss yield or
        # worker restart, while the combined ``gift_claims`` key is still
        # withheld until both outer zones are completely clean.
        progress.valuable_done.update(
            key for key in valuable_event.KEYS if bot.is_daily_done(key))
        progress.super_value_done.update(
            key for key in super_value_return.KEYS if bot.is_daily_done(key))
        bot._gift_claims_progress = progress
    return progress


def _dispatch(bot, screen_name: GiftScreen, progress: GiftProgress):
    """Handle whichever fixed screen the clicked lobby dot actually opened."""
    if screen_name == GiftScreen.VALUABLE_EVENT:
        if screen_name not in progress.completed_parents:
            outcomes, scanned = valuable_event._run.run_opened(
                bot, valuable_event.KEYS - progress.valuable_done,
                handled=progress.valuable_done,
            )
            progress.outcomes.extend(outcomes.values())
            if scanned:
                progress.completed_parents.add(screen_name)
                progress.unresolved_parents.discard(screen_name)
            else:
                progress.unresolved_parents.add(screen_name)
                bot.record("Gift Claims: Valuable Event còn dấu đỏ; vẫn quét tiếp vùng còn lại")
        else:
            return_home(bot)
        return

    if screen_name == GiftScreen.SUPER_VALUE_RETURN:
        if screen_name not in progress.completed_parents:
            outcomes, scanned = super_value_return.run_opened(
                bot, super_value_return.KEYS - progress.super_value_done,
                handled=progress.super_value_done,
            )
            progress.outcomes.extend(outcomes.values())
            if scanned:
                progress.completed_parents.add(screen_name)
                progress.unresolved_parents.discard(screen_name)
            else:
                progress.unresolved_parents.add(screen_name)
                bot.record("Gift Claims: Super Value Return còn dấu đỏ; vẫn quét tiếp vùng còn lại")
        else:
            return_home(bot)
        return

    if screen_name == GiftScreen.EVENT_CENTER:
        clean = event_center._run.run_opened(bot, progress.event_center_done)
        progress.outcomes.append("event_center_clean" if clean else
                                 "event_center_remaining")
        if clean:
            progress.unresolved_parents.discard(screen_name)
        else:
            progress.unresolved_parents.add(screen_name)
        return

    if screen_name == GiftScreen.BACK_TO_TERRITORY:
        clean = back_to_territory.run_opened(bot, progress.back_to_territory_done)
        progress.outcomes.append("back_to_territory_clean" if clean else
                                 "back_to_territory_remaining")
        if clean:
            progress.unresolved_parents.discard(screen_name)
        else:
            progress.unresolved_parents.add(screen_name)
        return_home(bot)
        return

    if screen_name == GiftScreen.FOLLOW_US:
        bot.record("Gift Claims: Follow Us - bỏ qua Go/Not Achieved, không có quà miễn phí")
        progress.outcomes.append("follow_us_skipped")
        return_home(bot)
        return

    if screen_name in (GiftScreen.REVELATION_OF_HORUS,
                        GiftScreen.SEALED_IMPERIAL_TREASURY):
        bot.record(f"Gift Claims: {screen_name.value} - bỏ qua và coi là DONE")
        progress.outcomes.append(f"skipped:{screen_name.value}")
        progress.unresolved_parents.discard(screen_name)
        return_home(bot)
        return

    # Rotating timer icons do not have a stable captured title. They still use
    # the same safe lower-area contract: exact reward words first, then four
    # bounded sparkle samples. A persistent purchase badge must not block the
    # whole daily task after those checks have been exhausted.
    fixed = claim_fixed_controls(bot, TEXT_CLAIM_CONTROLS, max_taps=16,
                                 region=(0, 18, 100, 88))
    if not back_if_close_x(bot):
        sparkle = claim_sparkles(bot, region=(5, 18, 90, 82), attempts=4)
    else:
        sparkle = None
    verified = fixed.verified + (sparkle.verified if sparkle is not None else 0)
    progress.outcomes.append(f"unidentified_checked:{verified}")
    bot.record("Gift Claims: màn xoay vòng chưa có tiêu đề cố định đã được "
               "kiểm tra nút chữ và sparkle đủ 4 lần; đánh dấu bỏ qua nếu "
               "không có kết quả nhận")
    progress.unresolved_parents.discard(GiftScreen.UNKNOWN)
    return_home(bot)


@_without_join_boss_interrupt
def run_region(bot, region: str) -> bool:
    """Run every DB-pending gift location in exactly one user-defined region."""
    if region not in (registry.REGION_1, registry.REGION_2):
        raise ValueError(f"unknown gift region: {region}")
    label = "Vùng 1 (ngoài Event Center)" if region == registry.REGION_1 else \
            "Vùng 2 (Event Center)"
    bot.record(f"Gift Claims: bắt đầu {label}")
    pending_now = registry.pending(bot, region)
    known_region_1 = {task.key for task in registry.REGION_1_TASKS}
    if (region == registry.REGION_1
            and all(item.task.key in known_region_1 for item in pending_now)):
        return _run_region_1(bot, label)
    for location in pending_now:
        bot.check()
        bot.record(f"Gift Claims: {label} kiểm tra {location.task.label}")
        inspected = location.task.run(bot)
        if not inspected:
            bot.record(f"Gift Claims: chưa tới/kiểm tra xong "
                       f"{location.task.label}; giữ PENDING")
    remaining = registry.pending(bot, region)
    if remaining:
        bot.record(f"Gift Claims: {label} còn PENDING: " +
                   ", ".join(item.task.label for item in remaining))
        return False
    bot.record(f"Gift Claims: {label} DONE")
    return True


def _finish_clean_parent(bot, tasks, due_keys, parent_label: str) -> None:
    """A fully scanned carousel with no red tab completes its remaining keys."""
    for task in tasks:
        if task.key in due_keys:
            from .common import mark_task_done
            mark_task_done(bot, task.key)
    bot.record(f"Gift Claims: {parent_label} hết tab đỏ; coi toàn bộ nhóm DONE")


def _run_region_1(bot, label: str) -> bool:
    """Run region 1 parent-by-parent instead of reopening every child tab."""
    valuable_due = {
        item.task.key for item in registry.pending(bot, registry.REGION_1)
        if item.task in registry.VALUABLE_EVENT_TASKS
    }
    if valuable_due:
        if lobby.open_named(bot, GiftScreen.VALUABLE_EVENT):
            _, clean = valuable_event.run_opened(bot, valuable_due, handled=set())
            if clean:
                _finish_clean_parent(
                    bot, registry.VALUABLE_EVENT_TASKS, valuable_due,
                    "Valuable Event")
        else:
            bot.record("Gift Claims: chưa mở được Valuable Event; giữ nhóm PENDING")

    super_due = {
        item.task.key for item in registry.pending(bot, registry.REGION_1)
        if item.task in registry.SUPER_VALUE_RETURN_TASKS
    }
    if super_due:
        if lobby.open_named(bot, GiftScreen.SUPER_VALUE_RETURN):
            _, clean = super_value_return.run_opened(bot, super_due, handled=set())
            if clean:
                _finish_clean_parent(
                    bot, registry.SUPER_VALUE_RETURN_TASKS, super_due,
                    "Super Value Return")
        else:
            bot.record("Gift Claims: chưa mở được Super Value Return; giữ nhóm PENDING")

    remaining = registry.pending(bot, registry.REGION_1)
    if remaining:
        bot.record(f"Gift Claims: {label} còn PENDING: " +
                   ", ".join(item.task.label for item in remaining))
        return False
    bot.record(f"Gift Claims: {label} DONE")
    return True


@_without_join_boss_interrupt
def run(bot) -> bool:
    """Run region 1 then region 2 with durable child checkpoints.

    Region 1 is grouped by parent carousel. A complete two-direction scan with
    no red tab completes that parent's remaining children instead of reopening
    each DB-pending tab. Region 2 keeps its Event Center inspection rules.
    """
    # ``gift_claims`` is deliberately only an aggregate scheduler checkpoint.
    # Every named location is authoritative: an old aggregate record must not
    # suppress a newly introduced/missing child location on the same server
    # day.  This is also what makes the next run after reset inspect each
    # location again even if the city currently displays no red badge.
    if registry.complete(bot):
        if not bot.is_daily_done(KEY):
            bot.mark_daily_done(KEY)
        return True
    if bot.is_daily_done(KEY):
        bot.record("Gift Claims: aggregate DONE cũ nhưng còn điểm nhận chưa "
                   "kiểm tra; bỏ qua aggregate và tiếp tục theo DB con")

    run_region(bot, registry.REGION_1)
    run_region(bot, registry.REGION_2)

    # A clean red-badge scan is not evidence that every named gift location
    # was inspected.  Each child flow writes its own key after opening the
    # page; only those keys may complete the aggregate task.
    if not registry.complete(bot):
        pending = ", ".join(item.task.label for item in registry.pending(bot))
        bot.record("Gift Claims: còn PENDING theo DB (không suy từ chấm đỏ): "
                   + pending)
        return False

    bot.mark_daily_done(KEY)
    bot.record("Gift Claims: HOÀN THÀNH; mọi key khu Valuable Event và "
               "Event Center đều current sau reset server")
    if hasattr(bot, "_gift_claims_progress"):
        delattr(bot, "_gift_claims_progress")
    return True


__all__ = ["KEY", "LABEL", "GiftProgress", "run_region", "run"]
