"""Deterministic two-zone runner for Valuable Event.

The carousel is rewound first. A task is selected in the upper strip, its
lower panel is completed and verified, and only then may the carousel move to
the next label. Red notification dots are deliberately not part of this flow.
"""
from dataclasses import dataclass

from . import (
    active_monthly_card, ancient_dynasty_treasury, general_vault, limited_offer,
    optional_package, refining_stone_sprint, resource_consumption_sprint,
    runestone_consumption_sprint,
    speedup_sprint, strategic_stockpile, successive_purchase_benefits,
    sulis_wishing, super_blazon_sale, super_value_weekly_card, tomb_expedition,
)
from ..common import (TEXT_CLAIM_CONTROLS, back_if_close_x, find,
                      mark_task_done)
from .named_flow import (ExactFlow, SLOW_SWIPE_DURATION, STEP_DELAY,
                         TASK_TAB_THRESHOLD, TOP_CAROUSEL, carousel_moved,
                         process_exact)

PAGE = "ValuableEvent/title"
MAX_SWIPES = 12
MAX_PARENT_PASSES = 2
COMMON_LOWER_CLAIMS = TEXT_CLAIM_CONTROLS
REWARD_DOT = "ValuableEvent/notification_dot"


@dataclass(frozen=True)
class ValuableSpec:
    task: object
    tab: str
    flow: ExactFlow


SPECS = (
    ValuableSpec(limited_offer.TASK, "LimitedOffer/tab_current",
                 limited_offer.FLOW),
    ValuableSpec(resource_consumption_sprint.TASK,
                 "ResourceConsumptionSprint/tab_current",
                 resource_consumption_sprint.FLOW),
    ValuableSpec(runestone_consumption_sprint.TASK,
                 "RunestoneConsumptionSprint/tab",
                 runestone_consumption_sprint.FLOW),
    ValuableSpec(super_blazon_sale.TASK, "SuperBlazonSale/tab_current",
                 super_blazon_sale.FLOW),
    ValuableSpec(optional_package.TASK, "OptionalPackage/tab", optional_package.FLOW),
    ValuableSpec(super_value_weekly_card.TASK,
                 "SuperValueWeeklyCard/tab_current",
                 super_value_weekly_card.FLOW),
    ValuableSpec(active_monthly_card.TASK, "ActiveMonthlyCard/tab",
                 active_monthly_card.FLOW),
    ValuableSpec(successive_purchase_benefits.TASK,
                 "SuccessivePurchaseBenefits/tab_current",
                 successive_purchase_benefits.FLOW),
    ValuableSpec(tomb_expedition.TASK, "TombExpedition/tab", tomb_expedition.FLOW),
    ValuableSpec(general_vault.TASK, "GeneralVault/tab_current",
                 general_vault.FLOW),
    # Older rotations remain named and use only their known safe controls.
    ValuableSpec(ancient_dynasty_treasury.TASK, "AncientDynastyTreasury/tab", ExactFlow(
        navigation=("AncientDynastyTreasury/button_daily_free",),
        claims=TEXT_CLAIM_CONTROLS, absence_done=True)),
    ValuableSpec(refining_stone_sprint.TASK, "RefiningStoneSprint/tab", ExactFlow(
        navigation=("SpeedupSprint/subtab_package",),
        claims=("SpeedupSprint/button_free",), absence_done=True)),
    ValuableSpec(speedup_sprint.TASK, "SpeedupSprint/tab", ExactFlow(
        navigation=("SpeedupSprint/subtab_package",),
        claims=("SpeedupSprint/button_free",), absence_done=True)),
    ValuableSpec(strategic_stockpile.TASK, "StrategicStockpile/tab_current",
                 strategic_stockpile.FLOW),
    ValuableSpec(sulis_wishing.TASK, "SulisWishing/tab", ExactFlow(skip=True)),
)


def _tab(bot, spec, screen):
    return find(bot, spec.tab, screen, threshold=TASK_TAB_THRESHOLD,
                region=TOP_CAROUSEL)


