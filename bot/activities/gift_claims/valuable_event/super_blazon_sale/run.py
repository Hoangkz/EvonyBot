"""Claim the free chest in Super Blazon Sale."""
from ...common import GiftTask
from ..named_flow import ExactFlow, run_carousel_exact
from ...screens import GiftScreen

KEY = "gift_super_blazon_sale"
FLOW = ExactFlow(
    claims=("SuperBlazonSale/button_free_current",
            "SuperBlazonSale/button_free"),
    done=("SuperBlazonSale/chest_open",),
    # If button_free is absent in the reward panel, the free gift is complete.
    absence_done=True,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "SuperBlazonSale/tab", FLOW)


TASK = GiftTask(KEY, "Super Blazon Sale", run)
