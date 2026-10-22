"""Claim Daily Free and require the captured opened chest terminal state."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_successive_purchase_benefits"
FLOW = ExactFlow(
    claims=("SuccessivePurchaseBenefits/button_daily_free_current",
            "SuccessivePurchaseBenefits/button_daily_free_text",
            "SuccessivePurchaseBenefits/button_daily_free",
            "LimitedOffer/button_free"),
    done=("SuccessivePurchaseBenefits/chest_open",),
)


def run(bot):
    return run_carousel_exact(
        bot, GiftScreen.VALUABLE_EVENT, "ValuableEvent/title",
        "SuccessivePurchaseBenefits/tab", FLOW)


TASK = GiftTask(KEY, "Successive Purchase Benefits", run)