def run_opened(bot, due_keys: set[str], *, handled: set[str] | None = None
               ) -> tuple[dict[str, str], bool]:
    """Process visible due labels; bool says the complete carousel was scanned."""
    results = {key: "not_present" for key in due_keys}
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72, region=(0, 0, 100, 13)) is None:
        return results, False

    handled = handled if handled is not None else set()
    pending = set(due_keys) - handled
    attempted_this_sweep: set[str] = set()
    saw_reward_dot = False
    # Inspect while moving toward the first edge, then reverse and inspect the
    # entire strip.  The rewind phase deliberately performs every bounded
    # swipe: animated artwork made carousel_moved() occasionally report a
    # false boundary halfway across the strip, causing the old flow to reverse
    # before the first tasks were reached.
    for phase, start_x, end_x in (("rewind", 20, 85), ("scan", 85, 55)):
        bot.record("Gift Claims: Valuable Event " +
                   ("đưa carousel về biên đầu" if phase == "rewind" else
                    "quét carousel từ đầu tới cuối"))
        stagnant_swipes = 0
        for step in range(MAX_SWIPES + 1):
            bot.check()
            screen = bot.screenshot()
            if find(bot, REWARD_DOT, screen, threshold=0.70,
                    region=TOP_CAROUSEL) is not None:
                saw_reward_dot = True
            if back_if_close_x(bot, screen):
                screen = bot.screenshot()
            visible = [(spec, pos) for spec in SPECS
                       if spec.task.key in pending
                       and spec.task.key not in attempted_this_sweep
                       and (pos := _tab(bot, spec, screen)) is not None]
            processed_task = False
            if visible:
                # Settle exactly one lower-panel flow before moving the upper
                # carousel. Never reuse the other tab coordinates captured
                # before the selected event animated or changed its content.
                spec, pos = min(visible, key=lambda item: item[1][0])
                key = spec.task.key
                bot.record(f"Gift Claims: Valuable Event mở {spec.task.label}")
                bot.tap(*pos, delay=STEP_DELAY)
                completed = process_exact(bot, spec.flow)
                attempted_this_sweep.add(key)
                results[key] = "done" if completed else "terminal_not_found"
                if not completed:
                    bot.record(f"Gift Claims: {spec.task.label} chưa đạt điều kiện DONE; "
                               "giữ PENDING và tiếp tục nhiệm vụ kế tiếp")
                else:
                    mark_task_done(bot, key)
                    handled.add(key)
                    pending.discard(key)
                processed_task = True
                bot.record(f"Gift Claims: {spec.task.label} đã chốt trạng thái "
                           f"{'DONE' if completed else 'PENDING'}; "
                           "chờ 1s rồi mới lướt carousel trên")
                bot.sleep(STEP_DELAY)

            if not pending:
                return results, True

            if step < MAX_SWIPES:
                bot.swipe_percent(start_x, 14, end_x, 14,
                                  duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
                after = bot.screenshot()
                if not carousel_moved(screen, after):
                    # A lower task was useful progress. Re-capture this same
                    # carousel position so every visible tab gets a chance
                    # before two genuinely empty/stagnant swipes end a pass.
                    stagnant_swipes = 0 if processed_task else stagnant_swipes + 1
                    if phase == "scan" and stagnant_swipes >= 2:
                        bot.log("Gift Claims: Valuable Event đã chạm biên carousel")
                        break
                else:
                    stagnant_swipes = 0

    if not saw_reward_dot:
        bot.record("Gift Claims: Valuable Event đã lướt trọn một lượt và "
                   "không thấy chấm đỏ; ghi nhận một lượt không thấy cho "
                   "các nhiệm vụ còn lại, chưa DONE sớm")
    else:
        bot.record("Gift Claims: Valuable Event đã lướt hết vùng trên; "
                   "label không xuất hiện được tính là một lượt không có hôm nay")
    return results, True


KEYS = {spec.task.key for spec in SPECS}
