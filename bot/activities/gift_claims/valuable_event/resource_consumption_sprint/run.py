"""Open Sprint Package and claim the Resource Consumption free package."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_resource_consumption_sprint"
FLOW = ExactFlow(
    navigation=("ResourceConsumptionSprint/subtab_sprint_package",),
    claims=("ResourceConsumptionSprint/button_free_current",
            "ResourceConsumptionSprint/button_free"),
    done=("ResourceConsumptionSprint/sold_out",),
    congratulations_done=True,
)


def run(bot):
    return run_carousel_exact(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "ResourceConsumptionSprint/tab",
        FLOW,
    )


TASK = GiftTask(KEY, "Resource Consumption Sprint", run)
