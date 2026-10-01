"""
run.py — flow nhiệm vụ Ground Troop (Gather Troops, Day 2).

Phần đi từ màn chính tới màn event nằm trong run_task() (xem event/common.py), nhiệm vụ
chỉ cần ảnh riêng + hàm handle.

Flow:
1. Màn chính -> nút dưới Event Center -> danh sách event -> icon Gather Troops
   (run_task, giống hệt Cultivate Generals).
2. Màn Gather Troops vừa mở: đếm ổ khoá trên hàng tab Day. Tab Day 2 còn khoá (4 ổ
   khoá) -> lưu "chưa thể thực hiện" (LOCKED_KEY, tới lần reset server) và dừng.
3. Tab "Day 2" chưa chọn -> bấm (mở ở tab phụ "Seize Time").
4. Tab phụ "Ground Troop" chưa chọn -> bấm.
5. Tab "Ground Troop" đang chọn: tìm nút "Go" đầu tiên (gần tab nhất), đọc số đã làm ở
   "0 / 500" ngay trên nút (OCR) rồi bấm Go. Không còn Go nào -> đánh dấu xong.
6. Bấm Go -> chờ 10 s (game đưa về thành, doanh trại ở giữa màn hình) -> bấm giữa màn
   hình. Thấy icon "Train" thì chờ 3 s; không thấy thì chờ 3 s, bấm giữa thêm 1 lần, chờ
   3 s. Rồi quét lại.
7. Menu doanh trại: bấm icon "Train" -> màn Train.
8. Màn Train: chọn cấp (troop_tier.choose_tier): bấm cấp phải nhất để đi lên (cấp vừa bấm
   nhảy ra giữa) tới khi thấy cấp người dùng chọn hoặc thấy ổ khoá; cấp chọn bị khoá thì
   lấy cấp mở cao nhất dưới nó, mục tiêu đổi theo cấp đó (bảng trong event.json). Cấp 7
   cũng khoá -> lưu "chưa thể thực hiện" (LOCKED_KEY) và dừng.
9. Đọc số lính tối đa một lần train (ô bên phải nút "+"), tính số lần bấm Train
   (VD 10000 / 1500 -> 7 lần).
    Vừa vào màn Train đã có mẻ đang train sẵn (nút là "Training Speedup"): Finish All mẻ đó
    trước như bước 10 nhưng không tính, rồi mới chọn cấp.
10. Mỗi lần: bấm "Train" -> nút đổi thành "Training Speedup" -> bấm -> màn Training Speedup.
    Lần đầu trong lượt: bấm "Speedup Settings" -> hộp Finish All: tích ô góc dưới trái nếu
    chưa tích -> Confirm. Rồi bấm "Finish All" -> về màn Train. Đủ số lần -> đánh dấu xong.
TODO: `done` đọc ở dòng Go đầu tiên (tier 7); khi train cấp khác cần đọc ở dòng của cấp đó.
"""
import math
from dataclasses import dataclass

from .....ocr import read_train_count
from ...common import (
    EVENT_OPENED,
    HANDLED,
    STOP,
    EventState,
    day_locked,
    nearest_go,
    read_go_progress,
    run_task,
)
from ...constants import GATHER_TROOPS_ICON
from .constants import (
    BUTTON_WAIT,
    CENTER,
    CHECKBOX_OFF,
    CONFIRM,
    CONFIRM_POS,
    DAY,
    DAY_2,
    FINISH_ALL,
    FINISH_ALL_POS,
    FINISH_ALL_TITLE,
    FINISH_WAIT,
    GO_WAIT,
    GROUND_TROOP,
    GROUND_TROOP_SELECTED,
    KEY,
    LOCKED_KEY,
    LOWEST_TIER,
    MENU_CHECK_DELAY,
    MENU_WAIT,
    ON_FINISH_ALL_DIALOG,
    ON_GROUND_TROOP,
    ON_SPEEDUP,
    ON_TRAIN_MENU,
    ON_TRAIN_SCREEN,
    OPEN_DAY_2,
    OPEN_GROUND_TROOP,
    REGIONS,
    SPEEDUP_SETTINGS,
    SPEEDUP_SETTINGS_POS,
    SPEEDUP_TITLE,
    THRESHOLDS,
    TIER_TARGETS,
    TIERS,
    TRAIN,
    TRAIN_BUTTON,
    TRAIN_BUTTON_ANY,
    TRAIN_BUTTON_POS,
    TRAIN_BUTTON_REGION,
    TRAIN_COUNT_BOX,
    TRAIN_WAIT,
)
from ..troop_tier import choose_tier

