"""Claim the red-dot reward on the rotating Dragon Battle page."""
from ...common import (GiftTask, claim_fixed_controls, open_event_center_event,
                     return_home)
from ...screens import GiftScreen
from ..policy import EventPolicy

KEY = "gift_dragon_battle"
POLICY = EventPolicy("Dragon Battle", key=KEY, screen=GiftScreen.DRAGON_BATTLE)


def run(bot):
    if not open_event_center_event(bot, "DragonBattle/list_row", "DragonBattle/title"):
        return False
    claim_fixed_controls(bot, ("DragonBattle/reward",))
    return_home(bot)
    return True


TASK = GiftTask(KEY, "Dragon Battle", run)
