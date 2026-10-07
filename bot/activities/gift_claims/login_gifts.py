"""Claim every currently visible unlocked free Login Gifts row."""
from .common import GiftTask, find, return_home, select_carousel_tab
from .lobby import open_named
from .screens import GiftScreen

KEY = "gift_login_gifts"
PAGE = "LoginGifts/title"


def claim_opened(bot):
    """Claim the free column after the Login Gifts tab is already open."""
    # Left reward column is free; locked premium rewards are in the right column.
    opened = False
    for page in range(2):
        screen = bot.screenshot()
        if find(bot, PAGE, screen, threshold=0.70, region=(0, 15, 45, 25)) is None:
            break
        opened = True
        # Include the sixth/bottom row: its sparkling chest is around 92% on
        # the supplied 396x704 layout. Tapping claimed rows is safe; only the
        # recognized item-detail popup is closed.
        for y in (49, 59, 69, 79, 89, 92):
            bot.tap_percent(34, y, delay=0.7)
            screen = bot.screenshot()
            if find(bot, "LoginGifts/detail_popup", screen, threshold=0.82,
                    region=(0, 20, 100, 36)) is not None:
                bot.back(delay=0.7)
        if page == 0:
            bot.swipe_percent(50, 89, 50, 55, duration=0.5, delay=1)
    return opened


def run(bot):
    if (not open_named(bot, GiftScreen.SUPER_VALUE_RETURN)
            or not select_carousel_tab(bot, "SuperValueReturn/title", "LoginGifts/tab")):
        return False
    claim_opened(bot)
    return_home(bot)
    return True


TASK = GiftTask(KEY, "Login Gifts", run)
