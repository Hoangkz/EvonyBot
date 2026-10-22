"""Claim the free chest in Optional Package."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_optional_package"
FLOW = ExactFlow(
    claims=("OptionalPackage/button_claimable",),
    done=("OptionalPackage/chest_open",),
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "OptionalPackage/tab", FLOW)


TASK = GiftTask(KEY, "Optional Package", run)
