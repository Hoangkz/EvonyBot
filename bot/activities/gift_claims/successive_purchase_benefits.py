"""Open Daily Free and claim any free daily package shown afterward."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_successive_purchase_benefits"


def run(bot):
    return run_carousel_claim(
        bot, GiftScreen.VALUABLE_EVENT, "ValuableEvent/title",
        "SuccessivePurchaseBenefits/tab",
        ("SuccessivePurchaseBenefits/button_daily_free", "LimitedOffer/button_free"))


TASK = GiftTask(KEY, "Successive Purchase Benefits", run)
