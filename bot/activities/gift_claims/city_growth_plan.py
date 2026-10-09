"""Claim unlocked free rewards in City Growth Plan Stage 1."""
from .common import (GiftTask, claim_fixed_controls, close_congratulations,
                     find, find_all, return_home, select_carousel_tab)
from .lobby import open_named
from .screens import GiftScreen

KEY = "gift_city_growth_plan"


def claim_opened(bot):
    """Try Claim All, then sweep the free left reward column by level."""
    fixed = claim_fixed_controls(bot, ("CityGrowthPlan/button_claim_all",),
                                 initial_wait_attempts=2)
    claimed = fixed.claimed
    # Some variants have no Claim All. The free Rewards column is on the left;
    # Advanced Rewards on the right is paid/locked and is never touched.
    for page in range(6):
        bot.check()
        screen = bot.screenshot()
        claimed_rows = find_all(bot, "CityGrowthPlan/claimed", screen,
                                threshold=0.70, region=(20, 45, 50, 98))
        for y in (58, 67, 76, 85, 94):
            pixel_y = int(screen.shape[0] * y / 100)
            if any(abs(check_y - pixel_y) <= 28 for _, check_y in claimed_rows):
                continue
            bot.tap_percent(31, y, delay=0.7)
            after = bot.screenshot()
            if close_congratulations(bot):
                claimed = True
            elif find(bot, "CityGrowthPlan/detail_popup", bot.screenshot(), threshold=0.82,
                    region=(80, 15, 100, 30)) is not None:
                bot.back(delay=0.7)
            else:
                checks = find_all(bot, "CityGrowthPlan/claimed", after,
                                  threshold=0.70, region=(20, 45, 50, 98))
                claimed = claimed or any(abs(check_y - pixel_y) <= 28
                                         for _, check_y in checks)
        if page < 5:
            before_scroll = bot.screenshot()
            bot.swipe_percent(50, 89, 50, 53, duration=0.5, delay=1)
            after_scroll = bot.screenshot()
            if float(abs(before_scroll.astype("int16")
                         - after_scroll.astype("int16")).mean()) < 0.5:
                break
    return claimed


def run(bot):
    if (not open_named(bot, GiftScreen.SUPER_VALUE_RETURN)
            or not select_carousel_tab(bot, "SuperValueReturn/title",
                                       "CityGrowthPlan/tab")):
        return False
    claimed = claim_opened(bot)
    return_home(bot)
    return claimed


TASK = GiftTask(KEY, "City Growth Plan Stage 1", run)
