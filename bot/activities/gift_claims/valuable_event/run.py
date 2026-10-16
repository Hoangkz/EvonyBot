"""Scan every known red-dot tab during one Valuable Event session."""
from dataclasses import dataclass

from . import (
    ancient_dynasty_treasury,
    general_vault,
    limited_offer,
    refining_stone_sprint,
    resource_consumption_sprint,
    speedup_sprint,
    strategic_stockpile,
    successive_purchase_benefits,
    sulis_wishing,
    super_blazon_sale,
    super_value_weekly_card,
)
from ..common import (ClaimReport, TEXT_CLAIM_CONTROLS, find, find_all,
                     mark_task_done, return_home)
from .named_flow import process_lower

PAGE = "ValuableEvent/title"
DOT = "ValuableEvent/notification_dot"
MAX_SWIPES = 8
MAX_PARENT_PASSES = 2
LOWER_CONTENT = (0, 20, 100, 88)
COMMON_LOWER_CLAIMS = TEXT_CLAIM_CONTROLS


@dataclass(frozen=True)
class ValuableSpec:
    task: object
    tab: str
    navigation: tuple[str, ...] = ()
    claims: tuple[str, ...] = ()


SPECS = (
    ValuableSpec(resource_consumption_sprint.TASK,
                 "ResourceConsumptionSprint/tab",
                 navigation=("SpeedupSprint/subtab_package",),
                 claims=("ResourceConsumptionSprint/button_free",)),
    ValuableSpec(ancient_dynasty_treasury.TASK,
                 "AncientDynastyTreasury/tab",
                 navigation=("AncientDynastyTreasury/button_daily_free",)),
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


def _verify_clean(bot, ignored_keys=()) -> bool:
    """Verify that no red tab remains anywhere in the parent carousel."""
    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            bot.check()
            screen = bot.screenshot()
            dots = _dots(bot, screen)
            tabs = [(spec, find(bot, spec.tab, screen, threshold=0.70,
                                region=(0, 7, 100, 19))) for spec in SPECS]
            for dot in dots:
                owner = _owner_for_dot(dot, tabs)
                if owner is None or owner[0].task.key not in ignored_keys:
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
    return process_lower(bot, navigation, claims)


def run_opened(bot, due_keys: set[str], *, handled: set[str] | None = None
               ) -> tuple[dict[str, str], bool]:
    """Sweep the full carousel up to twice and process every pending tab.

    Result values are ``no_dot``, ``cleared`` or ``remaining``. A complete
    sweep is complete only after a second top-carousel check finds no red dot.
    """
    results = {key: "no_dot" for key in due_keys}
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72, region=(0, 0, 100, 13)) is None:
        return_home(bot)
        return results, False

    handled = handled if handled is not None else set()
    remaining = set(due_keys) - set(handled)
    clean = False
    for pass_number in range(1, MAX_PARENT_PASSES + 1):
        attempted_this_pass = set()
        bot.record(f"Gift Claims: Valuable Event bắt đầu vòng tổng "
                   f"{pass_number}/{MAX_PARENT_PASSES}")
        for direction in (-1, 1):
            for step in range(MAX_SWIPES + 1):
                bot.check()
                screen = bot.screenshot()
                dots = _dots(bot, screen)
                tabs = [(spec, find(bot, spec.tab, screen, threshold=0.70,
                                    region=(0, 7, 100, 19))) for spec in SPECS]
            # DB-pending fixed labels are authoritative.  A claim badge may
            # disappear before a free control becomes visible, so visit every
            # known label encountered from left to right even without a dot.
                candidates = list(dots)
                for spec, tab in tabs:
                    if (tab is not None and spec.task.key in remaining
                            and spec.task.key not in attempted_this_pass
                            and not any((_owner_for_dot(dot, tabs) or (None,))[0]
                                        is spec for dot in dots)):
                        candidates.append((tab[0] + 25, tab[1] - 16))
                for dot in sorted(candidates, key=lambda point: point[0]):
                    match = _owner_for_dot(dot, tabs)
                    if match is None:
                    # Click the marker's owning tab even when this rotation has
                    # no captured module yet. Never click inside its body.
                        bot.tap(max(0, dot[0] - 25),
                                min(screen.shape[0] - 1, dot[1] + 16), delay=1)
                        _process_lower(bot, (), ())
                        bot.log("Gift Claims: Valuable Event đã xử lý phần dưới "
                                "của tab đỏ chưa nhận diện")
                        continue
                    spec, tab = match
                    key = spec.task.key
                    if key not in remaining or key in attempted_this_pass:
                        continue

                    has_dot = any((_owner_for_dot(red_dot, tabs) or (None,))[0]
                                  is spec for red_dot in dots)
                    bot.record(f"Gift Claims: Valuable Event mở {spec.task.label} "
                               f"({'có dấu đỏ' if has_dot else 'label DB-pending'})")
                    bot.tap(*tab, delay=1)
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
                    bot.log(f"Gift Claims: {spec.task.label} - dấu đỏ {state} "
                            f"sau vòng {pass_number}")
                    results[key] = ("cleared" if dot_gone else
                                    "claimed_remaining" if report.claimed else
                                    "visited_remaining" if report.acted or navigated
                                    else "remaining")
                    attempted_this_pass.add(key)

                    # A no-badge DB label is complete after its lower content
                    # is exhausted. A persistent badge gets exactly one full
                    # second parent pass before it is classified as paid or
                    # decorative and checkpointed for today.
                    if dot_gone or not has_dot or pass_number == MAX_PARENT_PASSES:
                        handled.add(key)
                        remaining.discard(key)
                        mark_task_done(bot, key)
                        if not dot_gone:
                            bot.record(f"Gift Claims: {spec.task.label} badge vẫn "
                                       "còn sau 2 vòng tổng; coi là paid/trang trí "
                                       "và DONE hôm nay")
                    screen = after

                if step == MAX_SWIPES:
                    break
                if direction < 0:
                    bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
                else:
                    bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)

        clean = _verify_clean(bot, handled)
        bot.record(f"Gift Claims: Valuable Event kết thúc vòng tổng "
                   f"{pass_number}/{MAX_PARENT_PASSES}: "
                   + ("phần trên đã sạch" if clean else
                      "phần trên vẫn còn badge, sẽ kiểm tra lại"))
        if clean:
            break

    if clean and due_keys - handled:
        # The region-1 coordinator owns the daily checkpoints.  A complete
        # two-direction scan with no red tab lets it finish the remaining
        # child keys without reopening clean tabs.
        bot.record("Gift Claims: Valuable Event không còn badge chưa xử lý nhưng "
                   "vẫn có label DB chưa xuất hiện; giữ chúng cho lượt dò tổng")
    bot.record("Gift Claims: Valuable Event - "
               + ("DONE, phần trên không còn badge chưa xử lý" if clean
                  else "chưa DONE, phần trên vẫn còn dấu đỏ"))
    return_home(bot)
    return results, clean


KEYS = {spec.task.key for spec in SPECS}
