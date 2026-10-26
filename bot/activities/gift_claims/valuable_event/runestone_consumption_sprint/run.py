"""Claim the free package in Runestone Consumption Sprint."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_runestone_consumption_sprint"
FLOW = ExactFlow(
    navigation=("ValuableEvent/RunestoneConsumptionSprint/subtab_sprint_package",),
    claims=("ValuableEvent/RunestoneConsumptionSprint/button_free",),
    done=("ValuableEvent/RunestoneConsumptionSprint/sold_out",),
    congratulations_done=True,
)


def run(bot):
    return run_carousel_exact(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "ValuableEvent/RunestoneConsumptionSprint/tab",
        FLOW,
    )


TASK = GiftTask(KEY, "Runestone Consumption Sprint", run)
