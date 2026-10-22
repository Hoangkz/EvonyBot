"""Claim the free package in Runestone Consumption Sprint."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_runestone_consumption_sprint"
FLOW = ExactFlow(
    navigation=("RunestoneConsumptionSprint/subtab_sprint_package",),
    claims=("RunestoneConsumptionSprint/button_free",),
    done=("RunestoneConsumptionSprint/sold_out",),
    congratulations_done=True,
)


def run(bot):
    return run_carousel_exact(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "RunestoneConsumptionSprint/tab",
        FLOW,
    )


TASK = GiftTask(KEY, "Runestone Consumption Sprint", run)
