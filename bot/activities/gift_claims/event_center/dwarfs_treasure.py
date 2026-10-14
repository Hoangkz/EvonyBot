"""Dwarf's Treasure: use the captured Daily Free chest control."""
from ..screens import GiftScreen
from .policy import EventPolicy


POLICY = EventPolicy(
    "Dwarf's Treasure",
    screen=GiftScreen.DWARFS_TREASURE,
    navigation=("Daily Free", "DwarfsTreasure/button_daily_free"),
)
