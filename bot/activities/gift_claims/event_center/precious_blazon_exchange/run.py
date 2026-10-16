"""Precious Blazon Exchange: open its exact Rewards control before claims."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Precious Blazon Exchange",
    key="gift_precious_blazon_exchange",
    screen=GiftScreen.PRECIOUS_BLAZON_EXCHANGE,
    navigation=("Rewards", "PreciousBlazonExchange/button_rewards"),
)


def run(bot):
    return run_opened_event(bot, POLICY)
