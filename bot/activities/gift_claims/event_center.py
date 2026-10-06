"""Claim safe free controls from red-dot rows on Event Center / Limited.

The first Invite Friends/Facebook row is intentionally skipped. Activities is
also intentionally not opened, matching the supplied flow notes.
"""
from .common import GiftTask, find, find_all, open_event_center, return_home, tap_claims

KEY = "gift_event_center_limited"
MAX_EVENTS = 8


def run(bot):
    screen = open_event_center(bot)
    if screen is None:
        return False
    return run_opened(bot)


def run_opened(bot):
    """Process red-dot Limited rows after Event Center is already open."""
    screen = bot.screenshot()
    if find(bot, "EventCenter/title", screen, threshold=0.72,
            region=(0, 0, 100, 13)) is None:
        return_home(bot)
        return False

    visited_rows = []
    for _ in range(MAX_EVENTS):
        screen = bot.screenshot()
        # Limited rows start below Invite Friends. Dot is on the left icon;
        # tapping the middle of that row avoids the icon carousel edge.
        dots = [
            dot for dot in find_all(bot, "EventCenter/notification_dot", screen,
                                    threshold=0.65, region=(10, 25, 25, 98))
            if dot[1] >= 205 and all(abs(dot[1] - old_y) > 24 for old_y in visited_rows)
        ]
        if not dots:
            break
        _, y = dots[0]
        visited_rows.append(y)
        bot.tap_percent(52, y * 100 / screen.shape[0], delay=2)
        opened = bot.screenshot()
        if find(bot, "BacchusTavern/title", opened, threshold=0.72,
                region=(0, 0, 100, 13)) is not None:
            bot.log("Gift Claims: Bacchus Tavern - bỏ qua theo cấu hình")
            bot.back(delay=2)
            continue
        tap_claims(bot, ("SpeedupSprint/button_free", "SuperBlazonSale/button_free",
                         "SuccessivePurchaseBenefits/button_daily_free",
                         "LimitedOffer/button_free", "EmpireDepot/button_claimable",
                         "LuckyRaffle/button_claimable", "CityGrowthPlan/button_claim_all"),
                   max_taps=4)
        bot.back(delay=2)
    bot.log(f"Gift Claims: Event Center checked {len(visited_rows)} unique Limited event(s)")
    return_home(bot)
    return True


TASK = GiftTask(KEY, "Event Center Limited", run)
