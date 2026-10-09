"""Redeem every affordable Stockpile chest through its confirmation popup."""
from .common import (GiftTask, claim_fixed_controls, find, return_home,
                     select_carousel_tab, tap_claims)
from .lobby import open_named
from .screens import GiftScreen

KEY = "gift_strategic_stockpile"
SUBTAB = "StrategicStockpile/subtab_stockpile"
REDEEM = "StrategicStockpile/button_redeem"
CONFIRM = "StrategicStockpile/button_confirm_redeem"


def claim_opened(bot) -> int:
    """Repeat Redeem -> ticket confirmation -> verified reward."""
    tap_claims(bot, (SUBTAB,), max_taps=1, initial_wait_attempts=2,
               region=(0, 20, 100, 88))
    claimed = 0
    for _ in range(6):
        bot.check()
        screen = bot.screenshot()
        redeem = find(bot, REDEEM, screen, threshold=0.76,
                      region=(0, 20, 100, 95))
        if redeem is None:
            break
        bot.record("Gift Claims: Strategic Stockpile mở Redeem bằng vé")
        bot.tap(*redeem, delay=1)
        report = claim_fixed_controls(
            bot, (CONFIRM,), max_taps=1, initial_wait_attempts=1,
            region=(20, 45, 80, 78))
        if not report.claimed:
            bot.log("Gift Claims: Strategic Stockpile chưa xác minh được Redeem")
            break
        claimed += report.verified
        bot.sleep(1)
    return claimed


def run(bot):
    if (not open_named(bot, GiftScreen.VALUABLE_EVENT)
            or not select_carousel_tab(bot, "ValuableEvent/title",
                                       "StrategicStockpile/tab")):
        return False
    claim_opened(bot)
    return_home(bot)
    return True


TASK = GiftTask(KEY, "Strategic Stockpile", run)
