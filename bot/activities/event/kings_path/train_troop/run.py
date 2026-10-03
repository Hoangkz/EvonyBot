"""
run.py — nhiệm vụ Train Troop (King's Path, Day 3): Day 3 -> tab phụ "Strong Troops" -> Go ->
công trình train (game chọn ngẫu nhiên 1 trong 4 loại lính) -> Train lính cấp I cho đủ số còn
thiếu. Code riêng của King's Path; chỉ import dùng lại các bước chung của
gather_troops/train_troop/run.py (menu công trình, tính số mẻ, bấm Train, Finish All) — không
sửa code Gather Troops.

Khác Gather Troops:
- Màn event là King's Path (tiêu đề TITLE phải thấy mới bấm tab / Go).
- Nhận ra màn Train bằng nút "i" góc trên (TRAIN_INFO) — giống nhau ở cả 4 loại công trình,
  mọi cấp; Gather Troops nhận bằng các vòng cấp của đúng loại lính.
- Luôn train cấp I (nhiệm vụ tính mọi cấp): tier.choose_first_tier vuốt hàng cấp sang trái tới
  khi thấy cấp I của loại bất kỳ. Không chọn được (cấp I luôn mở = lỗi nhận diện) -> ghi lỗi,
  dừng, KHÔNG lưu _locked: lượt sau thử lại.
- Mục tiêu = số lính người dùng chọn (không đổi theo cấp).

Flow: màn chính -> Event Center -> King's Path (run_task) -> Day 3 (khoá -> _locked) -> tab
Strong Troops -> Go (OCR số đã làm; không còn Go -> xong) -> bấm giữa -> menu công trình (Speed Up
-> Finish All mẻ đang train, không tính / Train) -> màn Train -> cấp I -> số mẻ = (mục tiêu - đã
làm) / số lính mỗi mẻ -> mỗi mẻ: Train -> Training Speedup -> (lần đầu Speedup Settings) Finish
All -> đủ mẻ -> xong (mark_complete).
"""
from .....context.templates import TEMPLATE_DIR
from ...common import (
    EVENT_OPENED,
    HANDLED,
    STOP,
    EventState,
    day_locked,
    mark_complete,
    nearest_go,
    read_go_progress,
    run_task,
)
from ...constants import KINGS_PATH_ICON, THRESHOLDS as EVENT_THRESHOLDS
from ...gather_troops.train_troop.constants import (
    BUTTON_WAIT,
    FINISH_ALL,
    FINISH_ALL_POS,
    FINISH_ALL_TITLE,
    FINISH_WAIT,
    GO_WAIT,
    ON_FINISH_ALL_DIALOG,
    ON_SPEED_UP_MENU,
    ON_SPEEDUP,
    ON_TAB,
    ON_TRAIN_MENU,
    ON_TRAIN_SCREEN,
    OPEN_DAY,
    OPEN_TAB,
    SPEED_UP,
    SPEEDUP_SETTINGS,
    SPEEDUP_SETTINGS_POS,
    SPEEDUP_TITLE,
    TRAIN,
    TRAIN_THRESHOLD,
    TRAIN_WAIT,
)
from ...gather_troops.train_troop.run import (
    _confirm_finish_all,
    _find_training_speedup,
    _open_building_menu,
    _Plan,
    _plan_batches,
    _pos_of,
    _train_step,
)
from ..constants import TITLE, TITLE_REGION
from .constants import (
    DAY,
    DAY_3,
    KEY,
    TAB,
    TAB_SELECTED,
    THRESHOLDS,
    TRAIN_INFO,
    TRAIN_INFO_REGION,
)
from .tier import choose_first_tier

NAME = "Train Troop"
LOCKED_KEY = f"{KEY}_locked"   # Day 3 còn khoá: bỏ qua tới lần reset server

