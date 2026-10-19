"""Giant's Wisdom Temple exact reward contract."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Giant's Wisdom Temple",
    key="gift_giants_wisdom_temple",
    screen=GiftScreen.GIANTS_WISDOM_TEMPLE,
)


def run(bot):
    return run_opened_event(bot, POLICY)
