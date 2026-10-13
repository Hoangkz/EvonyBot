"""Claim glowing/unlocked rewards in the free Login Gifts column."""
from .common import GiftTask, find, find_all, return_home, select_carousel_tab
from .lobby import open_named
from .screens import GiftScreen

KEY = "gift_login_gifts"
PAGE = "LoginGifts/title"
CONGRATULATIONS = "LoginGifts/congratulations"
GLOWING_TREASURE_BOX = "LoginGifts/reward_glowing_treasure_box"


def _tap_reward(bot, pos) -> bool:
    """Tap one free reward and verify whether Congratulations appeared."""
    bot.tap(*pos, delay=1)
    for attempt in range(3):
        screen = bot.screenshot()
        if find(bot, CONGRATULATIONS, screen, threshold=0.78,
                region=(0, 38, 100, 62)) is not None:
            bot.record("Gift Claims: Login Gifts nhận được quà (Congratulations)")
            bot.back(delay=0.8)
            return True
        if find(bot, "LoginGifts/detail_popup", screen, threshold=0.82,
                region=(0, 20, 100, 40)) is not None:
            bot.back(delay=0.7)
            return False
        if attempt < 2:
            bot.sleep(0.4)
    return False


def claim_opened(bot):
    """Claim the free column after the Login Gifts tab is already open."""
    # Left reward column is free; locked premium rewards are in the right column.
    opened = False
    claimed = 0
    for page in range(2):
        failed_positions = []
        for _ in range(12):
            screen = bot.screenshot()
            if find(bot, PAGE, screen, threshold=0.70,
                    region=(0, 15, 45, 25)) is None:
                break
            opened = True
            positions = find_all(bot, GLOWING_TREASURE_BOX, screen,
                                 threshold=0.72, region=(20, 38, 48, 98))
            pos = next((candidate for candidate in positions
                        if all((candidate[0] - old[0]) ** 2 +
                               (candidate[1] - old[1]) ** 2 > 30 ** 2
                               for old in failed_positions)), None)
            if pos is None:
                break
            if _tap_reward(bot, pos):
                claimed += 1
            else:
                # Never probe the other rows blindly: a non-claimable chest
                # can open item detail or a purchase view.
                failed_positions.append(pos)
        if page == 0:
            bot.swipe_percent(50, 89, 50, 55, duration=0.5, delay=1)
    if opened and claimed == 0:
        bot.log("Gift Claims: Login Gifts đã kiểm tra, chưa có phần thưởng sáng nhận được")
    return claimed


def run(bot):
    if (not open_named(bot, GiftScreen.SUPER_VALUE_RETURN)
            or not select_carousel_tab(bot, "SuperValueReturn/title", "LoginGifts/tab")):
        return False
    claim_opened(bot)
    return_home(bot)
    return True


TASK = GiftTask(KEY, "Login Gifts", run)
