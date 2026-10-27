"""
run.py — "Refine Equipment" activity: tinh luyện 6 trang bị của một tướng. Xem FLOW.md.

Màn thành -> "•••" -> Generals -> (tích tim yêu thích, chọn tab loại tướng nếu cấu hình) -> tướng đầu tiên -> với từng ô trang bị đã chọn thuộc tính:
bấm ô -> hộp thông tin -> View -> General Equipment -> Refine -> màn Craft -> Refine -> màn Refine Equipment -> bấm Refine cho tới khi 4 dòng New đạt
yêu cầu (Confirm) hoặc hết số lần tối đa của trang bị đó (`max_refines`: 100 .. 1000 hoặc ALL; Cancel) -> Back về màn tướng -> ô kế.

CHƯA XONG (TODO.md): đọc 4 dòng New (tên thuộc tính + màu) — `_judge`; tới khi có, READY = False và nhiệm vụ không vào danh sách của worker.
"""
import cv2

from ...common import go_home
from ..result import save_errors
from .constants import (
    ALL_TAB_X,
    ATTRIBUTE_KEY,
    BACKS_TO_CITY,
    BOX_FROM_LABEL,
    BOX_HALF,
    BOX_OFF,
    BOX_ON,
    BACKS_TO_GENERAL,
    CANCEL,
    COLOR_KEY,
    CONFIRM,
    CRAFT_REFINE,
    DEFAULT_COLOR,
    DEFAULT_GENERAL_TYPE,
    ENHANCE,
    EQUIPMENT_REFINE,
    EQUIPMENT_TITLE,
    EQUIPMENT_TITLE_THRESHOLD,
    FAVORITE_KEY,
    FAVORITE_OFF,
    FAVORITE_ON,
    FAVORITE_REGION,
    FAVORITE_THRESHOLD,
    FEATURES_ICON,
    FIRST_GENERAL,
    LABEL_GOLD,
    LABEL_ORANGE,
    LABEL_THRESHOLD,
    LOCK_OFF,
    LOCK_ON,
    LOCK_REGION,
    LOCK_THRESHOLD,
    GENERAL_TYPE_KEY,
    GENERAL_WAIT_TRIES,
    GENERAL_TYPES,
    KEY,
    LINES_KEY,
    LOCK_KEY,
    MAX_LINES,
    MAX_REFINES_KEY,
    MAX_REFINES_OPTIONS,
    REFINES_ALL,
    DEFAULT_MAX_REFINES,
    EMPTY_SATURATION,
    MAX_STEPS,
    MENU_GENERALS,
    MENU_WAIT_TRIES,
    NAME,
    READY,
    REFINE_BUTTON,
    REFINE_WAIT,
    SCREEN_WAIT,
    SLOTS,
    SLOTS_KEY,
    SLOT_TAP_TRIES,
    SLOT_HALF,
    STEP_WAIT,
    TYPE_TAB_Y,
    VIEW,
    VIEW_THRESHOLD,
    BUTTON_TAP_TRIES,
    SCREEN_WAIT_TRIES,
    VIEW_WAIT_TRIES,
)

CONFIRM_THRESHOLD = 0.9


def goals(settings: dict) -> dict[str, dict]:
    """{id ô trang bị: {"lines": [{"attribute", "color", "lock"}, ...], "max_refines": int | None}} của các ô đã thêm ít nhất một dòng cần có. Mỗi trang
    bị tối đa MAX_LINES dòng (4 dòng tinh luyện của game); mỗi dòng cần có là một thuộc tính trong danh mục của trang bị kèm màu tối thiểu, hai dòng
    có thể trùng thuộc tính; không cần đúng vị trí dòng. `max_refines` là số lần Refine tối đa CHO TỪNG TRANG BỊ; None = ALL."""
    chosen = {}
    for slot_id, _label, _pos, catalog in SLOTS:
        slot = (settings.get(SLOTS_KEY) or {}).get(slot_id) or {}
        lines = [{ATTRIBUTE_KEY: line[ATTRIBUTE_KEY], COLOR_KEY: line.get(COLOR_KEY) or DEFAULT_COLOR, LOCK_KEY: bool(line.get(LOCK_KEY))}
                 for line in slot.get(LINES_KEY) or [] if line.get(ATTRIBUTE_KEY) in catalog][:MAX_LINES]
        if lines:
            chosen[slot_id] = {LINES_KEY: lines, MAX_REFINES_KEY: _limit(slot.get(MAX_REFINES_KEY))}
    return chosen


def _limit(value) -> int | None:
    """Số lần Refine tối đa của một trang bị: 100 .. 1000 theo cấu hình, "ALL" -> None (không giới hạn), giá trị lạ -> mặc định."""
    if value == REFINES_ALL:
        return None
    return value if value in MAX_REFINES_OPTIONS else DEFAULT_MAX_REFINES


