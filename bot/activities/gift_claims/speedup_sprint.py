"""Claim the free Sprint Package in Valuable Event."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_speedup_sprint"


def run(bot):
    return run_carousel_claim(bot, GiftScreen.VALUABLE_EVENT, "ValuableEvent/title",
                              "SpeedupSprint/tab",
                              ("SpeedupSprint/subtab_package",
                               "SpeedupSprint/button_free"))


TASK = GiftTask(KEY, "Speedup Sprint", run)
