"""Claim the Claimable chest on the Empire Depot tab."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_empire_depot"


def run(bot):
    return run_carousel_claim(bot, GiftScreen.SUPER_VALUE_RETURN,
                              "SuperValueReturn/title",
                              "EmpireDepot/tab", ("EmpireDepot/button_claimable",))


TASK = GiftTask(KEY, "Empire Depot", run)
