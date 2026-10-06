"""Claim the red-dot reward on the rotating Dragon Battle page."""
from .common import GiftTask, open_event_center_event, return_home, tap_claims

KEY = "gift_dragon_battle"


def run(bot):
    if not open_event_center_event(bot, "DragonBattle/list_row", "DragonBattle/title"):
        return False
    tap_claims(bot, ("DragonBattle/reward",))
    return_home(bot)
    return True


TASK = GiftTask(KEY, "Dragon Battle", run)
