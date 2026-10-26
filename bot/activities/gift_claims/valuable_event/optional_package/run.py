"""Claim the free chest in Optional Package."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_optional_package"
FLOW = ExactFlow(
    claims=("ValuableEvent/OptionalPackage/button_claimable",),
    done=("ValuableEvent/OptionalPackage/chest_open",),
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ValuableEvent/OptionalPackage/tab_icon", FLOW)


TASK = GiftTask(KEY, "Optional Package", run)
