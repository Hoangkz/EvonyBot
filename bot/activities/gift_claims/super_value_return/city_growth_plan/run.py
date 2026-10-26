"""Claim image-identified free rewards in City Growth Plan Stage 1."""
from ...common import (GiftTask, claim_fixed_controls, return_home,
                       select_carousel_tab)
from ...lobby import open_named
from ...screens import GiftScreen

KEY = "gift_city_growth_plan"


def claim_opened(bot):
    """Use only recognised claim controls; never probe fixed row positions."""
    fixed = claim_fixed_controls(bot, ("Common/button_claim_all_text",),
                                 initial_wait_attempts=2)
    return fixed.claimed


def run(bot):
    if (not open_named(bot, GiftScreen.SUPER_VALUE_RETURN)
            or not select_carousel_tab(bot, "SuperValueReturn/title",
                                       "SuperValueReturn/CityGrowthPlan/tab")):
        return False
    claimed = claim_opened(bot)
    return_home(bot)
    return claimed


TASK = GiftTask(KEY, "City Growth Plan Stage 1", run)
