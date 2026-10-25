"""Hypnos' Dream: open its exact Rewards control before claims."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Hypnos' Dream",
    key="gift_hypnos_dream",
    screen=GiftScreen.HYPNOS_DREAM,
    navigation=("Rewards", "EventCenter/HypnosDream/button_rewards_text"),
)


def run(bot):
    return run_opened_event(bot, POLICY)
