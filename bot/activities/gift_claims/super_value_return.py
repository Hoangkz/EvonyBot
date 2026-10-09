"""Process known red-dot tabs on the fixed Super Value Return screen."""
from dataclasses import dataclass

from . import city_growth_plan, empire_depot, login_gifts, lucky_raffle
from .common import (ClaimReport, claim_fixed_controls, claim_sparkle, find,
                     find_all, return_home)

PAGE = "SuperValueReturn/title"
DOT = "SuperValueReturn/notification_dot"
MAX_SWIPES = 8
LOWER_CONTENT = (0, 20, 100, 88)
COMMON_LOWER_CLAIMS = (
    "Common/button_claimable", "Common/button_claimable_alt",
    "LimitedOffer/button_free", "SpeedupSprint/button_free",
    "SuperBlazonSale/button_free",
    "SuccessivePurchaseBenefits/button_daily_free_text",
    "SuccessivePurchaseBenefits/button_daily_free",
    "CityGrowthPlan/button_claim_all", "EmpireDepot/button_claimable",
    "LuckyRaffle/button_claimable",
)


@dataclass(frozen=True)
class SuperValueSpec:
    task: object
    tab: str
    claims: tuple[str, ...] = ()
    requires_dot: bool = True


SPECS = (
    SuperValueSpec(empire_depot.TASK, "EmpireDepot/tab",
                   ("Common/button_claimable", "Common/button_claimable_alt",
                    "EmpireDepot/button_claimable")),
    SuperValueSpec(lucky_raffle.TASK, "LuckyRaffle/tab",
                   ("Common/button_claimable", "Common/button_claimable_alt",
                    "LuckyRaffle/button_claimable")),
    SuperValueSpec(city_growth_plan.TASK, "CityGrowthPlan/tab",
                   ("CityGrowthPlan/button_claim_all",)),
    # Login Gifts can contain a sparkling daily chest even after its tab dot
    # disappears, so it must be opened once on every daily scan.
    SuperValueSpec(login_gifts.TASK, "LoginGifts/tab", requires_dot=False),
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
    # The dot changes brightness with the rotating artwork. 0.65 still gives
    # a single exact dot on the supplied variant while 0.80 misses it.
    return find_all(bot, DOT, screen, threshold=0.65, region=(0, 7, 100, 19))


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


def run_opened(bot, due_keys: set[str], *, handled: set[str] | None = None
               ) -> tuple[dict[str, str], bool]:
    """Sweep an opened carousel, clicking each red tab in encountered order."""
    results = {key: "no_dot" for key in due_keys}
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72, region=(0, 0, 100, 13)) is None:
        return results, False

    handled = handled if handled is not None else set()
    attempted_this_run = set(handled)
    if (login_gifts.KEY in due_keys
            and find(bot, login_gifts.PAGE, screen, threshold=0.70,
                     region=(0, 15, 45, 25)) is not None):
        login_gifts.claim_opened(bot)
        handled.add(login_gifts.KEY)
        results[login_gifts.KEY] = "processed"

    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            bot.check()
            screen = bot.screenshot()
            if login_gifts.KEY in due_keys and login_gifts.KEY not in handled:
                login_tab = find(bot, "LoginGifts/tab", screen, threshold=0.70,
                                 region=(0, 7, 100, 20))
                if login_tab is not None:
                    bot.record("Gift Claims: Super Value Return mở Login Gifts "
                               "(kiểm tra quà ngày)")
                    bot.tap(*login_tab, delay=2)
                    claimed = bool(login_gifts.claim_opened(bot))
                    results[login_gifts.KEY] = "processed" if claimed else "checked"
                    handled.add(login_gifts.KEY)
                    screen = bot.screenshot()
            dots = _dots(bot, screen)
            tabs = [(spec, find(bot, spec.tab, screen, threshold=0.70,
                                region=(0, 7, 100, 20))) for spec in SPECS]
            for dot in dots:
                match = _owner_for_dot(dot, tabs)
                if match is None:
                    bot.tap(max(0, dot[0] - 25), min(screen.shape[0] - 1, dot[1] + 16),
                            delay=1)
                    report = claim_fixed_controls(
                        bot, COMMON_LOWER_CLAIMS, region=LOWER_CONTENT)
                    if not report.acted:
                        claim_sparkle(bot, region=LOWER_CONTENT)
                    bot.log("Gift Claims: Super Value Return đã xử lý phần dưới "
                            "của tab đỏ chưa nhận diện")
                    continue
                spec, tab = match
                key = spec.task.key
                if key not in due_keys or key in attempted_this_run:
                    continue
                has_dot = True
                marker = "có dấu đỏ" if has_dot else "kiểm tra quà ngày"
                bot.record(f"Gift Claims: Super Value Return mở {spec.task.label} ({marker})")
                bot.tap(*tab, delay=2)
                if key == login_gifts.KEY:
                    count = login_gifts.claim_opened(bot)
                    report = ClaimReport(count, count)
                elif key == city_growth_plan.KEY:
                    claimed = int(bool(city_growth_plan.claim_opened(bot)))
                    report = ClaimReport(claimed, claimed)
                else:
                    claims = tuple(dict.fromkeys((*spec.claims, *COMMON_LOWER_CLAIMS)))
                    report = claim_fixed_controls(bot, claims, region=LOWER_CONTENT)
                    if not report.acted:
                        report = claim_sparkle(bot, region=LOWER_CONTENT)

                after = bot.screenshot()
                after_dots = _dots(bot, after)
                after_tabs = [(candidate, find(
                    bot, candidate.tab, after, threshold=0.70,
                    region=(0, 7, 100, 20))) for candidate in SPECS]
                cleared = not any(
                    (owner := _owner_for_dot(red_dot, after_tabs)) is not None
                    and owner[0].task.key == key for red_dot in after_dots)
                results[key] = ("cleared" if cleared else
                                "claimed_remaining" if report.claimed else
                                "visited_remaining" if report.acted else "remaining")
                attempted_this_run.add(key)
                if cleared or not spec.requires_dot:
                    handled.add(key)
                bot.log(f"Gift Claims: {spec.task.label} - dấu đỏ "
                        f"{'đã mất' if cleared else 'vẫn còn'} sau xử lý")

            if step == MAX_SWIPES:
                break
            if direction < 0:
                bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
            else:
                bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)

    clean = _verify_clean(bot)
    bot.record("Gift Claims: Super Value Return - "
               + ("DONE, phần trên đã hết dấu đỏ" if clean
                  else "chưa DONE, phần trên vẫn còn dấu đỏ"))
    return_home(bot)
    return results, clean


KEYS = {spec.task.key for spec in SPECS}
