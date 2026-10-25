"""Claim the current Dragon Battle button and verify Congratulations."""
from ...common import (GiftTask, close_congratulations, find,
                       open_event_center_event)
from ...screens import GiftScreen
from ..policy import EventPolicy

KEY = "gift_dragon_battle"
POLICY = EventPolicy("Dragon Battle", key=KEY, screen=GiftScreen.DRAGON_BATTLE)


def run(bot):
    if not open_event_center_event(bot, "DragonBattle/list_row", "DragonBattle/title"):
        return False
    button = None
    for attempt in range(4):
        button = find(bot, "DragonBattle/button_claim_015225", bot.screenshot(),
                      threshold=0.80, region=(0, 15, 100, 95))
        if button is not None:
            break
        if attempt < 3:
            bot.sleep(1.5)
    if button is None:
        bot.record("Gift Claims: Dragon Battle không còn nút "
                   "Screenshot_20261026-015225; DONE")
        bot.back(delay=1.5)
        return True
    bot.record("Gift Claims: Dragon Battle tap nút "
               "Screenshot_20261026-015225")
    bot.tap(*button, delay=1.5)
    done = close_congratulations(bot, attempts=5)
    if done:
        bot.record("Gift Claims: Dragon Battle đã hiện Congratulations; DONE")
    if done:
        # Chỉ sau khi chốt DONE mới rời trang Dragon để chọn nhiệm vụ kế tiếp.
        bot.back(delay=1.5)
    else:
        bot.record("Gift Claims: Dragon Battle đã bấm nhưng chưa thấy "
                   "Congratulations; giữ PENDING")
    return done


TASK = GiftTask(KEY, "Dragon Battle", run)
