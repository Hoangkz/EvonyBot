"""Open Sprint Package and claim its verified Free package."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_refining_stone_sprint"


def run(bot):
    return run_carousel_claim(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "RefiningStoneSprint/tab",
        ("SpeedupSprint/button_free",),
        navigation=("SpeedupSprint/subtab_package",),
    )


TASK = GiftTask(KEY, "Refining Stone Sprint", run)
