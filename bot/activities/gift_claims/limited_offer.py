"""Claim the free Daily Package on Valuable Event / Limited Offer."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_limited_offer"


def run(bot):
    return run_carousel_claim(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "LimitedOffer/tab",
                              ("LimitedOffer/button_free",))


TASK = GiftTask(KEY, "Limited Offer", run)
