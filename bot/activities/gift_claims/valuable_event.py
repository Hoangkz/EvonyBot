"""Scan every known red-dot tab during one Valuable Event session."""
from dataclasses import dataclass

from . import (
    general_vault,
    limited_offer,
    refining_stone_sprint,
    speedup_sprint,
    strategic_stockpile,
    successive_purchase_benefits,
    sulis_wishing,
    super_blazon_sale,
    super_value_weekly_card,
)
from .common import (ClaimReport, claim_fixed_controls, claim_sparkle, find,
                     find_all, return_home, tap_claims)

PAGE = "ValuableEvent/title"
DOT = "ValuableEvent/notification_dot"
MAX_SWIPES = 8
LOWER_CONTENT = (0, 20, 100, 88)
COMMON_LOWER_CLAIMS = (
    "Common/button_claim_text",
    "GeneralVault/button_daily_free",
    "SuccessivePurchaseBenefits/button_daily_free_text",
    "SuccessivePurchaseBenefits/button_daily_free",
    "Common/button_claimable", "Common/button_claimable_alt",
    "LimitedOffer/button_free", "SpeedupSprint/button_free",
    "SuperBlazonSale/button_free",
    "CityGrowthPlan/button_claim_all", "EmpireDepot/button_claimable",
    "LuckyRaffle/button_claimable",
)


@dataclass(frozen=True)
class ValuableSpec:
    task: object
    tab: str
    navigation: tuple[str, ...] = ()
    claims: tuple[str, ...] = ()


SPECS = (
    ValuableSpec(general_vault.TASK, "GeneralVault/tab", claims=("GeneralVault/button_daily_free",)),
    ValuableSpec(refining_stone_sprint.TASK, "RefiningStoneSprint/tab",
                 navigation=("SpeedupSprint/subtab_package",),
                 claims=("SpeedupSprint/button_free",)),
    ValuableSpec(strategic_stockpile.TASK, "StrategicStockpile/tab",
                 navigation=("StrategicStockpile/subtab_stockpile",)),
    ValuableSpec(limited_offer.TASK, "LimitedOffer/tab",
                 claims=("LimitedOffer/button_free",)),
    ValuableSpec(speedup_sprint.TASK, "SpeedupSprint/tab",
                 navigation=("SpeedupSprint/subtab_package",),
                 claims=("SpeedupSprint/button_free",)),
    ValuableSpec(super_blazon_sale.TASK, "SuperBlazonSale/tab",
                 claims=("SuperBlazonSale/button_free",)),
    ValuableSpec(sulis_wishing.TASK, "SulisWishing/tab"),
    ValuableSpec(super_value_weekly_card.TASK, "SuperValueWeeklyCard/tab",
                 navigation=("SuperValueWeeklyCard/button_scores",)),
    ValuableSpec(successive_purchase_benefits.TASK, "SuccessivePurchaseBenefits/tab",
                 claims=("SuccessivePurchaseBenefits/button_daily_free_text",
                         "SuccessivePurchaseBenefits/button_daily_free",
                         "LimitedOffer/button_free")),
)


def _near_tab(dot, tab) -> bool:
    return abs(dot[0] - tab[0]) <= 55 and abs(dot[1] - tab[1]) <= 40


def _owner_for_dot(dot, tabs):
    """Assign one marker to the nearest visible tab, never two neighbours."""
    candidates = [(spec, tab) for spec, tab in tabs
                  if tab is not None and abs(dot[1] - tab[1]) <= 40
                  and abs(dot[0] - tab[0]) <= 70]
    if not candidates:
        return None
    return min(candidates, key=lambda item:
               (dot[0] - item[1][0]) ** 2 + (dot[1] - item[1][1]) ** 2)


def _dots(bot, screen):
    return find_all(bot, DOT, screen, threshold=0.65, region=(0, 7, 100, 18))


def _verify_clean(bot) -> bool:
    """Verify that no red tab remains anywhere in the parent carousel."""
    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            bot.check()
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


def _process_lower(bot, navigation: tuple[str, ...],
                   claims: tuple[str, ...]) -> tuple[ClaimReport, int]:
    """Navigate first, then claim fixed controls, then one verified sparkle."""
    navigated = (tap_claims(bot, navigation, max_taps=len(navigation),
                            initial_wait_attempts=2, region=LOWER_CONTENT)
                 if navigation else 0)
    templates = tuple(dict.fromkeys((*claims, *COMMON_LOWER_CLAIMS)))
    report = claim_fixed_controls(bot, templates, region=LOWER_CONTENT)
    if not report.acted:
        report = claim_sparkle(bot, region=LOWER_CONTENT)
    return report, navigated


def run_opened(bot, due_keys: set[str], *, handled: set[str] | None = None
               ) -> tuple[dict[str, str], bool]:
    """Sweep the carousel once and process every visible red dot.

    Result values are ``no_dot``, ``cleared`` or ``remaining``. A complete
    sweep is complete only after a second top-carousel check finds no red dot.
    """
    results = {key: "no_dot" for key in due_keys}
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72, region=(0, 0, 100, 13)) is None:
        return_home(bot)
        return results, False

    handled = handled if handled is not None else set()
    attempted_this_run = set(handled)
    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            bot.check()
            screen = bot.screenshot()
            dots = _dots(bot, screen)
            tabs = [(spec, find(bot, spec.tab, screen, threshold=0.70,
                                region=(0, 7, 100, 19))) for spec in SPECS]
            for dot in dots:
                match = _owner_for_dot(dot, tabs)
                if match is None:
                    # Click the marker's owning tab even when this rotation has
                    # no captured module yet. Never click inside its body.
                    bot.tap(max(0, dot[0] - 25), min(screen.shape[0] - 1, dot[1] + 16),
                            delay=1)
                    _process_lower(bot, (), ())
                    bot.log("Gift Claims: Valuable Event đã xử lý phần dưới của tab đỏ chưa nhận diện")
                    continue
                spec, tab = match
                key = spec.task.key
                if key not in due_keys or key in attempted_this_run:
                    continue

                bot.record(f"Gift Claims: Valuable Event mở {spec.task.label} (có dấu đỏ)")
                bot.tap(*tab, delay=2)
                if key == strategic_stockpile.KEY:
                    verified = strategic_stockpile.claim_opened(bot)
                    report = ClaimReport(verified, verified)
                    navigated = 1
                else:
                    report, navigated = _process_lower(
                        bot, spec.navigation, spec.claims)
                _close_known_popup(bot)

                after = bot.screenshot()
                after_dots = _dots(bot, after)
                after_tabs = [(candidate, find(
                    bot, candidate.tab, after, threshold=0.70,
                    region=(0, 7, 100, 19))) for candidate in SPECS]
                dot_gone = not any(
                    (owner := _owner_for_dot(red_dot, after_tabs)) is not None
                    and owner[0].task.key == key for red_dot in after_dots)
                state = "đã mất" if dot_gone else "vẫn còn"
                bot.log(f"Gift Claims: {spec.task.label} - dấu đỏ {state} sau xử lý")
                results[key] = ("cleared" if dot_gone else
                                "claimed_remaining" if report.claimed else
                                "visited_remaining" if report.acted or navigated
                                else "remaining")
                attempted_this_run.add(key)
                if dot_gone:
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
               + ("DONE, phần trên đã hết dấu đỏ" if clean
                  else "chưa DONE, phần trên vẫn còn dấu đỏ"))
    return_home(bot)
    return results, clean


KEYS = {spec.task.key for spec in SPECS}
