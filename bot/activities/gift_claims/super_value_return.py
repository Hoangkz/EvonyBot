"""Process known red-dot tabs on the fixed Super Value Return screen."""
from dataclasses import dataclass

from . import city_growth_plan, empire_depot, login_gifts, lucky_raffle
from .common import find, find_all, return_home, tap_claims

PAGE = "SuperValueReturn/title"
DOT = "SuperValueReturn/notification_dot"
MAX_SWIPES = 8


@dataclass(frozen=True)
class SuperValueSpec:
    task: object
    tab: str
    claims: tuple[str, ...] = ()
    requires_dot: bool = True


SPECS = (
    SuperValueSpec(empire_depot.TASK, "EmpireDepot/tab", ("EmpireDepot/button_claimable",)),
    SuperValueSpec(lucky_raffle.TASK, "LuckyRaffle/tab", ("LuckyRaffle/button_claimable",)),
    SuperValueSpec(city_growth_plan.TASK, "CityGrowthPlan/tab",
                   ("CityGrowthPlan/button_claim_all",)),
    # Login Gifts can contain a sparkling daily chest even after its tab dot
    # disappears, so it must be opened once on every daily scan.
    SuperValueSpec(login_gifts.TASK, "LoginGifts/tab", requires_dot=False),
)


def _near_tab(dot, tab) -> bool:
    return abs(dot[0] - tab[0]) <= 55 and abs(dot[1] - tab[1]) <= 40


def _dots(bot, screen):
    # The dot changes brightness with the rotating artwork. 0.65 still gives
    # a single exact dot on the supplied variant while 0.80 misses it.
    return find_all(bot, DOT, screen, threshold=0.65, region=(0, 7, 100, 19))


def run_opened(bot, due_keys: set[str]) -> dict[str, str]:
    """Sweep an already-open Super Value Return carousel exactly once."""
    results = {key: "no_dot" for key in due_keys}
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72, region=(0, 0, 100, 13)) is None:
        return results

    handled = set()
    if (login_gifts.KEY in due_keys
            and find(bot, login_gifts.PAGE, screen, threshold=0.70,
                     region=(0, 15, 45, 25)) is not None):
        login_gifts.claim_opened(bot)
        handled.add(login_gifts.KEY)
        results[login_gifts.KEY] = "processed"

    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            screen = bot.screenshot()
            dots = _dots(bot, screen)
            for spec in SPECS:
                key = spec.task.key
                if key not in due_keys or key in handled:
                    continue
                tab = find(bot, spec.tab, screen, threshold=0.70, region=(0, 7, 100, 20))
                has_dot = tab is not None and any(_near_tab(dot, tab) for dot in dots)
                if tab is None or (spec.requires_dot and not has_dot):
                    continue
                marker = "có dấu đỏ" if has_dot else "kiểm tra quà ngày"
                bot.record(f"Gift Claims: Super Value Return mở {spec.task.label} ({marker})")
                bot.tap(*tab, delay=2)
                if key == login_gifts.KEY:
                    claimed = bool(login_gifts.claim_opened(bot))
                elif key == city_growth_plan.KEY:
                    claimed = city_growth_plan.claim_opened(bot)
                else:
                    claimed = tap_claims(bot, spec.claims) > 0

                after = bot.screenshot()
                after_tab = find(bot, spec.tab, after, threshold=0.70,
                                 region=(0, 7, 100, 20))
                after_dots = _dots(bot, after)
                cleared = (after_tab is None
                           or not any(_near_tab(dot, after_tab) for dot in after_dots))
                results[key] = ("cleared" if cleared else
                                "claimed_remaining" if claimed else "remaining")
                handled.add(key)
                bot.log(f"Gift Claims: {spec.task.label} - dấu đỏ "
                        f"{'đã mất' if cleared else 'vẫn còn'} sau xử lý")

            if step == MAX_SWIPES:
                break
            if direction < 0:
                bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
            else:
                bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)

    return_home(bot)
    return results


KEYS = {spec.task.key for spec in SPECS}
