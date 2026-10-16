"""Poseidon's Day: open Ocean Offering, then collect Daily Free."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Poseidon's Day",
    key="gift_poseidons_day",
    screen=GiftScreen.POSEIDONS_DAY,
    navigation=("Daily Free", "PoseidonsDay/button_daily_free"),
    navigation_entry=("PoseidonsDay/tab_ocean_offering",),
)


def run(bot):
    return run_opened_event(bot, POLICY)
