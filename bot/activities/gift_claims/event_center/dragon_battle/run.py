"""Claim the exact Dragon Battle chest and require Congratulations."""
from ...common import (GiftTask, close_congratulations, find,
                       open_event_center_event, return_home)
from ...screens import GiftScreen
from ..policy import EventPolicy

KEY = "gift_dragon_battle"
POLICY = EventPolicy("Dragon Battle", key=KEY, screen=GiftScreen.DRAGON_BATTLE)


def run(bot):
    if not open_event_center_event(bot, "DragonBattle/list_row", "DragonBattle/title"):
        return False
    reward = None
    for attempt in range(4):
        reward = find(bot, "DragonBattle/reward_230317", bot.screenshot(),
                      threshold=0.80, region=(0, 15, 100, 95))
        if reward is not None:
            break
        if attempt < 3:
            bot.sleep(1.5)
    if reward is None:
        bot.record("Gift Claims: Dragon Battle không thấy rương "
                   "Screenshot_20261023-230317; giữ PENDING")
        return_home(bot)
        return False
    bot.record("Gift Claims: Dragon Battle tap rương "
               "Screenshot_20261023-230317")
    bot.tap(*reward, delay=1.5)
    done = close_congratulations(bot, attempts=5)
    if done:
        bot.record("Gift Claims: Dragon Battle đã hiện Congratulations; DONE")
    else:
        bot.record("Gift Claims: Dragon Battle chưa thấy Congratulations; "
                   "giữ PENDING")
    return_home(bot)
    return done


TASK = GiftTask(KEY, "Dragon Battle", run)
