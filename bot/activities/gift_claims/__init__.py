"""One resumable, low-priority DB-first task for every post-daily gift flow.

Every named reward location has a durable child key.  ``KEY`` is written only
after all locations in both outer zones have a current server-day checkpoint.
"""
from dataclasses import dataclass, field
from importlib import import_module

from ...context.errors import YieldToBoss
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
LABEL = "Nhận toàn bộ quà sau Daily Activities"


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


def run(bot) -> bool:
    """Inspect every DB-pending reward location, in its two fixed zones.

    This is deliberately DB-first.  A red marker can disappear before a free
    chest becomes visible, so it is not an execution queue and never writes a
    DONE timestamp.  Every individual flow must return true only after it has
    reached and inspected its named screen; :class:`GiftTask` then writes its
    own key.  ``bot.check()`` keeps the normal two-minute/Boss yielding
    contract between locations.
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

    for zone in (registry.VALUABLE_EVENT, registry.EVENT_CENTER):
        for location in registry.pending(bot, zone):
            bot.check()
            bot.record(f"Gift Claims: kiểm tra DB-pending {location.task.label}")
            inspected = location.task.run(bot)
            if not inspected:
                bot.record(f"Gift Claims: chưa tới/kiểm tra xong "
                           f"{location.task.label}; giữ PENDING")

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


__all__ = ["KEY", "LABEL", "GiftProgress", "run"]