NAME = "Ground Troop"


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "level": int, "day": int}."""
    if bot.is_daily_done(KEY):
        bot.log(f"{NAME}: already done")
        return
    if bot.is_daily_done(LOCKED_KEY):
        bot.log(f"{NAME}: day still locked, skipped until server reset")
        return
    day = int(task.get("day") or DAY)
    target = int(task.get("value") or 0)   # tổng số lính cần train
    level = int(task.get("level") or LOWEST_TIER)   # cấp lính người dùng chọn
    done = None   # số đã làm, đọc ở dòng có nút Go (None = chưa đọc / đọc lỗi)
    plan = _Plan()

    def handle(action, pos, screen):
        nonlocal done
        if action == EVENT_OPENED:
            if day_locked(bot, bot.screenshot(), day):
                bot.log(f"{NAME}: Day {day} locked, cannot do this task yet")
                bot.mark_daily_done(LOCKED_KEY)
                return STOP
            return None   # Day đã mở: quét tiếp
        if action in (OPEN_DAY_2, OPEN_GROUND_TROOP):
            bot.tap(*pos, delay=2)
        elif action == ON_GROUND_TROOP:
            go = nearest_go(bot, screen, pos)
            if go is None:
                bot.log(f"{NAME}: no Go left, done")
                bot.mark_daily_done(KEY)
                return STOP
            done = read_go_progress(bot, screen, go)
            if done is None:
                bot.log(f"{NAME}: cannot read progress")
            else:
                bot.log(f"{NAME}: done {done}, remaining {max(0, target - done)}")
            bot.tap(*go, delay=GO_WAIT)
            _open_barracks_menu(bot)
        elif action == ON_TRAIN_MENU:
            bot.tap(*pos, delay=TRAIN_WAIT)
        elif action == ON_TRAIN_SCREEN:
            if plan.times is None:
                if bot.find(TRAIN_BUTTON, threshold=TRAIN_BUTTON_ANY, screen=screen,
                            region=TRAIN_BUTTON_REGION) is None:
                    # Vừa vào đã có mẻ đang train (không phải của nhiệm vụ): Finish All nó
                    # trước (không tính vào số lần), rồi mới chọn cấp / tính kế hoạch.
                    bot.log(f"{NAME}: troops already training, finishing them first (not counted)")
                    bot.tap(*TRAIN_BUTTON_POS, delay=BUTTON_WAIT)
                    return HANDLED
                tier = choose_tier(bot, TIERS, level, LOWEST_TIER)
                if tier is None:
                    bot.log(f"{NAME}: tier {LOWEST_TIER} locked, cannot do this task yet")
                    bot.mark_daily_done(LOCKED_KEY)
                    return STOP
                goal = target if tier == level else TIER_TARGETS.get(tier, 0)
                count = max(0, goal - (done or 0))
                bot.log(f"{NAME}: train tier {tier} (chosen {level}), goal {goal}, count {count}")
                if not _plan_batches(bot, plan, count):
                    return STOP
            return _train_step(bot, plan)
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
        else:
            return None
        return HANDLED

    run_task(bot, state, NAME, GATHER_TROOPS_ICON, handle,
             targets=_TARGETS, regions=REGIONS, thresholds=THRESHOLDS)


def _open_barracks_menu(bot):
    """Sau khi bấm Go (doanh trại ở giữa màn hình): bấm giữa màn hình; thấy icon Train thì
    chờ MENU_WAIT giây, không thấy thì chờ MENU_WAIT giây, bấm thêm 1 lần rồi chờ
    MENU_WAIT giây. Vòng lặp kế tiếp tự nhận ra menu (ON_TRAIN_MENU)."""
    bot.tap_percent(*CENTER, delay=MENU_CHECK_DELAY)
    if bot.find(TRAIN) is not None:
        bot.sleep(MENU_WAIT)
        return
    bot.log(f"{NAME}: Train menu not shown, tapping center again")
    bot.sleep(MENU_WAIT)
    bot.tap_percent(*CENTER, delay=MENU_WAIT)


@dataclass
class _Plan:
    """Kế hoạch train trong một lượt chạy nhiệm vụ."""
    times: int | None = None      # số lần cần bấm Train (None = chưa chọn cấp / tính)
    started: int = 0              # số lần đã bấm Train
    settings_done: bool = False   # đã tích ô trong Speedup Settings (lần đầu vào màn speedup)


def _plan_batches(bot, plan: _Plan, count: int) -> bool:
    """Đọc số lính tối đa một lần train (ô bên phải nút "+"), tính số lần cần bấm Train:
    VD 10000 lính, mỗi lần 1500 -> 7 lần (lần cuối train đủ cả mẻ). False nếu không đọc
    được hoặc không cần train nữa (đã đánh dấu xong)."""
    if count <= 0:
        bot.log(f"{NAME}: nothing left to train, done")
        bot.mark_daily_done(KEY)
        return False
    batch = read_train_count(bot.crop(bot.screenshot(), *TRAIN_COUNT_BOX))
    if not batch:
        bot.log(f"{NAME}: cannot read train count")
        return False
    plan.times = math.ceil(count / batch)
    bot.log(f"{NAME}: {batch} per batch -> {plan.times} batch(es)")
    return True


def _train_step(bot, plan: _Plan):
    """Màn Train: nút "Train" xanh -> bấm (1 mẻ); nút đã đổi thành "Training Speedup" (đang
    train) -> bấm mở màn speedup. Đã bấm đủ số lần và nút Train hiện lại -> xong.
    Mỗi lượt chỉ bấm 1 lần rồi quét lại (nút "Use" của màn speedup ở gần đúng chỗ nút Train)."""
    screen = bot.screenshot()
    train = bot.find(TRAIN_BUTTON, screen=screen, region=TRAIN_BUTTON_REGION)
    if train is None:
        bot.tap(*TRAIN_BUTTON_POS, delay=BUTTON_WAIT)     # Training Speedup
    elif plan.started >= plan.times:
        bot.log(f"{NAME}: trained {plan.started} batch(es), done")
        bot.mark_daily_done(KEY)
        return STOP
    else:
        plan.started += 1
        bot.log(f"{NAME}: Train batch {plan.started}/{plan.times}")
        bot.tap(*train, delay=BUTTON_WAIT)
    return HANDLED


def _confirm_finish_all(bot, screen):
    """Hộp Finish All (Speedup Settings): ô "dùng speedup thường khi speedup riêng không đủ"
    chưa tích thì tích, rồi bấm Confirm."""
    box = bot.find(CHECKBOX_OFF, screen=screen)
    if box is not None:
        bot.tap(*box, delay=1)
    bot.tap(*_pos_of(bot, bot.screenshot(), CONFIRM, CONFIRM_POS), delay=BUTTON_WAIT)


def _pos_of(bot, screen, template, fallback):
    """Tâm `template` trên `screen`, không thấy thì toạ độ đo sẵn `fallback`."""
    pos = bot.find(template, screen=screen)
    return fallback if pos is None else pos


# Ảnh riêng của nhiệm vụ: màn sau trước, màn trước sau; "đang chọn" trước "chưa chọn"
# (hai ảnh tab Ground Troop khớp chéo, xem constants). Hộp Finish All đè lên màn speedup
# (tiêu đề speedup vẫn khớp) nên xét trước.
_TARGETS = [
    (FINISH_ALL_TITLE, ON_FINISH_ALL_DIALOG),
    (SPEEDUP_TITLE, ON_SPEEDUP),
    *[(path, ON_TRAIN_SCREEN) for path in TIERS.values()],
    (TRAIN, ON_TRAIN_MENU),
    (GROUND_TROOP_SELECTED, ON_GROUND_TROOP),
    (GROUND_TROOP, OPEN_GROUND_TROOP),
    (DAY_2, OPEN_DAY_2),
]
