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
        screen = bot.screenshot()
        if find(bot, PAGE, screen, threshold=0.70, region=(0, 15, 45, 25)) is None:
            break
        opened = True
        # Prioritize the exact sparkling Treasure Box supplied by the user.
        # Then probe every free-column row: future/claimed rows only open the
        # known detail popup, while a claimable glow produces Congratulations.
        tried_y = []
        for pos in find_all(bot, GLOWING_TREASURE_BOX, screen, threshold=0.72,
                            region=(20, 38, 48, 98)):
            tried_y.append(pos[1])
            claimed += int(_tap_reward(bot, pos))

        # Include the sixth/bottom row: its sparkling chest is around 92% on
        # the supplied 396x704 layout.
        for y in (49, 59, 69, 79, 89, 92):
            pixel_y = round(bot.screenshot().shape[0] * y / 100)
            if any(abs(pixel_y - old_y) <= 25 for old_y in tried_y):
                continue
            screen = bot.screenshot()
            claimed += int(_tap_reward(bot, (round(screen.shape[1] * 0.34), pixel_y)))
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