# Màn King's Path (lần đầu thấy thì kiểm tra Day khoá) / màn sau khi bấm Go (phải bấm Go của
# chính nhiệm vụ trước).
_EVENT_ACTIONS = (OPEN_DAY, OPEN_TAB, ON_TAB)
_AFTER_GO_ACTIONS = (ON_SPEED_UP_MENU, ON_TRAIN_MENU, ON_TRAIN_SCREEN, ON_FINISH_ALL_DIALOG,
                     ON_SPEEDUP)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    if not (TEMPLATE_DIR / KINGS_PATH_ICON).exists():
        bot.log(f"{NAME}: no event icon image yet ({KINGS_PATH_ICON}), skipped")
        return
    if bot.is_daily_done(KEY):
        bot.log(f"{NAME}: already done")
        return
    if bot.is_daily_done(LOCKED_KEY):
        bot.log(f"{NAME}: day still locked, skipped until server reset")
        return
    day = int(task.get("day") or DAY)
    target = int(task.get("value") or 0)   # tổng số lính cần train (mọi cấp)
    done = None   # số đã làm, đọc ở dòng có nút Go (None = chưa đọc / đọc lỗi)
    plan = _Plan()
    progress = {"entered": False, "went": False}

    def enter(screen):
        """Lần đầu ở màn King's Path trong lượt này: Day khoá -> lưu, STOP."""
        progress["entered"] = True
        if day_locked(bot, screen, day):
            bot.record(f"{NAME}: Day {day} locked, cannot do this task yet")
            bot.mark_daily_done(LOCKED_KEY)
            return STOP
        return None

    def handle(action, pos, screen):
        nonlocal done
        if action == EVENT_OPENED:
            return enter(bot.screenshot())
        if action in _EVENT_ACTIONS and bot.find(TITLE, screen=screen, region=TITLE_REGION) is None:
            bot.log(f"{NAME}: event tabs but not King's Path, back")
            bot.back(delay=1)
            return HANDLED
        if action in _EVENT_ACTIONS and not progress["entered"]:
            if enter(screen) == STOP:
                return STOP
        if action in _AFTER_GO_ACTIONS and not progress["went"]:
            bot.log(f"{NAME}: {action} before Go, back")
            bot.back(delay=1)
            return HANDLED
        if action in (OPEN_DAY, OPEN_TAB):
            bot.tap(*pos, delay=2)
        elif action == ON_TAB:
            go = nearest_go(bot, screen, pos)
            if go is None:
                bot.log(f"{NAME}: no Go left, done")
                mark_complete(bot, KEY)
                return STOP
            done = read_go_progress(bot, screen, go)
            if done is None:
                bot.record(f"{NAME}: cannot read progress")
            else:
                bot.log(f"{NAME}: done {done}, remaining {max(0, target - done)}")
            bot.tap(*go, delay=GO_WAIT)
            progress["went"] = True
            _open_building_menu(bot, NAME, TRAIN)
        elif action == ON_SPEED_UP_MENU:
            bot.log(f"{NAME}: building already training, Speed Up from menu (not counted)")
            bot.tap(*pos, delay=BUTTON_WAIT)
            plan.from_menu = True
        elif action == ON_TRAIN_MENU:
            bot.tap(*pos, delay=TRAIN_WAIT)
        elif action == ON_TRAIN_SCREEN:
            if plan.times is None:
                speedup = _find_training_speedup(bot, screen)
                if speedup is not None:
                    bot.log(f"{NAME}: troops already training, finishing them first (not counted)")
                    bot.tap(*speedup, delay=BUTTON_WAIT)
                    return HANDLED
                if choose_first_tier(bot) is None:
                    # Cấp I luôn mở: không chọn được = lỗi nhận diện -> không lưu _locked.
                    bot.record(f"{NAME}: ERROR cannot choose tier 1 on Train screen, retry next run")
                    return STOP
                count = max(0, target - (done or 0))
                bot.log(f"{NAME}: train tier 1, goal {target}, count {count}")
                if not _plan_batches(bot, plan, count, NAME, KEY):
                    return STOP
            return _train_step(bot, plan, NAME, KEY)
        elif action == ON_FINISH_ALL_DIALOG:
            _confirm_finish_all(bot, screen)
            plan.settings_done = True
        elif action == ON_SPEEDUP:
            if not plan.settings_done:
                bot.tap(*_pos_of(bot, screen, SPEEDUP_SETTINGS, SPEEDUP_SETTINGS_POS),
                        delay=BUTTON_WAIT)
            else:
                bot.log(f"{NAME}: Finish All (batch {plan.started}/{plan.times})")
                bot.tap(*_pos_of(bot, screen, FINISH_ALL, FINISH_ALL_POS), delay=FINISH_WAIT)
                if plan.from_menu:
                    plan.from_menu = False
                    _open_building_menu(bot, NAME, TRAIN)
        else:
            return None
        return HANDLED

    run_task(bot, state, NAME, KINGS_PATH_ICON, handle,
             targets=_TARGETS, regions=_REGIONS, thresholds=_THRESHOLDS)


# Màn sau trước, màn trước sau (giống Gather Troops); màn Train nhận bằng nút "i".
_TARGETS = [
    (FINISH_ALL_TITLE, ON_FINISH_ALL_DIALOG),
    (SPEEDUP_TITLE, ON_SPEEDUP),
    (TRAIN_INFO, ON_TRAIN_SCREEN),
    (SPEED_UP, ON_SPEED_UP_MENU),   # trước TRAIN: icon "View" của menu này khớp nhầm TRAIN
    (TRAIN, ON_TRAIN_MENU),
    (TAB_SELECTED, ON_TAB),
    (TAB, OPEN_TAB),
    (DAY_3, OPEN_DAY),
]
_REGIONS = {TRAIN_INFO: TRAIN_INFO_REGION}
_THRESHOLDS = {
    **EVENT_THRESHOLDS,
    TRAIN: TRAIN_THRESHOLD,
    SPEED_UP: TRAIN_THRESHOLD,
    **THRESHOLDS,
}
