"""Claim General Vault Daily Free; only Congratulations is terminal."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_general_vault"
FLOW = ExactFlow(
    claims=("ValuableEvent/GeneralVault/button_daily_free_current",
            "ValuableEvent/GeneralVault/button_daily_free"),
    congratulations_done=True,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ValuableEvent/GeneralVault/tab_icon", FLOW)


TASK = GiftTask(KEY, "General Vault", run)
