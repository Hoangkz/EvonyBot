"""Standalone helpers that enter flows by fixed inner-screen names."""
from .common import (TEXT_CLAIM_CONTROLS, claim_fixed_controls, return_home,
                     select_carousel_tab, tap_claims)
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
    # `claims` is kept as page metadata, but a generic tap is only driven by
    # the tight common text crops. This makes the matched centre the real word
    # inside the button instead of the centre of a chest/panel screenshot.
    report = claim_fixed_controls(bot, TEXT_CLAIM_CONTROLS,
                                  max_taps=16) if claims else None
    if report is not None:
        bot.log(f"Gift Claims: fixed claims {report.verified}/{report.attempted} verified")
    return_home(bot)
    return True
