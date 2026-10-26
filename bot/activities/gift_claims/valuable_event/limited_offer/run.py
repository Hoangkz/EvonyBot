"""Claim the free Daily Package on Valuable Event / Limited Offer."""
from ...common import GiftTask
from ..named_flow import ExactFlow, run_carousel_exact
from ...screens import GiftScreen

KEY = "gift_limited_offer"
FLOW = ExactFlow(
    claims=("ValuableEvent/LimitedOffer/button_free_current", "ValuableEvent/LimitedOffer/button_free"),
    # The reward area is authoritative: no Free after two checks means DONE.
    absence_done=True,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ValuableEvent/LimitedOffer/tab_icon", FLOW)


TASK = GiftTask(KEY, "Limited Offer", run)
