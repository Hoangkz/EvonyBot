"""Open Sprint Package and claim the Resource Consumption free package."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import run_carousel_claim

KEY = "gift_resource_consumption_sprint"


def run(bot):
    return run_carousel_claim(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "ResourceConsumptionSprint/tab",
        ("ResourceConsumptionSprint/button_free",),
        navigation=("SpeedupSprint/subtab_package",),
    )


TASK = GiftTask(KEY, "Resource Consumption Sprint", run)
