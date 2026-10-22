"""Dwarf's Lucky Apple policy in Event Center > Activities."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event

KEY = "gift_dwarfs_lucky_apple"
POLICY = EventPolicy(
    "Dwarf's Lucky Apple",
    key=KEY,
    screen=GiftScreen.DWARFS_LUCKY_APPLE,
)


def run(bot):
    return run_opened_event(bot, POLICY)
