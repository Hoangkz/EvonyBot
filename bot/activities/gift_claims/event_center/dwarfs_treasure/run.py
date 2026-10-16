"""Dwarf's Treasure: use the captured Daily Free chest control."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Dwarf's Treasure",
    key="gift_dwarfs_treasure",
    screen=GiftScreen.DWARFS_TREASURE,
    navigation=("Daily Free", "DwarfsTreasure/button_daily_free"),
)


def run(bot):
    return run_opened_event(bot, POLICY)
