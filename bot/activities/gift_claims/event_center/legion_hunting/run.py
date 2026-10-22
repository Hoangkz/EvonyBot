"""Legion Hunting policy in Event Center > Limited."""

from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event

KEY = "gift_legion_hunting"
POLICY = EventPolicy(
    "Legion Hunting",
    key=KEY,
    screen=GiftScreen.LEGION_HUNTING,
)


def run(bot):
    return run_opened_event(bot, POLICY)
