"""Precious Blazon Exchange: open its exact Rewards control before claims."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Precious Blazon Exchange",
    screen=GiftScreen.PRECIOUS_BLAZON_EXCHANGE,
    navigation=("Rewards", "PreciousBlazonExchange/button_rewards"),
)


def run(bot):
    return run_opened_event(bot, POLICY)
