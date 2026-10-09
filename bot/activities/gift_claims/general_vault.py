"""Claim the fixed Daily Free chest on Valuable Event / General Vault."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_general_vault"


def run(bot):
    return run_carousel_claim(
        bot, GiftScreen.VALUABLE_EVENT, "ValuableEvent/title",
        "GeneralVault/tab", ("GeneralVault/button_daily_free",),
    )


TASK = GiftTask(KEY, "General Vault", run)
