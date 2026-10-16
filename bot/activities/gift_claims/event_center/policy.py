"""Per-event policies used by the Event Center red-dot scanner."""
from dataclasses import dataclass
from importlib import import_module

from ..screens import GiftScreen


@dataclass(frozen=True)
class EventPolicy:
    """A named Event Center event and its safe reward contract.

    ``screen`` is intentionally optional: Pallas is still processed by the
    generic red-row scanner, but we do not claim to identify it by name until
    a stable title crop is captured.
    """

    label: str
    key: str | None = None
    screen: GiftScreen | None = None
    navigation: tuple[str, str] | None = None
    navigation_entry: tuple[str, ...] = ()
    reward_navigation: tuple[str, ...] = ()
    skip_reason: str | None = None


def run_opened_event(bot, policy: EventPolicy):
    """Run one policy after its Event Center page is already open.

    Navigation and scheduling deliberately remain outside this function.  It
    lets every event package expose a small ``run(bot)`` entry point now while
    preserving the current red-dot scanner as the sole caller until a later
    scheduler design is chosen.
    """
    scanner = import_module(f"{__package__}.run")
    # A policy is never allowed to mark its own DB key merely because the
    # Event Center happens to be open.  The caller must have reached the exact
    # named page first.  Pallas intentionally remains pending until a stable
    # page-title crop is available; guessing its list row
    # would violate the no-blind-tap safety contract.
    if policy.screen is None:
        bot.log(f"Gift Claims: {policy.label} chưa có tiêu đề cố định; giữ PENDING")
        return False
    if scanner.identify(bot) != policy.screen:
        bot.log(f"Gift Claims: chưa vào đúng {policy.label}; giữ PENDING")
        return False
    if policy.skip_reason is not None:
        bot.record(f"Gift Claims: {policy.label} - {policy.skip_reason}")
        if policy.key is not None:
            scanner.mark_task_done(bot, policy.key)
        return True
    scanner._process_known_event(bot, policy)
    return True
