"""Deterministic two-zone runner for Super Value Return / Empire Depot."""
from dataclasses import dataclass

from .. import (city_growth_plan, empire_depot, login_gifts, lucky_raffle,
                refining_weekly_card)
from ...common import (TEXT_CLAIM_CONTROLS, back_if_close_x, find,
                       mark_task_done)
from ..named_flow import (ExactFlow, SLOW_SWIPE_DURATION, STEP_DELAY,
                          TASK_TAB_THRESHOLD, TOP_CAROUSEL, carousel_moved,
                          process_exact)

PAGE = "SuperValueReturn/title"
MAX_SWIPES = 12
LOWER_CONTENT = (0, 18, 100, 99)
COMMON_LOWER_CLAIMS = TEXT_CLAIM_CONTROLS


@dataclass(frozen=True)
class SuperValueSpec:
    task: object
    tab: str
    flow: ExactFlow


SPECS = (
    SuperValueSpec(empire_depot.TASK, "EmpireDepot/tab_current", ExactFlow(
        claims=("EmpireDepot/button_claimable_current",),
        done=("EmpireDepot/chest_open",))),
    SuperValueSpec(login_gifts.TASK, "LoginGifts/tab_text", ExactFlow()),
    SuperValueSpec(lucky_raffle.TASK, "LuckyRaffle/tab", lucky_raffle.FLOW),
    SuperValueSpec(refining_weekly_card.TASK, "RefiningWeeklyCard/tab",
                   refining_weekly_card.FLOW),
    # Kept for event rotations that still expose the older free reward column.
    SuperValueSpec(city_growth_plan.TASK, "CityGrowthPlan/tab", ExactFlow(
        claims=("CityGrowthPlan/button_claim_all", "Common/button_claim_all_text"),
        # Screenshot supplied by the user belongs to this tab: require row 15
        # and its green claimed check in the same crop, not any earlier check.
        done=("CityGrowthPlan/level_15_claimed",),
        scroll_claims=True)),
)

def run_opened(bot, due_keys: set[str], *, handled: set[str] | None = None
               ) -> tuple[dict[str, str], bool]:
    results = {key: "not_present" for key in due_keys}
    if find(bot, PAGE, bot.screenshot(), threshold=0.72,
            region=(0, 0, 100, 13)) is None:
        return results, False

    handled = handled if handled is not None else set()
    pending = set(due_keys) - handled
    attempted_this_sweep: set[str] = set()
    for start_x, end_x in ((20, 85), (85, 55)):
        stagnant_swipes = 0
        for step in range(MAX_SWIPES + 1):
            bot.check()
            screen = bot.screenshot()
            popup_close = find(bot, "SuperValueReturn/button_close_popup", screen,
                               threshold=0.78, region=(80, 5, 100, 20))
            if popup_close is not None:
                bot.record("Gift Claims: đóng Depot Rewards Boost trước khi quét tab")
                bot.tap(*popup_close, delay=STEP_DELAY)
                screen = bot.screenshot()
            elif back_if_close_x(bot, screen):
                screen = bot.screenshot()
            visible = [(spec, pos) for spec in SPECS
                       if spec.task.key in pending
                       and spec.task.key not in attempted_this_sweep
                       and (pos := find(bot, spec.tab, screen,
                                        threshold=TASK_TAB_THRESHOLD,
                                        region=TOP_CAROUSEL)) is not None]
            processed_task = False
            if visible:
                # Process exactly one lower panel from this carousel position.
                # Its DONE/PENDING state must be settled before the upper
                # carousel moves; cached coordinates for other visible tabs
                # are deliberately discarded because the lower-page action
                # may animate or shift the UI on slow multi-device runs.
                spec, pos = min(visible, key=lambda item: item[1][0])
                key = spec.task.key
                bot.record(f"Gift Claims: Super Value Return mở {spec.task.label}")
                bot.tap(*pos, delay=STEP_DELAY)
                if key == login_gifts.KEY:
                    completed = login_gifts.claim_opened(bot)
                elif key == refining_weekly_card.KEY:
                    completed = refining_weekly_card.claim_opened(bot)
                else:
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
                    # Finishing one lower task is useful progress even when
                    # the top strip is already at an edge. Re-scan the same
                    # position so another visible tab can be selected from a
                    # fresh screenshot before declaring the edge stagnant.
                    stagnant_swipes = 0 if processed_task else stagnant_swipes + 1
                    if stagnant_swipes >= 2:
                        bot.log("Gift Claims: Super Value Return đã chạm biên carousel")
                        break
                else:
                    stagnant_swipes = 0

    bot.record("Gift Claims: Super Value Return đã lướt hết vùng trên")
    return results, True


KEYS = {spec.task.key for spec in SPECS}
