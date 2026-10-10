"""One resumable, low-priority task for every post-daily gift flow.

Only ``KEY`` is persisted. The per-screen modules are implementation details:
their progress lives on ``BotContext`` while the worker yields to Join Boss and
is discarded after the whole two-boundary scan completes.
"""
from dataclasses import dataclass, field

from ...context.errors import YieldToBoss
from . import back_to_territory, event_center, lobby, super_value_return, valuable_event
from .common import return_home
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
        bot._gift_claims_progress = progress
    return progress


def _dispatch(bot, screen_name: GiftScreen, progress: GiftProgress):
    """Handle whichever fixed screen the clicked lobby dot actually opened."""
    if screen_name == GiftScreen.VALUABLE_EVENT:
        if screen_name not in progress.completed_parents:
            outcomes, scanned = valuable_event.run_opened(
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
        clean = event_center.run_opened(bot, progress.event_center_done)
        progress.outcomes.append("event_center_clean" if clean else
                                 "event_center_remaining")
        if clean:
            progress.unresolved_parents.discard(screen_name)
        else:
            progress.unresolved_parents.add(screen_name)
            progress.event_center_done.clear()
        return

    if screen_name == GiftScreen.BACK_TO_TERRITORY:
        clean = back_to_territory.run_opened(bot, progress.back_to_territory_done)
        progress.outcomes.append("back_to_territory_clean" if clean else
                                 "back_to_territory_remaining")
        if clean:
            progress.unresolved_parents.discard(screen_name)
        else:
            progress.unresolved_parents.add(screen_name)
            progress.back_to_territory_done.clear()
        return_home(bot)
        return

    if screen_name == GiftScreen.FOLLOW_US:
        bot.record("Gift Claims: Follow Us - bỏ qua Go/Not Achieved, không có quà miễn phí")
        progress.outcomes.append("follow_us_skipped")
        return_home(bot)
        return

    # Some right-rail dots perform an immediate lobby action and have no title
    # (Back to Territory, Follow Us, rotating timer icons...). They were still
    # clicked exactly once in this pass; record them as an unverified outcome.
    progress.outcomes.append(f"unidentified:{screen_name.value}")
    bot.record(f"Gift Claims: đã bấm dấu đỏ nhưng không nhận diện được {screen_name.value}")
    progress.unresolved_parents.add(GiftScreen.UNKNOWN)
    return_home(bot)


def run(bot) -> bool:
    """Resume both boundaries and persist only after the whole scan finishes.

    A timeout/boss exception may interrupt any device action. The last outer
    dot is rolled back, while completed inner tabs stay in memory, so the next
    two-minute slice resumes safely rather than repeating the entire scan.
    """
    if bot.is_daily_done(KEY):
        return True

    progress = _progress(bot)
    # Unknown means the clicked lobby marker opened no captured title. Many of
    # those badges clear merely by being opened. Retry it on the next full
    # pass, but do not carry a stale Unknown blocker forever after the marker
    # has disappeared from the lobby.
    if (progress.boundary_index == 0
            and all(not points for points in progress.attempted.values())):
        progress.unresolved_parents.discard(GiftScreen.UNKNOWN)
    while progress.boundary_index < len(lobby.BOUNDARIES):
        boundary = lobby.BOUNDARIES[progress.boundary_index]
        attempted = progress.attempted[boundary]
        bot.check()
        before = len(attempted)
        try:
            screen_name = lobby.open_next(bot, boundary, attempted)
            if screen_name is None:
                progress.boundary_index += 1
                continue
            progress.seen_parents.add(screen_name)
            _dispatch(bot, screen_name, progress)
        except Exception:
            # open_next can itself time out after appending/tapping a dot, so
            # rollback covers both navigation and the opened child flow.
            if len(attempted) > before:
                attempted.pop()
            raise

    # A parent may remove its lobby badge on the final successful tap just as
    # the two-minute slice expires. A complete two-boundary rescan is the
    # authoritative verification: if that parent was not seen again, its old
    # unresolved marker is stale and must not block the combined DB task.
    vanished = progress.unresolved_parents - progress.seen_parents
    for screen_name in vanished:
        progress.unresolved_parents.discard(screen_name)
        progress.outcomes.append(f"cleared_on_lobby_recheck:{screen_name.value}")
        bot.record(f"Gift Claims: {screen_name.value} đã hết dấu đỏ khi quét lại hai vùng")

    if progress.unresolved_parents:
        names = ", ".join(sorted(item.value for item in progress.unresolved_parents))
        bot.record(f"Gift Claims: chưa DONE ({names} còn đỏ); nhường Boss rồi quét lại")
        progress.boundary_index = 0
        progress.attempted = {name: [] for name in lobby.BOUNDARIES}
        progress.seen_parents.clear()
        raise YieldToBoss

    bot.mark_daily_done(KEY)
    verified = sum(1 for item in progress.outcomes
                   if not item.startswith("unidentified:"))
    unknown = sum(1 for item in progress.outcomes
                  if item.startswith("unidentified:"))
    bot.record(f"Gift Claims: HOÀN THÀNH một task chung; "
               f"{verified} luồng đã kiểm tra, {unknown} dấu đỏ không có màn cố định")
    delattr(bot, "_gift_claims_progress")
    return True


__all__ = ["KEY", "LABEL", "GiftProgress", "run"]
