"""
run.py — flow chung của các nhiệm vụ train lính trong Gather Troops (Ground Troop Day 2,
Mounted Troop Day 3, ...). Mỗi nhiệm vụ chỉ khác tab Day, tab phụ và ảnh cấp lính: khai
báo một TroopTask rồi gọi run(bot, task, state, troop).
King's Path Train Troop (kings_path/train_troop/) dùng lại flow này với event_icon /
title của King's Path và first_tier=True (luôn train cấp I, troop_tier.choose_first_tier).

Phần đi từ màn chính tới màn event nằm trong run_task() (xem event/common.py).

Flow:
1. Màn chính -> nút dưới Event Center -> danh sách event -> icon Gather Troops
   (run_task, giống hệt Cultivate Generals).
   Đang ở sẵn màn Gather Troops thì làm luôn từ bước 2. Chưa bấm Go trong lượt này mà gặp
   menu công trình / màn Train / màn speedup (VD nhiệm vụ trước dừng ở đó) -> Back cho tới
   khi về lại Gather Troops (bắt buộc đi qua dòng Go để biết nhiệm vụ còn cần làm không).
2. Màn Gather Troops vừa mở: đếm ổ khoá trên hàng tab Day. Tab Day của nhiệm vụ còn khoá
   -> lưu "chưa thể thực hiện" (locked_key, tới lần reset server) và dừng.
3. Tab "Day N" chưa chọn -> bấm.
4. Tab phụ của nhiệm vụ (VD "Ground Troop", "Mounted Troop") chưa chọn -> bấm.
5. Tab phụ đang chọn: tìm nút "Go" đầu tiên (gần tab nhất), đọc số đã làm ở "0 / 500"
   ngay trên nút (OCR) rồi bấm Go. Không còn Go nào -> đánh dấu xong.
6. Bấm Go -> chờ 10 s (game đưa về thành, công trình ở giữa màn hình) -> bấm giữa màn
   hình. Thấy menu (icon "Train" hoặc "Speed Up") thì chờ 3 s; không thấy thì chờ 3 s, bấm
   giữa thêm 1 lần, chờ 3 s. Rồi quét lại.
7. Menu công trình:
   - Có icon "Speed Up" (công trình đang có mẻ train, không có "Train"): bấm -> màn Training
     Speedup -> Finish All như bước 10 (không tính) -> về lại thành (công trình vẫn ở giữa)
     -> làm lại bước 6 (bấm giữa màn hình), lúc này menu có "Train".
   - Có icon "Train": bấm -> màn Train.
8. Màn Train: chọn cấp (troop_tier.choose_tier): bấm cấp phải nhất để đi lên (cấp vừa bấm
   nhảy ra giữa) tới khi thấy cấp người dùng chọn hoặc thấy ổ khoá; cấp chọn bị khoá thì
   lấy cấp mở cao nhất dưới nó, mục tiêu đổi theo cấp đó (bảng trong event.json). Cấp 7
   cũng khoá -> lưu "chưa thể thực hiện" (locked_key) và dừng.
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
from dataclasses import dataclass, field

from .....context.templates import TEMPLATE_DIR
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
from ...constants import GATHER_TROOPS_ICON, THRESHOLDS as EVENT_THRESHOLDS
from ..troop_tier import TIER_ROW_REGION, TIER_THRESHOLD, choose_first_tier, choose_tier
from .constants import (
    BUTTON_WAIT,
    CENTER,
    CENTER_TAP_EXTRA,
    CHECKBOX_OFF,
    CONFIRM,
    CONFIRM_POS,
    FINISH_ALL,
    FINISH_ALL_POS,
    FINISH_ALL_TITLE,
    FINISH_WAIT,
    GO_WAIT,
    LOWEST_TIER,
    MENU_CHECK_DELAY,
    MENU_WAIT,
    ON_FINISH_ALL_DIALOG,
    ON_SPEEDUP,
    ON_TAB,
    ON_SPEED_UP_MENU,
    ON_TRAIN_MENU,
    ON_TRAIN_SCREEN,
    OPEN_DAY,
    OPEN_TAB,
    SPEEDUP_SETTINGS,
    SPEEDUP_SETTINGS_POS,
    SPEED_UP,
    SPEEDUP_TITLE,
    TRAIN,
    TRAIN_BUTTON,
    TRAIN_BUTTON_POS,
    TRAIN_BUTTON_REGION,
    TRAIN_COUNT_BOX,
    TRAIN_THRESHOLD,
    TRAIN_WAIT,
    TRAINING_SPEEDUP,
    TRAINING_SPEEDUP_THRESHOLD,
    tier_targets,
)


@dataclass(frozen=True)
class TroopTask:
    """Phần riêng của một nhiệm vụ train lính."""
    key: str                      # key trong settings / event.json (VD "gather_troops_ground_troop")
    name: str                     # tên trong log (VD "Ground Troop")
    day: int                      # ngày mở nhiệm vụ (dùng khi settings thiếu "day")
    day_tab: str                  # ảnh tab "Day N" khi CHƯA chọn
    tab: str                      # ảnh tab phụ khi chưa chọn
    tab_selected: str             # ảnh tab phụ khi đang chọn
    # {cấp: ảnh cấp lính} (troop_tier.tier_images), hoặc {cấp: [ảnh từng loại]} khi một cấp
    # có nhiều vòng tròn (bẫy: troop_tier.kind_images)
    tiers: dict
    # Ngưỡng riêng của ảnh tab Day / tab phụ (đo chéo chưa chọn - đang chọn).
    thresholds: dict[str, float] = field(default_factory=dict)
    lowest: int = LOWEST_TIER     # cấp thấp nhất nhiệm vụ tính ("tier 7 and above")
    menu_icon: str = TRAIN        # icon mở màn Train trong menu công trình (bẫy: "Build")
    speedup_title: str = SPEEDUP_TITLE   # tiêu đề màn speedup (bẫy: "Trap Building Speedup")
    event_icon: str = GATHER_TROOPS_ICON  # icon event trong danh sách (King's Path: KINGS_PATH_ICON)
    # Tiêu đề màn event, phải thấy mới bấm tab Day / tab phụ / Go (King's Path: hàng tab Day
    # giống hệt Gather Troops). None = không kiểm tra.
    title: str | None = None
    title_region: tuple | None = None
    # True: luôn train cấp thấp nhất (vòng đầu tiên, troop_tier.choose_first_tier) thay vì
    # cấp người dùng chọn (King's Path: "Train N Troop(s)" tính mọi cấp).
    first_tier: bool = False

    @property
    def locked_key(self) -> str:
        """Lưu trong daily_done khi tab Day hoặc cấp 7 còn khoá: bỏ qua nhiệm vụ tới lần
        reset server kế tiếp."""
        return f"{self.key}_locked"


def run(bot, task: dict, state: EventState, troop: TroopTask):
    """`task` là settings của nhiệm vụ: {"value": int, "level": int, "day": int}."""
    name, key, locked_key = troop.name, troop.key, troop.locked_key
    if not (TEMPLATE_DIR / troop.event_icon).exists():
        bot.log(f"{name}: no event icon image yet ({troop.event_icon}), skipped")
        return
    if bot.is_daily_done(key):
        bot.log(f"{name}: already done")
        return
    if bot.is_daily_done(locked_key):
        bot.log(f"{name}: day still locked, skipped until server reset")
        return
    day = int(task.get("day") or troop.day)
    target = int(task.get("value") or 0)   # tổng số lính cần train
    level = int(task.get("level") or troop.lowest)   # cấp lính người dùng chọn
    done = None   # số đã làm, đọc ở dòng có nút Go (None = chưa đọc / đọc lỗi)
    plan = _Plan()
    targets_by_tier = tier_targets(key)

    # Bắt buộc đi qua màn Gather Troops trong lượt chạy này: kiểm tra Day khoá (lần đầu thấy
    # màn Gather Troops — vừa mở từ danh sách event, hoặc đang ở sẵn đó) -> tab Day / tab
    # phụ -> bấm Go của chính nhiệm vụ (đọc số đã làm), rồi mới xử lý menu công trình / màn
    # Train / màn speedup. Gặp các màn đó trước khi bấm Go (VD nhiệm vụ trước dừng ở màn
    # Train của nó) thì Back cho tới khi về lại Gather Troops (qua màn chính nếu cần).
    progress = {"entered": False, "went": False}

    def enter(screen):
        """Lần đầu ở màn Gather Troops trong lượt này: Day khoá -> lưu, STOP."""
        progress["entered"] = True
        if day_locked(bot, screen, day):
            bot.record(f"{name}: Day {day} locked, cannot do this task yet")
            bot.mark_daily_done(locked_key)
            return STOP
        return None

    def handle(action, pos, screen):
        nonlocal done
        if action == EVENT_OPENED:
            return enter(bot.screenshot())   # Day đã mở: quét tiếp
        if (action in _EVENT_ACTIONS and troop.title is not None
                and bot.find(troop.title, screen=screen, region=troop.title_region) is None):
            bot.log(f"{name}: event tabs but not this event, back")
            bot.back(delay=1)
            return HANDLED
        if action in _EVENT_ACTIONS and not progress["entered"]:
            if enter(screen) == STOP:
                return STOP
        if action in _AFTER_GO_ACTIONS and not progress["went"]:
            bot.log(f"{name}: {action} before Go, back")
            bot.back(delay=1)
            return HANDLED
        if action in (OPEN_DAY, OPEN_TAB):
            bot.tap(*pos, delay=2)
        elif action == ON_TAB:
            go = nearest_go(bot, screen, pos)
            if go is None:
                bot.log(f"{name}: no Go left, done")
                bot.mark_daily_done(key)
                return STOP
            done = read_go_progress(bot, screen, go)
            if done is None:
                bot.record(f"{name}: cannot read progress")
            else:
                bot.log(f"{name}: done {done}, remaining {max(0, target - done)}")
            bot.tap(*go, delay=GO_WAIT)
            progress["went"] = True
            _open_building_menu(bot, name, troop.menu_icon)
        elif action == ON_SPEED_UP_MENU:
            # Công trình đang train (không phải của nhiệm vụ): Finish All ở màn speedup rồi
            # mở lại menu (xem nhánh ON_SPEEDUP).
            bot.log(f"{name}: building already training, Speed Up from menu (not counted)")
            bot.tap(*pos, delay=BUTTON_WAIT)
            plan.from_menu = True
        elif action == ON_TRAIN_MENU:
            bot.tap(*pos, delay=TRAIN_WAIT)
        elif action == ON_TRAIN_SCREEN:
            if plan.times is None:
                speedup = _find_training_speedup(bot, screen)
                if speedup is not None:
                    # Vừa vào đã có mẻ đang train (không phải của nhiệm vụ): Finish All nó
                    # trước (không tính vào số lần), rồi mới chọn cấp / tính kế hoạch. Phải
                    # làm trước choose_tier: đang train thì không có nút "+", cấp ở giữa sẽ
                    # bị coi là khoá.
                    bot.log(f"{name}: troops already training, finishing them first (not counted)")
                    bot.tap(*speedup, delay=BUTTON_WAIT)
                    return HANDLED
                tier = (choose_first_tier(bot, troop.tiers) if troop.first_tier
                        else choose_tier(bot, troop.tiers, level, troop.lowest))
                if tier is None:
                    bot.record(f"{name}: tier {troop.lowest} locked, cannot do this task yet")
                    bot.mark_daily_done(locked_key)
                    return STOP
                goal = target if tier == level else targets_by_tier.get(tier, 0)
                count = max(0, goal - (done or 0))
                bot.log(f"{name}: train tier {tier} (chosen {level}), goal {goal}, count {count}")
                if not _plan_batches(bot, plan, count, name, key):
                    return STOP
            return _train_step(bot, plan, name, key)
        elif action == ON_FINISH_ALL_DIALOG:
            _confirm_finish_all(bot, screen)
            plan.settings_done = True
        elif action == ON_SPEEDUP:
            if not plan.settings_done:
                bot.tap(*_pos_of(bot, screen, SPEEDUP_SETTINGS, SPEEDUP_SETTINGS_POS),
                        delay=BUTTON_WAIT)
            else:
                bot.log(f"{name}: Finish All (batch {plan.started}/{plan.times})")
                bot.tap(*_pos_of(bot, screen, FINISH_ALL, FINISH_ALL_POS), delay=FINISH_WAIT)
                if plan.from_menu:
                    # Mở từ menu công trình: Finish All đưa về lại thành (công trình vẫn ở
                    # giữa) chứ không về màn Train -> mở lại menu như sau khi bấm Go.
                    plan.from_menu = False
                    _open_building_menu(bot, name, troop.menu_icon)
        else:
            return None
        return HANDLED

    run_task(bot, state, name, troop.event_icon, handle,
             targets=_targets(troop), regions=_regions(troop), thresholds=_thresholds(troop))


# Màn Gather Troops (lần đầu thấy thì kiểm tra Day khoá) / màn sau khi bấm Go (cần bấm Go
# của chính nhiệm vụ trước), xem `progress` trong run().
_EVENT_ACTIONS = (OPEN_DAY, OPEN_TAB, ON_TAB)
_AFTER_GO_ACTIONS = (ON_SPEED_UP_MENU, ON_TRAIN_MENU, ON_TRAIN_SCREEN, ON_FINISH_ALL_DIALOG,
                     ON_SPEEDUP)


def _open_building_menu(bot, name: str, menu_icon: str = TRAIN):
    """Sau khi bấm Go (công trình ở giữa màn hình): bấm giữa màn hình (mỗi lần bấm giữa chờ
    thêm CENTER_TAP_EXTRA giây cho menu hiện); thấy icon Train thì
    chờ MENU_WAIT giây, không thấy thì chờ MENU_WAIT giây, bấm thêm 1 lần rồi chờ
    MENU_WAIT giây. Vòng lặp kế tiếp tự nhận ra menu (ON_TRAIN_MENU)."""
    bot.tap_percent(*CENTER, delay=MENU_CHECK_DELAY + CENTER_TAP_EXTRA)
    screen = bot.screenshot()
    if (bot.find(SPEED_UP, threshold=TRAIN_THRESHOLD, screen=screen) is not None
            or bot.find(menu_icon, threshold=TRAIN_THRESHOLD, screen=screen) is not None):
        bot.sleep(MENU_WAIT)
        return
    bot.log(f"{name}: Train menu not shown, tapping center again")
    bot.sleep(MENU_WAIT)
    bot.tap_percent(*CENTER, delay=MENU_WAIT + CENTER_TAP_EXTRA)


@dataclass
class _Plan:
    """Kế hoạch train trong một lượt chạy nhiệm vụ."""
    times: int | None = None      # số lần cần bấm Train (None = chưa chọn cấp / tính)
    started: int = 0              # số lần đã bấm Train
    settings_done: bool = False   # đã tích ô trong Speedup Settings (lần đầu vào màn speedup)
    from_menu: bool = False       # màn speedup mở từ menu công trình (Speed Up), không từ màn Train


def _plan_batches(bot, plan: _Plan, count: int, name: str, key: str) -> bool:
    """Đọc số lính tối đa một lần train (ô bên phải nút "+"), tính số lần cần bấm Train:
    VD 10000 lính, mỗi lần 1500 -> 7 lần (lần cuối train đủ cả mẻ). False nếu không đọc
    được hoặc không cần train nữa (đã đánh dấu xong)."""
    if count <= 0:
        bot.log(f"{name}: nothing left to train, done")
        bot.mark_daily_done(key)
        return False
    batch = read_train_count(bot.crop(bot.screenshot(), *TRAIN_COUNT_BOX))
    if not batch:
        bot.record(f"{name}: cannot read train count")
        return False
    plan.times = math.ceil(count / batch)
    bot.log(f"{name}: {batch} per batch -> {plan.times} batch(es)")
    return True


def _train_step(bot, plan: _Plan, name: str, key: str):
    """Màn Train: nút "Train" xanh -> bấm (1 mẻ); nút đã đổi thành "Training Speedup" (đang
    train) -> bấm mở màn speedup. Đã bấm đủ số lần và nút Train hiện lại -> xong.
    Mỗi lượt chỉ bấm 1 lần rồi quét lại (nút "Use" của màn speedup ở gần đúng chỗ nút Train)."""
    screen = bot.screenshot()
    speedup = _find_training_speedup(bot, screen)
    train = None if speedup else bot.find(TRAIN_BUTTON, screen=screen, region=TRAIN_BUTTON_REGION)
    if speedup is not None:
        bot.tap(*speedup, delay=BUTTON_WAIT)
    elif train is None:
        bot.tap(*TRAIN_BUTTON_POS, delay=BUTTON_WAIT)     # không nhận ra nút: bấm chỗ nút
    elif plan.started >= plan.times:
        bot.record(f"{name}: trained {plan.started} batch(es), done")
        bot.mark_daily_done(key)
        return STOP
    else:
        plan.started += 1
        bot.log(f"{name}: Train batch {plan.started}/{plan.times}")
        bot.tap(*train, delay=BUTTON_WAIT)
    return HANDLED


def _find_training_speedup(bot, screen):
    """Tâm nút "Training Speedup" (có mẻ đang train) trên `screen`, hoặc None."""
    return bot.find(TRAINING_SPEEDUP, threshold=TRAINING_SPEEDUP_THRESHOLD, screen=screen,
                    region=TRAIN_BUTTON_REGION)


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


def _targets(troop: TroopTask) -> list[tuple[str, str]]:
    """Ảnh của nhiệm vụ: màn sau trước, màn trước sau; tab phụ "đang chọn" trước "chưa chọn"
    (hai ảnh khớp chéo). Hộp Finish All đè lên màn speedup (tiêu đề speedup vẫn khớp) nên
    xét trước. Tab Day đang chọn vẫn khớp khá cao ảnh "chưa chọn" -> xét sau tab phụ."""
    return [
        (FINISH_ALL_TITLE, ON_FINISH_ALL_DIALOG),
        (troop.speedup_title, ON_SPEEDUP),
        *[(path, ON_TRAIN_SCREEN) for path in _tier_paths(troop)],
        (SPEED_UP, ON_SPEED_UP_MENU),   # trước TRAIN: icon "View" của menu này khớp nhầm TRAIN
        (troop.menu_icon, ON_TRAIN_MENU),
        (troop.tab_selected, ON_TAB),
        (troop.tab, OPEN_TAB),
        (troop.day_tab, OPEN_DAY),
    ]


def _tier_paths(troop: TroopTask) -> list[str]:
    """Mọi ảnh vòng tròn cấp (một hoặc nhiều ảnh mỗi cấp)."""
    return [path for paths in troop.tiers.values()
            for path in ([paths] if isinstance(paths, str) else paths)]


def _regions(troop: TroopTask) -> dict[str, tuple]:
    return {path: TIER_ROW_REGION for path in _tier_paths(troop)}


def _thresholds(troop: TroopTask) -> dict[str, float]:
    return {
        **EVENT_THRESHOLDS,
        troop.menu_icon: TRAIN_THRESHOLD,
        SPEED_UP: TRAIN_THRESHOLD,
        **troop.thresholds,
        **{path: TIER_THRESHOLD for path in _tier_paths(troop)},
    }
