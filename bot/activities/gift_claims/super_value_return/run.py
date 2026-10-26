"""Danh sách event của Super Value Return: ảnh tab + flow (ExactFlow) của từng event; cách đi hàng tab ở zone.py."""
from dataclasses import dataclass

from . import (city_growth_plan, empire_depot, login_gifts, lucky_raffle,
               refining_weekly_card)
from ..common import (TEXT_CLAIM_CONTROLS, back_if_close_x, find,
                      mark_task_done)
from ..valuable_event import hall_of_historic_generals, soul_of_spiritual_beast
from ..valuable_event.named_flow import (CAROUSEL_EDGE_CONFIRMATIONS,
                                         ExactFlow, SLOW_SWIPE_DURATION,
                                         STEP_DELAY, TASK_TAB_THRESHOLD,
                                         TOP_CAROUSEL, carousel_moved,
                                         process_exact)

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
        done=("SuperValueReturn/CityGrowthPlan/level_15_claimed",),
        scroll_claims=True)),
)

KEYS = {spec.task.key for spec in SPECS}


def run_opened(bot, due_keys: set[str], *, handled: set[str] | None = None
               ) -> tuple[dict[str, str], bool]:
    results = {key: "not_present" for key in due_keys}
    if find(bot, PAGE, bot.screenshot(), threshold=0.72,
            region=(0, 0, 100, 13)) is None:
        return results, False

    handled = handled if handled is not None else set()
    pending = set(due_keys) - handled
    attempted_this_sweep: set[str] = set()
    for phase, start_x, end_x in (("rewind", 20, 85), ("scan", 85, 55)):
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
                spec, pos = min(visible, key=lambda item: item[1][0])
                key = spec.task.key
                bot.record(f"Gift Claims: Super Value Return mở {spec.task.label}")
                bot.tap(*pos, delay=STEP_DELAY)
                if key == login_gifts.KEY:
                    completed = login_gifts.claim_opened(bot)
                elif key == refining_weekly_card.KEY:
                    completed = refining_weekly_card.claim_opened(bot)
                elif key == hall_of_historic_generals.KEY:
                    completed = hall_of_historic_generals.claim_opened(bot)
                elif key == soul_of_spiritual_beast.KEY:
                    completed = soul_of_spiritual_beast.claim_opened(bot)
                else:
                    completed = process_exact(bot, spec.flow)
                attempted_this_sweep.add(key)
                if completed == "done_1":
                    results[key] = "done_1"
                else:
                    results[key] = "done" if completed else "terminal_not_found"
                if not completed:
                    bot.record(f"Gift Claims: {spec.task.label} chưa đạt điều kiện DONE; "
                               "giữ PENDING và tiếp tục nhiệm vụ kế tiếp")
                elif completed != "done_1":
                    mark_task_done(bot, key)
                    handled.add(key)
                    pending.discard(key)
                bot.record(f"Gift Claims: {spec.task.label} đã chốt trạng thái "
                           f"{'DONE' if completed else 'PENDING'}; "
                           "chờ 1s rồi mới lướt carousel trên")
                bot.sleep(STEP_DELAY)

            if not pending:
                return results, True

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
