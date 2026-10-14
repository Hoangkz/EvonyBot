"""Per-event policies used by the Event Center red-dot scanner."""
from dataclasses import dataclass

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
