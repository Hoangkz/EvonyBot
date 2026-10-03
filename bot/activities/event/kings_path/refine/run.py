"""
run.py — nhiệm vụ Refine Equipment (King's Path, Day 4): Day 4 -> tab phụ "Sharp Weapons" ->
OCR số đã refine ở dòng Go -> Go -> Lò rèn -> Craft -> tab Refine -> chọn món viền xanh -> bấm
Refine đủ số còn thiếu -> làm lại từ đầu (đọc lại số đã refine). Flow chung tới Go: xem
../path_task.py (OCR "a / b" trước khi bấm Go, đủ mục tiêu thì xong).

Sau Go (về thành, Lò rèn ở giữa):
1. Bấm giữa màn hình -> menu Lò rèn -> "Craft" (../building.py).
2. Màn Craft (mở ở tab Craft): tab "Refine" chưa chọn -> bấm; đang chọn -> sang bước 3.
3. Thanh trang bị ở dưới (loại đang mở, vào màn là Nhẫn): chọn món XANH bên trái nhất (ảnh mẫu
   Equipment/<loại>/blue*, rồi viền xanh theo màu);
   chưa thấy thì vuốt thanh sang trái tìm tiếp (tối đa ITEMS_SWIPES lần, dừng khi thanh không
   đổi). Cả thanh không có món xanh -> món TÍM bên trái nhất (Equipment/<loại>/purple*) ở chỗ
   đang dừng.
   Loại này không có cả xanh lẫn tím -> bấm vòng bên trái sang loại kế (nhẫn -> giày -> quần ->
   giáp -> mũ) rồi tìm lại; bấm mà vòng giữa không đổi (hết bên trái) vẫn chưa thấy -> Back,
   xong hôm nay.
4. Bấm nút "Refine" ở màn Craft -> màn "Refine Equipment": ô "Gold Attribute" / "Orange
   Attribute" đang tích -> bỏ tích; bấm "Refine" giữa đáy -> hiện thuộc tính New + Cancel / Confirm
   -> Cancel (giữ thuộc tính cũ); lặp tới đủ (mục tiêu - số đã refine) lần. Không thấy nút
   BUTTON_MISSES giây liền thì thôi.
5. Back 2 lần (về thành), trả AGAIN: đi lại từ màn chính -> King's Path -> Day 4 -> Sharp Weapons -> OCR lại ->
   đủ thì xong, chưa thì Go lần nữa. Số đã refine không tăng sau một lượt bấm (VD hết nguyên
   liệu) -> xong hôm nay, mai làm tiếp.
Không đọc được số đã refine ở dòng Go thì không refine (không biết cần bấm bao nhiêu lần).
"""
import cv2
import numpy as np

from ...common import EventState
from .. import path_task
from ..building import open_menu
from .constants import (
    BLUE_HUE,
    BLUE_MIN_S,
    BLUE_MIN_V,
    BLUE_ITEMS,
    ACTIVE_HALF,
    ACTIVE_THRESHOLD,
    BOX_HALF,
    BOX_OFF,
    BOX_ON,
    BUTTON_MISSES,
    CANCEL,
    CRAFT_TITLE,
    DISABLED_LEFT_POS,
    EQUIPMENT_ACTIVE,
    ACTIVE_POS,
    DAY,
    EQUIPMENT_REFINE,
    EQUIPMENT_STEPS,
    EQUIPMENT_TITLE,
    ITEM_MIN,
    ITEM_THRESHOLD,
    ITEM_WAIT,
    ITEMS_REGION,
    ITEMS_SAME,
    ITEMS_SWIPE,
    ITEMS_SWIPE_WAIT,
    ITEMS_SWIPES,
    ITEMS_Y,
    KEY,
    LAST_TYPE,
    LABEL_THRESHOLD,
    LABELS,
    MENU_CRAFT,
    PURPLE_ITEMS,
    REFINE_BUTTON,
    REFINE_REGION,
    REFINE_WAIT,
    STEP_WAIT,
    SCREEN_STEPS,
    TAB,
    TAB_INDEX,
    TAB_REFINE,
    TAB_REFINE_REGION,
    TAB_REFINE_SELECTED,
    TAB_REFINE_THRESHOLD,
    TAB_SELECTED,
    TAB_WAIT,
    TYPE_CHECKS,
    TYPE_SAME,
    TYPE_SWITCHES,
    TYPE_WAIT,
)

NAME = "Refine"

# Số đã refine lúc bấm lượt trước, theo thiết bị (id(bot)): lượt sau đọc ra vẫn bằng số này
# -> bấm Refine không ăn (hết nguyên liệu / vàng) -> dừng, khỏi lặp AGAIN mãi.
_last_done: dict[int, int] = {}

# _find_item: bấm sang loại khác mà vòng giữa không đổi sau TYPE_CHECKS lần kiểm tra (đã Back).
STUCK = "stuck"


