"""Standalone helpers that enter flows by fixed inner-screen names."""
from .common import return_home, select_carousel_tab, tap_claims
from .lobby import open_named


def run_carousel_claim(bot, screen_name, page: str, tab: str,
                       claims: tuple[str, ...]) -> bool:
    if not open_named(bot, screen_name):
        return False
    if not select_carousel_tab(bot, page, tab):
        return_home(bot)
        return False
    tap_claims(bot, claims)
    return_home(bot)
    return True
