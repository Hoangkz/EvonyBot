"""Per-event policies used by the Event Center red-dot scanner."""
from dataclasses import dataclass
from importlib import import_module

from ..screens import GiftScreen


@dataclass(frozen=True)
class EventPolicy:
    """A named Event Center event and its safe reward contract.

    ``screen`` is intentionally optional: Pallas and Poseidon's Day are still
    processed by the generic red-row scanner, but we do not claim to identify
    them by name until a stable title crop is captured.
    """

    label: str
    screen: GiftScreen | None = None
    navigation: tuple[str, str] | None = None
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
    if policy.skip_reason is not None:
        bot.record(f"Gift Claims: {policy.label} - {policy.skip_reason}")
        return scanner.ClaimReport()
    report, _ = scanner._process_current_event_content(bot)
    return report
