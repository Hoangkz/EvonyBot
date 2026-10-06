"""Scan every known red-dot tab during one Valuable Event session."""
from dataclasses import dataclass

from . import (
    limited_offer,
    speedup_sprint,
    successive_purchase_benefits,
    sulis_wishing,
    super_blazon_sale,
    super_value_weekly_card,
)
from .common import find, find_all, return_home, tap_claims

PAGE = "ValuableEvent/title"
DOT = "ValuableEvent/notification_dot"
MAX_SWIPES = 8


@dataclass(frozen=True)
class ValuableSpec:
    task: object
    tab: str
    claims: tuple[str, ...] = ()


SPECS = (
    ValuableSpec(limited_offer.TASK, "LimitedOffer/tab", ("LimitedOffer/button_free",)),
    ValuableSpec(speedup_sprint.TASK, "SpeedupSprint/tab",
                 ("SpeedupSprint/subtab_package", "SpeedupSprint/button_free")),
    ValuableSpec(super_blazon_sale.TASK, "SuperBlazonSale/tab",
                 ("SuperBlazonSale/button_free",)),
    ValuableSpec(sulis_wishing.TASK, "SulisWishing/tab"),
    ValuableSpec(super_value_weekly_card.TASK, "SuperValueWeeklyCard/tab",
                 ("SuperValueWeeklyCard/button_scores",)),
    ValuableSpec(successive_purchase_benefits.TASK, "SuccessivePurchaseBenefits/tab",
                 ("SuccessivePurchaseBenefits/button_daily_free",
                  "LimitedOffer/button_free")),
)


def _near_tab(dot, tab) -> bool:
    return abs(dot[0] - tab[0]) <= 55 and abs(dot[1] - tab[1]) <= 40


def _dots(bot, screen):
    return find_all(bot, DOT, screen, threshold=0.65, region=(0, 7, 100, 18))


def _verify_clean(bot) -> bool:
    """Verify that no red tab remains anywhere in the parent carousel."""
    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            if _dots(bot, bot.screenshot()):
                return False
            if step < MAX_SWIPES:
                if direction < 0:
                    bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
                else:
                    bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)
    return True


def _close_known_popup(bot):
    screen = bot.screenshot()
    if find(bot, "LoginGifts/detail_popup", screen, threshold=0.82,
            region=(80, 20, 100, 36)) is not None:
        bot.back(delay=0.7)


def run_opened(bot, due_keys: set[str]) -> tuple[dict[str, str], bool]:
    """Sweep the carousel once and process only known tabs with a real red dot.

    Result values are ``no_dot``, ``cleared`` or ``remaining``. A complete
    ``no_dot`` sweep is still a valid daily check, while ``remaining`` is
    logged distinctly and is never reported as a successful claim.
    """
    results = {key: "no_dot" for key in due_keys}
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72, region=(0, 0, 100, 13)) is None:
        return_home(bot)
        return results, False

    handled = set()
    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            screen = bot.screenshot()
            dots = _dots(bot, screen)
            for spec in SPECS:
                key = spec.task.key
                if key not in due_keys or key in handled:
                    continue
                tab = find(bot, spec.tab, screen, threshold=0.70, region=(0, 7, 100, 19))
                if tab is None or not any(_near_tab(dot, tab) for dot in dots):
                    continue

                bot.record(f"Gift Claims: Valuable Event mở {spec.task.label} (có dấu đỏ)")
                bot.tap(*tab, delay=2)
                if spec.claims:
                    claimed = tap_claims(bot, spec.claims) > 0
                else:
                    claimed = False
                    bot.log(f"Gift Claims: {spec.task.label} không có nút nhận miễn phí an toàn")
                _close_known_popup(bot)

                after = bot.screenshot()
                after_tab = find(bot, spec.tab, after, threshold=0.70,
                                 region=(0, 7, 100, 19))
                after_dots = _dots(bot, after)
                dot_gone = (after_tab is None
                            or not any(_near_tab(dot, after_tab) for dot in after_dots))
                state = "đã mất" if dot_gone else "vẫn còn"
                bot.log(f"Gift Claims: {spec.task.label} - dấu đỏ {state} sau xử lý")
                results[key] = ("cleared" if dot_gone else
                                "claimed_remaining" if claimed else "remaining")
                handled.add(key)
                screen = after

            if step == MAX_SWIPES:
                break
            if direction < 0:
                bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
            else:
                bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)

    clean = _verify_clean(bot)
    bot.record("Gift Claims: Valuable Event - "
               + ("DONE, đã hết dấu đỏ bên trong" if clean
                  else "chưa DONE, vẫn còn dấu đỏ bên trong"))
    return_home(bot)
    return results, clean


KEYS = {spec.task.key for spec in SPECS}
