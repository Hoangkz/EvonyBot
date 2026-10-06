"""Claim the free Claimable chest on Lucky Raffle."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_lucky_raffle"


def run(bot):
    return run_carousel_claim(bot, GiftScreen.SUPER_VALUE_RETURN,
                              "SuperValueReturn/title",
                              "LuckyRaffle/tab", ("LuckyRaffle/button_claimable",))


TASK = GiftTask(KEY, "Lucky Raffle", run)