@save_errors(KEY)   # lỗi thì lưu `refine_equipment_error` vào DB
def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Refine Equipment" tab's config."""
    chosen = goals(settings)
    if not chosen:
        bot.log(f"{NAME}: no attribute chosen, nothing to do")
        return
    if not _open_general(bot, settings):
        return
    for slot_id, label, pos, _catalog in SLOTS:
        if slot_id in chosen:
            bot.log(f"{NAME}: {label}: " + ", ".join(
                f"{line[ATTRIBUTE_KEY]} ({line[COLOR_KEY]}{', lock' if line[LOCK_KEY] else ''})" for line in chosen[slot_id][LINES_KEY]) + f"; max refines {chosen[slot_id][MAX_REFINES_KEY] or REFINES_ALL}")
            if not _refine_slot(bot, label, pos, chosen[slot_id]):
                break
    for _ in range(BACKS_TO_CITY):
        bot.back(delay=1)


def _open_general(bot, settings: dict) -> bool:
    """Từ màn bất kỳ tới màn tướng đầu tiên của danh sách (đã lọc). True khi đang ở màn tướng."""
    filtered = False
    for _ in range(MAX_STEPS):
        screen = bot.screenshot()
        if bot.find(ENHANCE, screen=screen) is not None:
            return True
        if _on_list(bot, screen):
            if not filtered:
                _apply_filters(bot, settings, screen)
                filtered = True
            bot.tap_percent(*FIRST_GENERAL)
            _wait_enhance(bot)
            continue
        pos = bot.find(MENU_GENERALS, screen=screen)
        if pos is not None:
            bot.tap(*pos)
            _wait_general_screen(bot)
            continue
        pos = bot.find(FEATURES_ICON, screen=screen)
        if pos is not None:
            bot.tap(*pos, delay=STEP_WAIT)
        else:
            go_home(bot, screen)
            bot.sleep(STEP_WAIT)
    bot.record(f"{NAME}: general screen not reached")
    return False


def _wait_general_screen(bot):
    """Sau khi bấm icon Generals: chờ 1 s rồi kiểm tra đã vào danh sách Generals (tim lọc) hoặc màn tướng (Enhance) chưa, tối đa MENU_WAIT_TRIES lần."""
    for _ in range(MENU_WAIT_TRIES):
        bot.sleep(1)
        screen = bot.screenshot()
        if _on_list(bot, screen) or bot.find(ENHANCE, screen=screen) is not None:
            return


def _wait_enhance(bot):
    """Sau khi bấm tướng đầu tiên: chờ 1 s rồi kiểm tra đã sang màn tướng (nút Enhance) chưa, tối đa GENERAL_WAIT_TRIES lần."""
    for _ in range(GENERAL_WAIT_TRIES):
        bot.sleep(1)
        if bot.find(ENHANCE) is not None:
            return


def _heart(bot, screen):
    """("on" | "off", vị trí) của tim lọc yêu thích ở danh sách Generals, hoặc (None, None) nếu không phải màn danh sách."""
    for state, image in (("off", FAVORITE_OFF), ("on", FAVORITE_ON)):
        pos = bot.find(image, threshold=FAVORITE_THRESHOLD, screen=screen, region=FAVORITE_REGION)
        if pos is not None:
            return state, pos
    return None, None


def _on_list(bot, screen) -> bool:
    return _heart(bot, screen)[0] is not None


def _apply_filters(bot, settings: dict, screen):
    """Danh sách Generals: tim yêu thích theo cấu hình, rồi tab loại tướng."""
    state, pos = _heart(bot, screen)
    if (state == "on") != bool(settings.get(FAVORITE_KEY)):
        bot.tap(*pos, delay=STEP_WAIT)
    bot.tap_percent(ALL_TAB_X, TYPE_TAB_Y, delay=STEP_WAIT)   # về tab All trước: tab đang chọn làm các tab khác dịch chỗ
    general_type = settings.get(GENERAL_TYPE_KEY, DEFAULT_GENERAL_TYPE)
    for type_id, _label, x in GENERAL_TYPES:
        if type_id == general_type and type_id != DEFAULT_GENERAL_TYPE:
            bot.tap_percent(x, TYPE_TAB_Y, delay=STEP_WAIT)


