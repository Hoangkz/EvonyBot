"""
run.py — "Refine Equipment" activity: tinh luyện 6 trang bị của một tướng. Xem FLOW.md.

Màn thành -> "•••" -> Generals -> (tích tim yêu thích, chọn tab loại tướng nếu cấu hình) -> tướng đầu tiên -> với từng ô trang bị đã chọn thuộc tính:
bấm ô -> hộp thông tin -> View -> General Equipment -> Refine -> màn Craft -> Refine -> màn Refine Equipment -> bấm Refine cho tới khi 4 dòng New đạt
yêu cầu (Confirm) hoặc hết MAX_REFINES lần (Cancel) -> Back về màn tướng -> ô kế.

CHƯA XONG (TODO.md): đọc 4 dòng New (tên thuộc tính + màu) — `_judge`; tới khi có, READY = False và nhiệm vụ không vào danh sách của worker.
"""
from ...common import go_home
from ..result import save_errors
from .constants import (
    ALL_TAB_X,
    ATTRIBUTE_KEY,
    BACKS_TO_CITY,
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
    GENERAL_TYPE_KEY,
    GENERAL_TYPES,
    KEY,
    LINES_KEY,
    LOCK_KEY,
    MAX_LINES,
    MAX_REFINES,
    MAX_STEPS,
    MENU_GENERALS,
    NAME,
    READY,
    REFINE_BUTTON,
    REFINE_WAIT,
    SCREEN_WAIT,
    SLOTS,
    SLOTS_KEY,
    STEP_WAIT,
    TYPE_TAB_Y,
    VIEW,
    VIEW_THRESHOLD,
)

CONFIRM_THRESHOLD = 0.9


def goals(settings: dict) -> dict[str, list[dict]]:
    """{id ô trang bị: [{"attribute", "color", "lock"}, ...]} của các ô đã chọn ít nhất một dòng (tối đa MAX_LINES, mỗi thuộc tính một lần)."""
    chosen = {}
    for slot_id, _label, _pos, catalog in SLOTS:
        saved = ((settings.get(SLOTS_KEY) or {}).get(slot_id) or {}).get(LINES_KEY) or []
        lines = {}
        for line in saved:
            name = line.get(ATTRIBUTE_KEY)
            if name in catalog and name not in lines and len(lines) < MAX_LINES:
                lines[name] = {ATTRIBUTE_KEY: name, COLOR_KEY: line.get(COLOR_KEY) or DEFAULT_COLOR, LOCK_KEY: bool(line.get(LOCK_KEY))}
        if lines:
            chosen[slot_id] = list(lines.values())
    return chosen


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
                f"{line[ATTRIBUTE_KEY]} ({line[COLOR_KEY]}{', lock' if line[LOCK_KEY] else ''})" for line in chosen[slot_id]))
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
            bot.tap_percent(*FIRST_GENERAL, delay=STEP_WAIT + 1)
            continue
        for image in (MENU_GENERALS, FEATURES_ICON):
            pos = bot.find(image, screen=screen)
            if pos is not None:
                bot.tap(*pos, delay=STEP_WAIT)
                break
        else:
            go_home(bot, screen)
            bot.sleep(STEP_WAIT)
    bot.record(f"{NAME}: general screen not reached")
    return False


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


def _refine_slot(bot, label: str, pos, goal: list[dict]) -> bool:
    """Màn tướng -> ô trang bị -> View -> Refine -> Refine Equipment, tinh luyện, rồi Back về màn tướng. False nếu không về được màn tướng."""
    bot.tap_percent(*pos, delay=STEP_WAIT)
    view = bot.wait_for(VIEW, timeout=SCREEN_WAIT, threshold=VIEW_THRESHOLD)
    if view is None:
        bot.record(f"{NAME}: {label}: no equipment info box (empty slot?), skip")
        return True
    for image, threshold in ((VIEW, VIEW_THRESHOLD), (EQUIPMENT_REFINE, 0.9), (CRAFT_REFINE, 0.9)):
        found = bot.wait_for(image, timeout=SCREEN_WAIT, threshold=threshold)
        if found is None:
            bot.record(f"{NAME}: {label}: {image} not shown, skip")
            return _back_to_general(bot)
        bot.tap(*found, delay=STEP_WAIT)
    if bot.wait_for(EQUIPMENT_TITLE, timeout=SCREEN_WAIT, threshold=EQUIPMENT_TITLE_THRESHOLD) is None:
        bot.record(f"{NAME}: {label}: Refine Equipment screen not shown, skip")
    elif not READY:
        bot.record(f"{NAME}: {label}: reading the new lines is not implemented, not refining")
    else:
        _refine_until(bot, label, goal)
    return _back_to_general(bot)


def _back_to_general(bot) -> bool:
    """Back tới khi thấy màn tướng (tối đa BACKS_TO_GENERAL + 2 lần)."""
    for _ in range(BACKS_TO_GENERAL + 2):
        if bot.find(ENHANCE) is not None and bot.find(VIEW, threshold=VIEW_THRESHOLD) is None:
            return True
        bot.back(delay=STEP_WAIT)
    bot.record(f"{NAME}: could not get back to the general screen")
    return False


def _refine_until(bot, label: str, goal: list[dict]):
    """Màn Refine Equipment: bấm Refine; có Confirm (kết quả New) thì `_judge`: đạt -> Confirm, không -> Cancel; tối đa MAX_REFINES lần."""
    for tried in range(1, MAX_REFINES + 1):
        button = bot.wait_for(REFINE_BUTTON, timeout=SCREEN_WAIT)
        if button is None:
            bot.record(f"{NAME}: {label}: Refine button not found after {tried - 1} refine(s)")
            return
        bot.tap(*button, delay=STEP_WAIT)
        confirm = bot.wait_for(CONFIRM, timeout=REFINE_WAIT, threshold=CONFIRM_THRESHOLD)
        if confirm is None:
            continue        # lần đầu: dòng áp thẳng thành Original, chưa có New
        if _judge(bot, bot.screenshot(), goal):
            bot.record(f"{NAME}: {label}: wanted lines after {tried} refine(s), confirm")
            bot.tap(*confirm, delay=STEP_WAIT)
            return
        cancel = bot.find(CANCEL)
        if cancel is not None:
            bot.tap(*cancel, delay=STEP_WAIT)
    bot.record(f"{NAME}: {label}: {MAX_REFINES} refines without the wanted lines")


def _judge(bot, screen, goal: list[dict]) -> bool:
    """4 dòng New có đủ các dòng của `goal` (mỗi dòng thuộc tính + màu tối thiểu riêng) không; dòng có `lock` thì khoá khi đã ra. TODO: chưa đọc được dòng (tên + màu chữ), nên luôn False."""
    return False


def _enabled(settings: dict) -> bool:
    return READY and bool(goals(settings))


JOB = {"run": run, "enabled": _enabled}
