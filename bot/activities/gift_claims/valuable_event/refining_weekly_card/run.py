"""Claim every free row in Refining Weekly Card."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_refining_weekly_card"
FLOW = ExactFlow(
    claims=("RefiningWeeklyCard/button_claim",),
    done=("RefiningWeeklyCard/button_go", "RefiningWeeklyCard/button_continue"),
    scroll_claims=True,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.SUPER_VALUE_RETURN,
                              "SuperValueReturn/title", "RefiningWeeklyCard/tab", FLOW)


TASK = GiftTask(KEY, "Refining Weekly Card", run)