def _refine_slot(bot, label: str, pos, goal: dict) -> bool:
    """Màn tướng -> ô trang bị -> View -> Refine -> Refine Equipment, tinh luyện, rồi Back về màn tướng. False nếu không về được màn tướng.
    Ô chưa mặc đồ thì bỏ qua, không bấm."""
    if _slot_empty(bot, bot.screenshot(), pos):
        bot.record(f"{NAME}: {label}: no equipment on this slot, skip")
        return True
    view = None
    for attempt in range(SLOT_TAP_TRIES):
        if attempt:
            if bot.find(ENHANCE) is None:      # đã sang màn khác (VD danh sách chọn đồ): không bấm lại, Back về màn tướng bên dưới
                break
            bot.log(f"{NAME}: {label}: View not shown, tap the slot again")
        bot.tap_percent(*pos)
        view = _wait_view(bot)
        if view is not None:
            break
    if view is None:
        bot.record(f"{NAME}: {label}: no equipment info box, skip")
        return _back_to_general(bot)      # bấm trúng màn khác (VD danh sách chọn đồ) thì Back về màn tướng
    # Mỗi lần chuyển màn: bấm nút, chờ 1 s tìm dấu hiệu của màn kế (tối đa SCREEN_WAIT_TRIES lần), không thấy thì bấm lại nút nếu nó còn hiện.
    equipment_refine = _tap_until(bot, label, "View", VIEW, VIEW_THRESHOLD, view, EQUIPMENT_REFINE, 0.9)
    if equipment_refine is None:
        bot.record(f"{NAME}: {label}: General Equipment screen not shown, skip")
        return _back_to_general(bot)
    craft_refine = _tap_until(bot, label, "Refine", EQUIPMENT_REFINE, 0.9, equipment_refine, CRAFT_REFINE, 0.9)
    if craft_refine is None:
        bot.record(f"{NAME}: {label}: Craft screen not shown, skip")
        return _back_to_general(bot)
    title = _tap_until(bot, label, "Craft Refine", CRAFT_REFINE, 0.9, craft_refine, EQUIPMENT_TITLE, EQUIPMENT_TITLE_THRESHOLD)
    if title is None:
        bot.record(f"{NAME}: {label}: Refine Equipment screen not shown, skip")
        return _back_to_general(bot)
    _read_lines(bot, label)
    _tick_attribute_box(bot, label, goal[LINES_KEY])
    if not READY:
        bot.record(f"{NAME}: {label}: reading the new lines is not implemented, not refining")
    else:
        _refine_until(bot, label, goal)
    return _back_to_general(bot)


def _wait_image(bot, image: str, tries: int, threshold: float = 0.9):
    """Chờ 1 s rồi tìm `image`, tối đa `tries` lần. Vị trí ảnh hoặc None."""
    for _ in range(tries):
        bot.sleep(1)
        pos = bot.find(image, threshold=threshold)
        if pos is not None:
            return pos
    return None


def _tap_until(bot, label: str, name: str, button: str, button_threshold: float, pos, appears: str, appears_threshold: float):
    """Bấm `button` (đang ở `pos`) rồi chờ 1 s tìm `appears` (dấu hiệu màn kế), tối đa SCREEN_WAIT_TRIES lần. Không thấy thì tìm lại `button`: còn
    hiện thì bấm lại (tối đa BUTTON_TAP_TRIES lần bấm), không còn thì thôi. Trả vị trí `appears` hoặc None."""
    for attempt in range(BUTTON_TAP_TRIES):
        if attempt:
            pos = bot.find(button, threshold=button_threshold)
            if pos is None:
                return None
            bot.log(f"{NAME}: {label}: next screen not shown, tap {name} again")
        bot.tap(*pos)
        found = _wait_image(bot, appears, SCREEN_WAIT_TRIES, appears_threshold)
        if found is not None:
            return found
    return None


def _wait_view(bot):
    """Sau khi bấm ô trang bị: chờ 1 s rồi tìm chữ View của hộp thông tin, tối đa VIEW_WAIT_TRIES lần. Vị trí View hoặc None."""
    return _wait_image(bot, VIEW, VIEW_WAIT_TRIES, VIEW_THRESHOLD)


def _read_lines(bot, label: str) -> list[bool]:
    """Màn Refine Equipment vừa mở: các dòng có sẵn (khung Original) từ trên xuống, True = đã khoá (ổ khoá vàng), False = chưa khoá (xám). Trang bị chưa
    tinh luyện không có dòng nào. Khoá + chưa khoá <= MAX_LINES."""
    screen = bot.screenshot()
    rows = [(y, True) for _x, y in bot.find_all(LOCK_ON, threshold=LOCK_THRESHOLD, screen=screen, region=LOCK_REGION)]
    rows += [(y, False) for _x, y in bot.find_all(LOCK_OFF, threshold=LOCK_THRESHOLD, screen=screen, region=LOCK_REGION)]
    locks = [locked for _y, locked in sorted(rows)][:MAX_LINES]
    bot.log(f"{NAME}: {label}: {len(locks)} existing line(s), {sum(locks)} locked, {len(locks) - sum(locks)} unlocked")
    return locks


