"""Poseidon's Day: open Ocean Offering, then collect Daily Free."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Poseidon's Day",
    key="gift_poseidons_day",
    screen=GiftScreen.POSEIDONS_DAY,
    navigation=("Daily Free", "EventCenter/PoseidonsDay/button_daily_free_text"),
    navigation_entry=("EventCenter/PoseidonsDay/tab_packages_red_dot",),
)


def run(bot):
    return run_opened_event(bot, POLICY)
