"""Standalone helpers that enter flows by fixed inner-screen names."""
from .common import (claim_fixed_controls, return_home, select_carousel_tab,
                     tap_claims)
from .lobby import open_named


def run_carousel_claim(bot, screen_name, page: str, tab: str,
                       claims: tuple[str, ...], *,
                       navigation: tuple[str, ...] = ()) -> bool:
    if not open_named(bot, screen_name):
        return False
    if not select_carousel_tab(bot, page, tab):
        return_home(bot)
        return False
    if navigation:
        tap_claims(bot, navigation, max_taps=len(navigation),
                   initial_wait_attempts=2)
    report = claim_fixed_controls(bot, claims) if claims else None
    if report is not None:
        bot.log(f"Gift Claims: fixed claims {report.verified}/{report.attempted} verified")
    return_home(bot)
    return True