def _tick_attribute_box(bot, label: str, lines: list[dict]):
    """Chọn ô cảnh báo của game: mọi dòng người dùng chọn đều màu vàng -> tích "Gold Attribute", ngược lại tích "Orange Attribute"; ô còn lại bỏ tích.
    Tích ô cần trước, rồi chụp lại mới bỏ tích ô kia nếu nó vẫn đang tích (đo 21913: tích ô này thì game tự bỏ tích ô kia, bấm cả hai theo một ảnh chụp
    sẽ tích lại ô vừa bị bỏ)."""
    gold = all(line[COLOR_KEY] == "gold" for line in lines)
    for image, wanted in ((LABEL_GOLD if gold else LABEL_ORANGE, True), (LABEL_ORANGE if gold else LABEL_GOLD, False)):
        screen = bot.screenshot()
        pos = bot.find(image, threshold=LABEL_THRESHOLD, screen=screen)
        if pos is None:
            bot.record(f"{NAME}: {label}: {image} not found, cannot set the attribute box")
            continue
        dx, dy = BOX_FROM_LABEL[image]
        x, y = pos[0] + dx, pos[1] + dy
        area = bot.crop(screen, x - BOX_HALF, y - BOX_HALF, 2 * BOX_HALF, 2 * BOX_HALF)
        if (bot.best_match(BOX_ON, screen=area)[0] > bot.best_match(BOX_OFF, screen=area)[0]) != wanted:
            bot.tap(x, y, delay=1)
    bot.log(f"{NAME}: {label}: attribute box {'Gold' if gold else 'Orange'} ticked")


def _slot_empty(bot, screen, pos) -> bool:
    """Ô trang bị (tâm `pos`, % màn hình) chưa mặc đồ: biểu tượng xám nên độ bão hòa trung bình thấp (< EMPTY_SATURATION)."""
    h, w = screen.shape[:2]
    x, y = int(w * pos[0] / 100), int(h * pos[1] / 100)
    area = screen[max(0, y - SLOT_HALF):y + SLOT_HALF, max(0, x - SLOT_HALF):x + SLOT_HALF]
    return float(cv2.cvtColor(area, cv2.COLOR_BGR2HSV)[..., 1].mean()) < EMPTY_SATURATION


def _back_to_general(bot) -> bool:
    """Back tới khi thấy màn tướng (tối đa BACKS_TO_GENERAL + 2 lần)."""
    for _ in range(BACKS_TO_GENERAL + 2):
        if bot.find(ENHANCE) is not None and bot.find(VIEW, threshold=VIEW_THRESHOLD) is None:
            return True
        bot.back(delay=STEP_WAIT)
    bot.record(f"{NAME}: could not get back to the general screen")
    return False


def _refine_until(bot, label: str, goal: dict):
    """Màn Refine Equipment: bấm Refine; có Confirm (kết quả New) thì `_judge`: đạt -> Confirm, không -> Cancel; tối đa `goal["max_refines"]` lần (None = tới khi đạt)."""
    limit = goal[MAX_REFINES_KEY]
    tried = 0
    while limit is None or tried < limit:
        tried += 1
        button = bot.wait_for(REFINE_BUTTON, timeout=SCREEN_WAIT)
        if button is None:
            bot.record(f"{NAME}: {label}: Refine button not found after {tried - 1} refine(s)")
            return
        bot.tap(*button, delay=STEP_WAIT)
        confirm = bot.wait_for(CONFIRM, timeout=REFINE_WAIT, threshold=CONFIRM_THRESHOLD)
        if confirm is None:
            continue        # lần đầu: dòng áp thẳng thành Original, chưa có New
        if _judge(bot, bot.screenshot(), goal[LINES_KEY]):
            bot.record(f"{NAME}: {label}: wanted lines after {tried} refine(s), confirm")
            bot.tap(*confirm, delay=STEP_WAIT)
            return
        cancel = bot.find(CANCEL)
        if cancel is not None:
            bot.tap(*cancel, delay=STEP_WAIT)
    bot.record(f"{NAME}: {label}: {limit} refines without the wanted lines")


def _judge(bot, screen, goal: list[dict]) -> bool:
    """4 dòng New có đủ các dòng của `goal` (mỗi dòng thuộc tính + màu tối thiểu riêng) không; dòng có `lock` thì khoá khi đã ra. TODO: chưa đọc được dòng (tên + màu chữ), nên luôn False."""
    return False


def _enabled(settings: dict) -> bool:
    return READY and bool(goals(settings))


JOB = {"run": run, "enabled": _enabled}
