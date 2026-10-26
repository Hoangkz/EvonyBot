"""Claim Daily Free and require the captured opened chest terminal state."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_successive_purchase_benefits"
FLOW = ExactFlow(
    claims=("ValuableEvent/SuccessivePurchaseBenefits/button_daily_free_current",
            "ValuableEvent/SuccessivePurchaseBenefits/button_daily_free_text",
            "ValuableEvent/SuccessivePurchaseBenefits/button_daily_free",
            "ValuableEvent/LimitedOffer/button_free"),
    done=("ValuableEvent/SuccessivePurchaseBenefits/chest_open",),
)


def run(bot):
    return run_carousel_exact(
        bot, GiftScreen.VALUABLE_EVENT, "ValuableEvent/title",
        "ValuableEvent/SuccessivePurchaseBenefits/tab_icon", FLOW)


TASK = GiftTask(KEY, "Successive Purchase Benefits", run)
