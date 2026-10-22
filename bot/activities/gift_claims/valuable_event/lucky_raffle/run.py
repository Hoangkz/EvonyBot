"""Claim the free Lucky Raffle chest and verify its opened state."""
from ...common import GiftTask
from ..named_flow import ExactFlow, run_carousel_exact
from ...screens import GiftScreen

KEY = "gift_lucky_raffle"
FLOW = ExactFlow(
    claims=("LuckyRaffle/button_claimable_current",),
    done=("LuckyRaffle/chest_open",),
    congratulations_done=True,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.SUPER_VALUE_RETURN,
                              "SuperValueReturn/title", "LuckyRaffle/tab",
                              FLOW)


TASK = GiftTask(KEY, "Lucky Raffle", run)