def blue_items(screen) -> list[tuple[int, int]]:
    """Tâm các món viền xanh trên hàng trang bị, trái -> phải."""
    y0, y1 = ITEMS_Y
    hsv = cv2.cvtColor(screen[y0:y1], cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mask = ((hue >= BLUE_HUE[0]) & (hue <= BLUE_HUE[1]) & (sat > BLUE_MIN_S)
            & (val > BLUE_MIN_V)).astype(np.uint8)
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    items = [(int(x + w / 2), int(y0 + y + h / 2))
             for x, y, w, h, _ in stats[1:count] if w >= ITEM_MIN and h >= ITEM_MIN]
    return sorted(items)


def _find_items(bot, screen, templates: list[str]) -> list[tuple[int, int]]:
    """Tâm các món khớp một trong `templates` trên thanh trang bị, trái -> phải."""
    found = []
    for template in templates:
        found += bot.find_all(template, threshold=ITEM_THRESHOLD, screen=screen, region=ITEMS_REGION)
    return sorted(found)


def _find_item(bot) -> tuple[tuple[int, int], str] | None:
    """(vị trí, màu) món sẽ refine: tìm trong loại đang mở (_find_item_in_type); không có thì bấm
    vòng bên trái sang loại kế rồi tìm lại, tới khi thấy hoặc tới mũ (LAST_TYPE, loại cuối) / hết
    bên trái -> None. Bấm sang loại khác mà vòng giữa không đổi (TYPE_CHECKS lần) -> Back, STUCK."""
    x, y = ACTIVE_POS
    for _ in range(TYPE_SWITCHES + 1):
        screen = bot.screenshot()
        kind = _active_type(bot, screen) or "?"
        found = _find_item_in_type(bot)
        if found is not None:
            return found
        if kind == LAST_TYPE:
            bot.log(f"{NAME}: {kind}: no blue / purple, last type")
            return None
        before = bot.crop(screen, x - ACTIVE_HALF, y - ACTIVE_HALF, 2 * ACTIVE_HALF, 2 * ACTIVE_HALF)
        bot.log(f"{NAME}: {kind}: no blue / purple, tap left type")
        bot.tap(*DISABLED_LEFT_POS, delay=TYPE_WAIT)
        if not _type_changed(bot, before):
            bot.record(f"{NAME}: equipment type still {kind} after {TYPE_CHECKS} checks, back")
            bot.back(delay=STEP_WAIT)
            return STUCK
    return None


def _type_changed(bot, before) -> bool:
    """Vòng giữa (ô quanh ACTIVE_POS) đã khác `before` chưa: kiểm tra, chưa đổi thì chờ 1 s rồi
    kiểm tra lại, tối đa TYPE_CHECKS lần."""
    x, y = ACTIVE_POS
    for _ in range(TYPE_CHECKS):
        after = bot.crop(bot.screenshot(), x - ACTIVE_HALF, y - ACTIVE_HALF, 2 * ACTIVE_HALF, 2 * ACTIVE_HALF)
        if bot.best_match(before, screen=after)[0] < TYPE_SAME:
            return True
        bot.sleep(1)
    return False


def _active_type(bot, screen) -> str | None:
    """Loại trang bị đang mở (vòng giữa): ảnh active.png khớp cao nhất, hoặc None."""
    x, y = ACTIVE_POS
    area = bot.crop(screen, x - 30, y - 30, 60, 60)
    scores = {kind: bot.best_match(icon, screen=area)[0] for kind, icon in EQUIPMENT_ACTIVE.items()}
    kind = max(scores, key=scores.get, default=None)
    return kind if kind is not None and scores[kind] >= ACTIVE_THRESHOLD else None


def _find_item_in_type(bot) -> tuple[tuple[int, int], str] | None:
    """(vị trí, màu) món sẽ refine trong loại đang mở: xanh trái nhất (ảnh mẫu, rồi theo màu viền);
    chưa thấy thì vuốt thanh sang trái tìm tiếp. Cả thanh không có món xanh -> món tím trái nhất ở
    màn đang dừng."""
    y0, y1 = ITEMS_Y
    previous = screen = None
    for swipes in range(ITEMS_SWIPES + 1):
        screen = bot.screenshot()
        items = _find_items(bot, screen, BLUE_ITEMS) or blue_items(screen)
        if items:
            return items[0], "blue"
        row = screen[y0:y1].astype(np.int16)
        if previous is not None and np.abs(row - previous).mean() < ITEMS_SAME:
            break   # vuốt mà thanh không đổi: đã tới cuối thanh
        previous = row
        if swipes < ITEMS_SWIPES:
            bot.swipe_percent(*ITEMS_SWIPE, delay=ITEMS_SWIPE_WAIT)
    items = _find_items(bot, screen, PURPLE_ITEMS)
    return (items[0], "purple") if items else None


def _open_refine_tab(bot) -> bool:
    """Chờ màn Craft, bấm tab Refine nếu chưa chọn. True nếu đang ở tab Refine."""
    for _ in range(SCREEN_STEPS):
        screen = bot.screenshot()
        if bot.find(CRAFT_TITLE, screen=screen) is not None:
            if bot.find(TAB_REFINE_SELECTED, threshold=TAB_REFINE_THRESHOLD, screen=screen,
                        region=TAB_REFINE_REGION) is not None:
                return True
            pos = bot.find(TAB_REFINE, threshold=TAB_REFINE_THRESHOLD, screen=screen,
                           region=TAB_REFINE_REGION)
            if pos is not None:
                bot.tap(*pos, delay=TAB_WAIT)
                continue
        bot.sleep(1)
    bot.record(f"{NAME}: Refine tab not shown")
    return False


def _refine(bot, path, done, target):
    """Sau Go: Lò rèn -> Craft -> tab Refine -> món xanh -> bấm Refine (target - done) lần."""
    if done is None:
        bot.record(f"{NAME}: progress unknown, not refining")
        return None
    if _last_done.get(id(bot)) == done:
        bot.record(f"{NAME}: progress still {done} after refining, done for today")
        _last_done.pop(id(bot), None)
        bot.mark_daily_done(path.key)
        return None
    _, pos = open_menu(bot, NAME, {"craft": MENU_CRAFT})
    if pos is None:
        return None
    bot.tap(*pos, delay=STEP_WAIT)
    if not _open_refine_tab(bot):
        return None
    found = _find_item(bot)
    if found == STUCK:
        return None   # đã Back, không lưu done: lượt sau làm lại
    if found is None:
        bot.record(f"{NAME}: ERROR no blue / purple equipment found (ring -> helmet), "
                   f"done for today, retry tomorrow")
        bot.back(delay=STEP_WAIT)
        bot.mark_daily_done(path.key)
        return None
    item, color = found
    bot.log(f"{NAME}: {color} equipment at {item}")
    bot.tap(*item, delay=ITEM_WAIT)
    need = target - done
    bot.record(f"{NAME}: refine {need} time(s) (done {done}, target {target})")
    if _open_equipment(bot):
        _refine_times(bot, need)
    _last_done[id(bot)] = done
    bot.back(delay=STEP_WAIT)
    bot.back(delay=STEP_WAIT)
    return path_task.AGAIN


def _open_equipment(bot) -> bool:
    """Màn Craft (tab Refine, đã chọn món): bấm nút Refine -> chờ màn "Refine Equipment"."""
    for _ in range(EQUIPMENT_STEPS):
        screen = bot.screenshot()
        if bot.find(EQUIPMENT_TITLE, screen=screen) is not None:
            return True
        button = bot.find(REFINE_BUTTON, screen=screen, region=REFINE_REGION)
        if button is not None:
            bot.tap(*button, delay=REFINE_WAIT)
            continue
        bot.sleep(1)
    bot.record(f"{NAME}: Refine Equipment screen not shown")
    return False


def _refine_times(bot, need: int):
    """Màn Refine Equipment: bỏ tích ô Gold / Orange, bấm Refine rồi Cancel, `need` lần."""
    tapped, misses = 0, 0
    while True:
        screen = bot.screenshot()
        if bot.find(EQUIPMENT_TITLE, screen=screen) is None:
            bot.record(f"{NAME}: left Refine Equipment screen after {tapped} time(s)")
            return
        cancel = bot.find(CANCEL, screen=screen)
        if cancel is not None:   # vừa Refine: bỏ thuộc tính mới
            bot.tap(*cancel, delay=REFINE_WAIT)
            continue
        if tapped >= need:
            bot.log(f"{NAME}: refined {tapped} time(s)")
            return
        if _untick_boxes(bot, screen):
            continue
        button = bot.find(EQUIPMENT_REFINE, screen=screen)
        if button is None:
            misses += 1
            if misses >= BUTTON_MISSES:
                bot.record(f"{NAME}: Refine button not found after {tapped} time(s)")
                return
            bot.sleep(1)
            continue
        misses = 0
        bot.tap(*button, delay=REFINE_WAIT)
        tapped += 1


def _untick_boxes(bot, screen) -> bool:
    """Ô "Gold Attribute" / "Orange Attribute" đang tích (giống boxOn hơn boxOff) -> bấm bỏ tích.
    True nếu đã bấm (chụp lại rồi xét tiếp)."""
    for label, (dx, dy) in LABELS.items():
        pos = bot.find(label, threshold=LABEL_THRESHOLD, screen=screen)
        if pos is None:
            continue
        x, y = pos[0] + dx, pos[1] + dy
        area = bot.crop(screen, x - BOX_HALF, y - BOX_HALF, 2 * BOX_HALF, 2 * BOX_HALF)
        if bot.best_match(BOX_ON, screen=area)[0] > bot.best_match(BOX_OFF, screen=area)[0]:
            bot.log(f"{NAME}: untick box at {(x, y)}")
            bot.tap(x, y, delay=STEP_WAIT)
            return True
    return False


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB, after_go=_refine,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
