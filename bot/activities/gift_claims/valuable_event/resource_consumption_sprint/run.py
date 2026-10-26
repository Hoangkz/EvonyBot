"""Open Sprint Package and claim the Resource Consumption free package."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_resource_consumption_sprint"
FLOW = ExactFlow(
    navigation=("ValuableEvent/ResourceConsumptionSprint/subtab_sprint_package",),
    claims=("ValuableEvent/ResourceConsumptionSprint/button_free_current",
            "ValuableEvent/ResourceConsumptionSprint/button_free"),
    done=("ValuableEvent/ResourceConsumptionSprint/sold_out",),
    congratulations_done=True,
)


def run(bot):
    return run_carousel_exact(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "ValuableEvent/ResourceConsumptionSprint/tab",
        FLOW,
    )


TASK = GiftTask(KEY, "Resource Consumption Sprint", run)
