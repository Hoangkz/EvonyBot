"""Deterministic two-zone runner for Super Value Return / Empire Depot."""
from dataclasses import dataclass

from .. import (city_growth_plan, empire_depot, hall_of_historic_generals,
                login_gifts, lucky_raffle, refining_weekly_card,
                soul_of_spiritual_beast)
from ...common import (TEXT_CLAIM_CONTROLS, back_if_close_x, find,
                       mark_task_done)
from ..named_flow import (CAROUSEL_EDGE_CONFIRMATIONS, ExactFlow,
                          SLOW_SWIPE_DURATION, STEP_DELAY, TASK_TAB_THRESHOLD,
                          TOP_CAROUSEL, carousel_moved, process_exact)

PAGE = "SuperValueReturn/title"
LOWER_CONTENT = (0, 18, 100, 99)
COMMON_LOWER_CLAIMS = TEXT_CLAIM_CONTROLS


@dataclass(frozen=True)
class SuperValueSpec:
    task: object
    tab: str
    flow: ExactFlow


SPECS = (
    SuperValueSpec(empire_depot.TASK, "SuperValueReturn/EmpireDepot/tab_current", ExactFlow(
        claims=("SuperValueReturn/EmpireDepot/button_claimable_current",),
        done=("SuperValueReturn/EmpireDepot/chest_open",))),
    SuperValueSpec(login_gifts.TASK, "SuperValueReturn/LoginGifts/tab_text", ExactFlow()),
    SuperValueSpec(hall_of_historic_generals.TASK,
                   "SuperValueReturn/HallOfHistoricGenerals/tab", ExactFlow()),
    SuperValueSpec(soul_of_spiritual_beast.TASK,
                   "SuperValueReturn/SoulOfSpiritualBeast/tab", ExactFlow()),
    SuperValueSpec(lucky_raffle.TASK, "SuperValueReturn/LuckyRaffle/tab", lucky_raffle.FLOW),
    SuperValueSpec(refining_weekly_card.TASK, "SuperValueReturn/RefiningWeeklyCard/tab",
                   refining_weekly_card.FLOW),
    # Kept for event rotations that still expose the older free reward column.
    SuperValueSpec(city_growth_plan.TASK, "SuperValueReturn/CityGrowthPlan/tab", ExactFlow(
        claims=("SuperValueReturn/CityGrowthPlan/button_claim_all", "Common/button_claim_all_text"),
        # Screenshot supplied by the user belongs to this tab: require row 15
        # and its green claimed check in the same crop, not any earlier check.
        done=("SuperValueReturn/CityGrowthPlan/level_15_claimed",),
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
    # Match Valuable Event: keep moving until two consecutive screenshots
    # prove each edge. There is no local swipe-count ceiling; bot.check()
    # provides the shared Stop/deadline guard.
    # MEmu 21513 ignores the old short 85%->55% drag even though the same
    # gesture moves other emulators. Use a full carousel drag while retaining
    # the two unchanged-Hamming confirmations at each real edge.
    for phase, start_x, end_x in (("rewind", 20, 85), ("scan", 90, 10)):
        bot.record("Gift Claims: Super Value Return " +
                   ("đưa carousel về biên đầu" if phase == "rewind" else
                    "quét carousel từ đầu tới cuối"))
        stagnant_swipes = 0
        while True:
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
                outcome = None
                if key == login_gifts.KEY:
                    completed = login_gifts.claim_opened(bot)
                elif key == refining_weekly_card.KEY:
                    outcome = refining_weekly_card.claim_opened(bot)
                    completed = outcome == refining_weekly_card.DONE
                elif key == hall_of_historic_generals.KEY:
                    outcome = hall_of_historic_generals.claim_opened(bot)
                    completed = outcome == hall_of_historic_generals.DONE
                elif key == soul_of_spiritual_beast.KEY:
                    outcome = soul_of_spiritual_beast.claim_opened(bot)
                    completed = outcome == soul_of_spiritual_beast.DONE
                else:
                    completed = process_exact(bot, spec.flow)
                attempted_this_sweep.add(key)
                results[key] = (outcome if outcome is not None else
                                ("done" if completed else "terminal_not_found"))
                if not completed:
                    state = "DONE_1" if outcome == "done_1" else "PENDING"
                    bot.record(f"Gift Claims: {spec.task.label} đạt {state}; "
                               "tiếp tục nhiệm vụ kế tiếp")
                else:
                    mark_task_done(bot, key)
                    handled.add(key)
                    pending.discard(key)
                shown_state = ("DONE" if completed else
                               ("DONE_1" if outcome == "done_1"
                                else "PENDING"))
                bot.record(f"Gift Claims: {spec.task.label} đã chốt trạng thái "
                           f"{shown_state}; "
                           "chờ 1s rồi mới lướt carousel trên")
                bot.sleep(STEP_DELAY)

            if not pending:
                return results, True

            # Re-capture after lower-panel actions so selection changes do not
            # masquerade as horizontal carousel movement.
            before_swipe = bot.screenshot()
            bot.swipe_percent(start_x, 14, end_x, 14,
                              duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
            after = bot.screenshot()
            if not carousel_moved(before_swipe, after):
                stagnant_swipes += 1
                if stagnant_swipes >= CAROUSEL_EDGE_CONFIRMATIONS:
                    edge = "đầu" if phase == "rewind" else "cuối"
                    bot.record("Gift Claims: Super Value Return đã xác nhận "
                               f"biên {edge} sau "
                               f"{CAROUSEL_EDGE_CONFIRMATIONS} cú không đổi")
                    break
            else:
                stagnant_swipes = 0

    bot.record("Gift Claims: Super Value Return đã xác nhận đủ biên đầu "
               "và biên cuối")
    return results, True


KEYS = {spec.task.key for spec in SPECS}
