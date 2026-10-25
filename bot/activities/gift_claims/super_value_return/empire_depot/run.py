"""Claim the Claimable chest on the Empire Depot tab."""
from ...common import GiftTask
from ...valuable_event.named_flow import run_carousel_claim
from ...screens import GiftScreen

KEY = "gift_empire_depot"


def run(bot):
    return run_carousel_claim(bot, GiftScreen.SUPER_VALUE_RETURN,
                              "SuperValueReturn/title",
                              "SuperValueReturn/EmpireDepot/tab", ("Common/button_claimable",
                                                   "Common/button_claimable_alt",
                                                   "SuperValueReturn/EmpireDepot/button_claimable"))


TASK = GiftTask(KEY, "Empire Depot", run)
