"""Claim the free chest in Super Blazon Sale."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_super_blazon_sale"


def run(bot):
    return run_carousel_claim(bot, GiftScreen.VALUABLE_EVENT, "ValuableEvent/title",
                              "SuperBlazonSale/tab", ("SuperBlazonSale/button_free",))


TASK = GiftTask(KEY, "Super Blazon Sale", run)
