"""Claim the Dragon Battle reward chest and verify a terminal state."""
from ...common import (ClaimReport, GiftTask, close_congratulations, find,
                       open_event_center_event)
from ...screens import GiftScreen
from ..policy import EventPolicy

KEY = "gift_dragon_battle"
POLICY = EventPolicy("Dragon Battle", key=KEY, screen=GiftScreen.DRAGON_BATTLE)
REWARD_REGION = (80, 20, 100, 40)
ACTIVE_REWARDS = (
    ("EventCenter/DragonBattle/reward", 0.80),
    ("EventCenter/DragonBattle/reward_230317", 0.72),
)
CLAIMED_REWARD = "EventCenter/DragonBattle/status_reward_claimed"
CLAIMED_THRESHOLD = 0.76
WAIT_ATTEMPTS = 4
RESULT_ATTEMPTS = 6
STEP_DELAY = 1.5
CONGRATULATIONS_REGION = (0, 20, 100, 38)


def _find_reward_chest(bot, screen):
    """Find either captured active Dragon Battle chest in its safe region."""
    for template, threshold in ACTIVE_REWARDS:
        position = find(bot, template, screen, threshold=threshold,
                        region=REWARD_REGION)
        if position is not None:
            return position
    return None


def _reward_claimed(bot, screen) -> bool:
    """Recognize the supplied opened/claimed chest terminal state."""
    return find(bot, CLAIMED_REWARD, screen, threshold=CLAIMED_THRESHOLD,
                region=REWARD_REGION) is not None


def claim_opened(bot) -> tuple[ClaimReport, bool]:
    """Claim the chest; DONE requires opened chest or Congratulations."""
    chest = None
    for attempt in range(WAIT_ATTEMPTS):
        bot.check()
        screen = bot.screenshot()
        if _reward_claimed(bot, screen):
            bot.record("Gift Claims: Dragon Battle thấy rương đã mở; DONE")
            return ClaimReport(0, 1), True
        chest = _find_reward_chest(bot, screen)
        if chest is not None:
            break
        if attempt + 1 < WAIT_ATTEMPTS:
            bot.sleep(STEP_DELAY)

    if chest is None:
        bot.record("Gift Claims: Dragon Battle chưa thấy rương nhận quà hoặc "
                   "rương đã mở; giữ PENDING")
        return ClaimReport(), False

    bot.record(f"Gift Claims: Dragon Battle thấy rương nhận quà tại {chest}; tap")
    bot.tap(*chest, delay=STEP_DELAY)
    for attempt in range(RESULT_ATTEMPTS):
        bot.check()
        if close_congratulations(bot, attempts=1,
                                 region=CONGRATULATIONS_REGION):
            bot.record("Gift Claims: Dragon Battle đã hiện Congratulations; DONE")
            return ClaimReport(1, 1), True
        if _reward_claimed(bot, bot.screenshot()):
            bot.record("Gift Claims: Dragon Battle rương đã chuyển sang mở; DONE")
            return ClaimReport(1, 1), True
        if attempt + 1 < RESULT_ATTEMPTS:
            bot.sleep(1)

    bot.record("Gift Claims: Dragon Battle đã bấm rương nhưng chưa thấy "
               "Congratulations hoặc rương mở; giữ PENDING")
    return ClaimReport(1, 0), False


def run(bot):
    if not open_event_center_event(bot, "EventCenter/DragonBattle/list_row", "EventCenter/DragonBattle/title"):
        return False
    _report, done = claim_opened(bot)
    if done:
        # Chỉ sau khi chốt DONE mới rời trang Dragon để chọn nhiệm vụ kế tiếp.
        bot.back(delay=STEP_DELAY)
    return done


TASK = GiftTask(KEY, "Dragon Battle", run)
