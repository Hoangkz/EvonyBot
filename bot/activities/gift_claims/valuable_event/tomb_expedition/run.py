"""Claim the Limited Rewards chest in Tomb Expedition."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_tomb_expedition"
FLOW = ExactFlow(
    opened=("ValuableEvent/TombExpedition/limited_rewards_header",),
    claims=("ValuableEvent/TombExpedition/button_rewards",),
    done=("ValuableEvent/TombExpedition/quests_done",),
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ValuableEvent/TombExpedition/tab", FLOW)


TASK = GiftTask(KEY, "Tomb Expedition", run)
