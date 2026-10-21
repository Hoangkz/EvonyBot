"""Claim General Vault Daily Free; only Congratulations is terminal."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_general_vault"
FLOW = ExactFlow(
    claims=("GeneralVault/button_daily_free_current",
            "GeneralVault/button_daily_free"),
    congratulations_done=True,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "GeneralVault/tab", FLOW)


TASK = GiftTask(KEY, "General Vault", run)
