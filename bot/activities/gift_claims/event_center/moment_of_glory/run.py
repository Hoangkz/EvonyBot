"""Moment of Glory policy in Event Center > Limited."""

from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event

KEY = "gift_moment_of_glory"
POLICY = EventPolicy(
    "Moment of Glory",
    key=KEY,
    screen=GiftScreen.MOMENT_OF_GLORY,
)


def run(bot):
    return run_opened_event(bot, POLICY)
