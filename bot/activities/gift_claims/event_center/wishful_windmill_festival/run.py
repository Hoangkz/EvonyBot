"""Wishful Windmill Festival two-part exact reward contract."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Wishful Windmill Festival",
    key="gift_wishful_windmill_festival",
    screen=GiftScreen.WISHFUL_WINDMILL_FESTIVAL,
)


def run(bot):
    return run_opened_event(bot, POLICY)
