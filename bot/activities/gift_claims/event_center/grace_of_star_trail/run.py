"""Claim the highlighted cumulative reward on Grace of Star Trail."""
from ...common import GiftTask, open_event_center_event, return_home
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event

KEY = "gift_grace_of_star_trail"
POLICY = EventPolicy(
    "Grace of Star Trail",
    key=KEY,
    screen=GiftScreen.GRACE_OF_STAR_TRAIL,
    reward_navigation=(
        "EventCenter/GraceOfStarTrail/button_star_trail_gift_current",
        "EventCenter/GraceOfStarTrail/button_star_trail_gift_alt",
        "EventCenter/GraceOfStarTrail/button_star_trail_gift",
    ),
)


def run(bot):
    if not open_event_center_event(bot, "EventCenter/GraceOfStarTrail/list_row",
                                   "EventCenter/GraceOfStarTrail/title"):
        return False
    # Reuse the same two-pass Star Trail Gift -> coin Claim contract as the
    # Event Center list scanner so standalone execution cannot checkpoint a
    # weaker flow.
    completed = run_opened_event(bot, POLICY)
    return_home(bot)
    return completed


TASK = GiftTask(KEY, "Grace of Star Trail", run)
