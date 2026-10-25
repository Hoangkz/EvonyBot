"""Claim the exact Dragon Battle chest and verify either terminal state."""
from ...common import (GiftTask, close_congratulations, find,
                       open_event_center_event)
from ...screens import GiftScreen
from ..policy import EventPolicy

KEY = "gift_dragon_battle"
POLICY = EventPolicy("Dragon Battle", key=KEY, screen=GiftScreen.DRAGON_BATTLE)


def run(bot):
    if not open_event_center_event(bot, "EventCenter/DragonBattle/list_row", "EventCenter/DragonBattle/title"):
        return False
    for attempt in range(2):
        claimed = find(bot, "EventCenter/DragonBattle/status_reward_claimed", bot.screenshot(),
                       threshold=0.82, region=(0, 15, 100, 95))
        if claimed is not None:
            bot.record("Gift Claims: Dragon Battle đã thấy rương trạng thái "
                       "Screenshot_20261025-012404; DONE")
            bot.back(delay=1.5)
            return True
        if attempt == 0:
            bot.sleep(1.5)
    reward = None
    for attempt in range(4):
        reward = find(bot, "EventCenter/DragonBattle/reward_230317", bot.screenshot(),
                      threshold=0.80, region=(0, 15, 100, 95))
        if reward is not None:
            break
        if attempt < 3:
            bot.sleep(1.5)
    if reward is None:
        bot.record("Gift Claims: Dragon Battle không thấy rương "
                   "Screenshot_20261023-230317; giữ PENDING")
        bot.back(delay=1.5)
        return False
    bot.record("Gift Claims: Dragon Battle tap rương "
               "Screenshot_20261023-230317")
    bot.tap(*reward, delay=1.5)
    done = close_congratulations(bot, attempts=5)
    if done:
        bot.record("Gift Claims: Dragon Battle đã hiện Congratulations; DONE")
    else:
        for attempt in range(3):
            claimed = find(bot, "EventCenter/DragonBattle/status_reward_claimed", bot.screenshot(),
                           threshold=0.82, region=(0, 15, 100, 95))
            if claimed is not None:
                done = True
                bot.record("Gift Claims: Dragon Battle rương đã đổi sang trạng thái "
                           "Screenshot_20261025-012404; DONE")
                break
            if attempt < 2:
                bot.sleep(1.5)
    if done:
        # Chỉ sau khi chốt DONE mới rời trang Dragon để chọn nhiệm vụ kế tiếp.
        bot.back(delay=1.5)
    else:
        bot.record("Gift Claims: Dragon Battle chưa thấy Congratulations/rương "
                   "đã nhận; giữ PENDING")
    return done


TASK = GiftTask(KEY, "Dragon Battle", run)
