"""
run.py — "Refine Equipment" activity: tinh luyện 6 trang bị của một tướng. Xem FLOW.md.

Màn thành -> "•••" -> Generals -> (tích tim yêu thích, chọn tab loại tướng nếu cấu hình) -> tướng đầu tiên -> với từng ô trang bị đã chọn thuộc tính:
bấm ô -> hộp thông tin -> View -> General Equipment -> Refine -> màn Craft -> Refine -> màn Refine Equipment -> bấm Refine cho tới khi 4 dòng New đạt
yêu cầu (Confirm) hoặc hết số lần tối đa của trang bị đó (`max_refines`: 100 .. 1000 hoặc ALL; Cancel) -> Back về màn tướng -> ô kế.

Luật dừng (bot/ocr/read_refine_lines.py): chỉ tính các dòng đúng thuộc tính đã tích và đủ màu tối thiểu của thuộc tính đó; dừng + Confirm khi đủ `stop` (vd 3 Orange mà chỉ
tích Ground Troop Load = cả 3 dòng phải là Ground Troop Load màu cam trở lên; 2 Gold + 1 Orange = ít nhất 2 dòng vàng và ít nhất 3 dòng cam trở lên), hoặc dừng (Cancel) khi hết
`max_refines`. Dòng Original đã đủ thì không Refine. Chưa làm: Lock (TODO.md).
"""
import cv2

from ...city.city_map import EXIT_CANCEL, EXIT_DIALOG, EXIT_THRESHOLD, ensure_city
from ...common import go_home
from ..daily_activities.constants import MAIN_MORE
from ...ocr.read_refine_lines import LOCK_X, meets, read_new, read_original, satisfies
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
    LOCK_OFF,
    LOCK_ON,
    LOCK_SEARCH_REGION,
    LOCK_THRESHOLD,
    GENERAL_TYPE_KEY,
    GENERAL_WAIT_TRIES,
    GENERAL_TYPES,
    KEY,
    KIND_KEY,
    KINDS,
    DEFAULT_KIND,
    LINES_KEY,
    LOCK_KEY,
    MAX_LINES,
    MAX_REFINES_KEY,
    MAX_REFINES_OPTIONS,
    REFINES_ALL,
    DEFAULT_MAX_REFINES,
    EMPTY_SATURATION,
    MAX_STEPS,
    NO_GENERAL,
    NO_GENERAL_ANY,
    NO_GENERAL_THRESHOLD,
    MENU_GENERALS,
    MENU_WAIT_TRIES,
    NAME,
    READY,
    REFINE_BUTTON_TRIES,
    RESULT_WAIT_TRIES,
    WARN_BOX_FROM_LABEL,
    WARN_CONFIRM,
    WARN_LABEL,
    LOCK_VERIFY_TRIES,
    REFINE_BUTTON,
    REFINE_BUTTON_REGION,
    REFINE_BUTTON_THRESHOLD,
    REFINE_WAIT,
    SCREEN_WAIT,
    SLOTS,
    SLOTS_KEY,
    SLOT_TAP_TRIES,
    STABLE_TRIES,
    STATIC_DIFF,
    UNKNOWN_POPUP_CHECKS,
    stop_label,
    DEFAULT_STOP,
    STOP_KEY,
    STOP_OPTIONS,
    SLOT_HALF,
    STEP_WAIT,
    TYPE_TAB_Y,
    VIEW,
    VIEW_THRESHOLD,
    BUTTON_TAP_TRIES,
    CITY_RETURN_BACKS,
    SCREEN_WAIT_TRIES,
    VIEW_WAIT_TRIES,
)

CONFIRM_THRESHOLD = 0.9


def goals(settings: dict) -> dict[str, dict]:
    """{id ô trang bị: {"lines": [{"attribute", "color", "lock"}, ...], "max_refines": int | None, "stop": {"gold", "orange"}}} của các ô đã tích ít nhất
    một thuộc tính. Mỗi trang bị có 4 dòng tinh luyện, mỗi dòng ra ngẫu nhiên một trong nhiều thuộc tính, nên `lines` là các thuộc tính người dùng cần (tích
    bao nhiêu cũng được, mỗi thuộc tính một lần) kèm màu tối thiểu và Lock. `stop` là khi nào dừng + Confirm; `max_refines` là số lần Refine tối đa
    (None = ALL); cả hai CHO TỪNG TRANG BỊ."""
    chosen = {}
    for slot_id, _label, _pos, catalog in SLOTS:
        slot = (settings.get(SLOTS_KEY) or {}).get(slot_id) or {}
        lines = {}
        for line in slot.get(LINES_KEY) or []:
            name = line.get(ATTRIBUTE_KEY)
            if name in catalog and name not in lines:
                kind = line.get(KIND_KEY)
                lines[name] = {ATTRIBUTE_KEY: name, COLOR_KEY: line.get(COLOR_KEY) or DEFAULT_COLOR,
                               KIND_KEY: kind if kind in dict(KINDS) else DEFAULT_KIND, LOCK_KEY: bool(line.get(LOCK_KEY))}
        if lines:
            chosen[slot_id] = {LINES_KEY: list(lines.values()), MAX_REFINES_KEY: _limit(slot.get(MAX_REFINES_KEY)), STOP_KEY: _stop(slot.get(STOP_KEY))}
    return chosen


def _stop(value) -> dict:
    """Mức dừng của một trang bị: {"gold": g, "orange": o} (một trong STOP_OPTIONS); thiếu / lạ -> DEFAULT_STOP (1 vàng)."""
    pair = (value.get("gold"), value.get("orange")) if isinstance(value, dict) else None
    gold, orange = pair if pair in STOP_OPTIONS else DEFAULT_STOP
    return {"gold": gold, "orange": orange}


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
    if not _at_city(bot):
        return
    if not _open_general(bot, settings):
        return
    for slot_id, label, pos, catalog in SLOTS:
        if slot_id in chosen:
            bot.log(f"{NAME}: {label}: " + ", ".join(
                f"{line[ATTRIBUTE_KEY]} ({line[COLOR_KEY]}{', lock' if line[LOCK_KEY] else ''})" for line in chosen[slot_id][LINES_KEY]) + f"; max refines {chosen[slot_id][MAX_REFINES_KEY] or REFINES_ALL}; stop at {stop_label(**chosen[slot_id][STOP_KEY])}")
            if not _refine_slot(bot, label, pos, chosen[slot_id], catalog):
                break
    for _ in range(BACKS_TO_CITY):
        bot.back(delay=1)


def _at_city(bot) -> bool:
    """Về thành trước khi làm (như các activity khác): đang ở bản đồ thế giới thì bấm nút về thành (`ensure_city`); màn khác trong game (màn Refine, màn tướng, danh sách...) thì
    Back tới khi thấy nút ••• của màn thành, tối đa CITY_RETURN_BACKS lần; hộp hỏi thoát game thì Cancel; không Back khi màn thành đã sạch (Back lúc đó mở hộp thoát game).
    Không về được thành thì không tinh luyện (False)."""
    ensure_city(bot, NAME)
    backs = 0
    for _ in range(CITY_RETURN_BACKS * 2 + 1):       # mỗi lần Back kèm tối đa một lần Cancel hộp thoát game
        screen = bot.screenshot()
        if bot.find(EXIT_DIALOG, threshold=EXIT_THRESHOLD, screen=screen) is not None:
            cancel = bot.find(EXIT_CANCEL, threshold=EXIT_THRESHOLD, screen=screen)
            if cancel is not None:
                bot.tap(*cancel, delay=1)
                continue
        if bot.find(MAIN_MORE, screen=screen) is not None:
            return True
        if backs >= CITY_RETURN_BACKS:
            break
        bot.back(delay=1)
        backs += 1
    bot.record(f"{NAME}: not at the city screen, cannot go back to the city, not refining")
    return False


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
            if any(bot.find(image, threshold=NO_GENERAL_THRESHOLD) is not None for image in (NO_GENERAL, NO_GENERAL_ANY)):
                bot.record(f"{NAME}: the general list is empty (No favorite General / No General!), stop")
                _leave_list(bot)
                return False
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


def _leave_list(bot):
    """Danh sách Generals -> thành: Back tới khi thấy nút ••• (màn thành), tối đa BACKS_TO_CITY lần (Back thừa ở màn thành mở hộp thoát game)."""
    for _ in range(BACKS_TO_CITY):
        bot.back(delay=STEP_WAIT)
        if bot.find(FEATURES_ICON) is not None:
            return


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


def _refine_slot(bot, label: str, pos, goal: dict, catalog: tuple) -> bool:
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
    _wait_entry_state(bot)
    opened, closed = _lock_counts(bot)
    if opened == 0 and closed >= MAX_LINES:
        bot.record(f"{NAME}: {label}: all {closed} lines are locked, nothing to refine, skip")
        return _back_to_general(bot)
    pending = bot.find(CONFIRM, threshold=CONFIRM_THRESHOLD) is not None     # còn kết quả New treo từ lần trước (Cancel / Confirm hiện sẵn)
    unrefined = opened == 0 and closed == 0 and not pending     # không thấy ổ khoá nào mà cũng không có kết quả treo: chưa tinh luyện (những khoảng đen lớn)
    bot.log(f"{NAME}: {label}: {opened} unlocked, {closed} locked line(s)" + (", not refined yet" if unrefined else ""))
    _refine_until(bot, label, goal, catalog, unrefined)
    return _back_to_general(bot)


def _wait_image(bot, image: str, tries: int, threshold: float = 0.9, region=None):
    """Chờ 1 s rồi tìm `image` (trong `region` % màn hình nếu có), tối đa `tries` lần. Vị trí ảnh hoặc None."""
    for _ in range(tries):
        bot.sleep(1)
        pos = bot.find(image, threshold=threshold, region=region)
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


def _wait_entry_state(bot):
    """Vừa vào màn Refine Equipment: chờ tới khi màn hiện đủ, tức thấy nút Refine (màn bình thường) HOẶC Cancel / Confirm (còn kết quả New treo từ lần trước): chờ 1 s,
    tối đa SCREEN_WAIT_TRIES lần. Không chờ thì có thể phân loại nhầm lúc màn còn đang hiện (chưa thấy ổ khoá nào -> tưởng chưa tinh luyện)."""
    for attempt in range(SCREEN_WAIT_TRIES + 1):
        if attempt:
            bot.sleep(1)
        screen = bot.screenshot()
        if bot.find(REFINE_BUTTON, threshold=REFINE_BUTTON_THRESHOLD, region=REFINE_BUTTON_REGION, screen=screen) is not None:
            return
        if bot.find(CONFIRM, threshold=CONFIRM_THRESHOLD, screen=screen) is not None:
            return


def _lock_counts(bot) -> tuple[int, int]:
    """(số ổ khoá MỞ, số ổ khoá ĐÓNG) ở cột trái của màn Refine Equipment (LOCK_SEARCH_REGION). Tìm ổ khoá mở trước, không thấy mới đếm ổ khoá đóng."""
    screen = bot.screenshot()
    opened = len(bot.find_all(LOCK_OFF, threshold=LOCK_THRESHOLD, screen=screen, region=LOCK_SEARCH_REGION))
    if opened:
        return opened, 0
    return 0, len(bot.find_all(LOCK_ON, threshold=LOCK_THRESHOLD, screen=screen, region=LOCK_SEARCH_REGION))


def _slot_empty(bot, screen, pos) -> bool:
    """Ô trang bị (tâm `pos`, % màn hình) chưa mặc đồ: biểu tượng xám nên độ bão hòa trung bình thấp (< EMPTY_SATURATION)."""
    h, w = screen.shape[:2]
    x, y = int(w * pos[0] / 100), int(h * pos[1] / 100)
    area = screen[max(0, y - SLOT_HALF):y + SLOT_HALF, max(0, x - SLOT_HALF):x + SLOT_HALF]
    return float(cv2.cvtColor(area, cv2.COLOR_BGR2HSV)[..., 1].mean()) < EMPTY_SATURATION


def _back_to_general(bot) -> bool:
    """Back tới khi thấy màn tướng (tối đa BACKS_TO_GENERAL + 2 lần). Rời màn Refine khi còn kết quả New chưa Confirm / Cancel thì game có thể hỏi lại (hộp có ô "Don't show this
    again for today"): tích ô rồi Confirm (`_pass_warning`)."""
    for _ in range(BACKS_TO_GENERAL + 2):
        screen = bot.screenshot()
        if _pass_warning(bot, screen):
            continue
        if bot.find(ENHANCE, screen=screen) is not None and bot.find(VIEW, threshold=VIEW_THRESHOLD, screen=screen) is None:
            return True
        bot.back(delay=STEP_WAIT)
    bot.record(f"{NAME}: could not get back to the general screen")
    return False


def _read_stable(bot, screen, catalog) -> list[dict] | None:
    """4 dòng New đã ổn định: đọc `screen`, rồi chờ 1 s chụp đọc lại, tới khi hai lần đọc liên tiếp giống nhau (tên + màu + loại), tối đa STABLE_TRIES lần chờ thêm. Màn
    còn đang chuyển động ngay sau khi hiện Confirm có thể đọc lệch (đo 21913: tên "?" và màu cam thay vì vàng ở lần Refine đầu), và đọc lệch dẫn tới Confirm nhầm; không
    ổn định thì trả None (coi như chưa đạt: Cancel)."""
    def key(rows):
        return [(row["name"], row["color"], row["kind"]) for row in rows] if rows else None

    rows = read_new(screen, catalog)
    for _ in range(STABLE_TRIES):
        bot.sleep(1)
        again = read_new(bot.screenshot(), catalog)
        if key(again) == key(rows):
            return again
        rows = again
    bot.log(f"{NAME}: the new lines kept changing, treat as not reached")
    return None


def _unknown_gold(rows: list[dict] | None) -> bool:
    """Có dòng màu vàng mà không nhận ra tên (name None): không biết có phải dòng người dùng cần không."""
    return any(row["name"] is None and row["color"] == "gold" for row in rows or [])


def _all_locked(rows: list[dict] | None) -> bool:
    """Cả MAX_LINES dòng của khung Original đều đã khoá (ổ khoá đóng)."""
    return bool(rows) and len(rows) >= MAX_LINES and all(row["locked"] for row in rows)


def _lockable(rows: list[dict] | None, wanted: dict, lock_names: set) -> int:
    """Số dòng thuộc yêu cầu mà người dùng bật Lock trong `rows`."""
    return sum(1 for row in rows or [] if row["name"] in lock_names and satisfies(row, wanted))


def _lock_lines(bot, label: str, original: list[dict] | None, wanted: dict, lock_names: set, catalog: tuple) -> int | None:
    """Khung Original: bấm ổ khoá các dòng thuộc yêu cầu mà người dùng bật Lock và chưa khoá (ổ khoá ở (LOCK_X, y của dòng)), rồi đọc lại. Trả số dòng như vậy đã khoá
    (None nếu không đọc được khung Original). Không có dòng nào cần khoá thì không bấm gì."""
    if not lock_names:
        return 0
    if original is None:
        return None
    todo = [row for row in original if row["name"] in lock_names and satisfies(row, wanted) and row["locked"] is False]
    for row in todo:
        bot.tap(LOCK_X, row["y"], delay=1)
    if todo:
        ys = {row["y"] for row in todo}
        for _ in range(LOCK_VERIFY_TRIES):         # ổ khoá đổi màu chậm: đọc lại tới khi mọi dòng vừa bấm đã khoá
            bot.sleep(1)
            after = read_original(bot.screenshot(), catalog)
            if after is None:
                return None
            original = after
            if all(row["locked"] for row in after if row["y"] in ys):
                break
    locked = sum(1 for row in original if row["name"] in lock_names and satisfies(row, wanted) and row["locked"])
    if todo:
        bot.record(f"{NAME}: {label}: locked {len(todo)} wanted line(s), {locked} locked in total")
    return locked


def _brief(rows: list[dict] | None) -> str:
    """Log ngắn 4 dòng: "Ground Troop Load/gold/percent, ?/normal/flat, ..." ("?" = không nhận ra tên)."""
    return ", ".join(f"{row['name'] or '?'}/{row['color']}/{row['kind']}" for row in rows) if rows else "no result frame"


def _pass_warning(bot, screen) -> bool:
    """Hộp thoại có ô "Don't show this again for today" + Cancel / Confirm đang hiện: tích ô rồi Confirm. Có hai hộp như vậy: (1) khi bấm Refine mà còn dòng cao cấp
    chưa khoá ("You have unlocked high quality attribute(s)...") -> Confirm để Refine tiếp; (2) khi bấm Cancel ở kết quả mà dòng mới cao hơn dòng cũ ("The new
    attribute is higher than the old one...") -> Confirm = giữ dòng cũ. Cả hai dùng chung ảnh chữ và nút Confirm. True nếu đã bấm."""
    label = bot.find(WARN_LABEL, screen=screen)
    if label is None:
        return False
    dx, dy = WARN_BOX_FROM_LABEL
    bot.log(f"{NAME}: high quality warning, tick 'don't show again' and confirm")
    bot.tap(label[0] + dx, label[1] + dy, delay=1)
    confirm = bot.find(WARN_CONFIRM)
    if confirm is not None:
        bot.tap(*confirm, delay=STEP_WAIT)
    return True


def _is_static(before, after) -> bool:
    """Hai ảnh chụp liên tiếp giống nhau (màn đứng yên, không chuyển cảnh): độ lệch điểm ảnh trung bình < STATIC_DIFF."""
    return before is not None and before.shape == after.shape and float(cv2.absdiff(before, after).mean()) < STATIC_DIFF


def _stuck_popup(bot, screen, state: dict) -> bool:
    """Màn đứng yên mà không thấy nút Refine (`state` = {"previous": ảnh trước, "static": số lần đứng yên liên tiếp, "backs": số lần đã Back}): nghi hộp thoại lạ chặn màn. Sau
    UNKNOWN_POPUP_CHECKS lần kiểm tra thì bấm Back MỘT lần (chỉ một lần mỗi lần chờ, để Back không đẩy bot ra khỏi màn Refine). True nếu vừa bấm Back."""
    state["static"] = state["static"] + 1 if _is_static(state["previous"], screen) else 0
    state["previous"] = screen
    if state["static"] >= UNKNOWN_POPUP_CHECKS and state["backs"] == 0:
        bot.log(f"{NAME}: the screen is not changing and the Refine button is missing, press Back to close an unknown popup")
        bot.back(delay=STEP_WAIT)
        state.update(static=0, backs=1, previous=None)
        return True
    return False


def _wait_result(bot, catalog, unrefined: bool = False):
    """Sau khi bấm Refine: chờ 1 s rồi chụp, tối đa RESULT_WAIT_TRIES lần. Hộp cảnh báo thì bấm qua. Trả (ảnh, vị trí Confirm) khi thấy Confirm (kết quả New);
    (ảnh, None) nếu không có kết quả New: hết lần mà không thấy Confirm (caller bấm Refine lại), hoặc `unrefined` (trang bị chưa tinh luyện, chưa có khung Original) mà khung
    Original vừa hiện: lần Refine đầu áp thẳng dòng thành Original, không có Confirm nên khỏi chờ hết RESULT_WAIT_TRIES. Màn đứng yên mà không thấy nút Refine: hộp thoại lạ, Back."""
    screen = None
    state = {"previous": None, "static": 0, "backs": 0}
    for _ in range(RESULT_WAIT_TRIES):
        bot.sleep(1)
        screen = bot.screenshot()
        if _pass_warning(bot, screen):
            state.update(previous=None, static=0)
            continue
        confirm = bot.find(CONFIRM, threshold=CONFIRM_THRESHOLD, screen=screen)
        if confirm is not None:
            return screen, confirm
        if unrefined and read_original(screen, catalog) is not None:
            return screen, None
        if bot.find(REFINE_BUTTON, threshold=REFINE_BUTTON_THRESHOLD, region=REFINE_BUTTON_REGION, screen=screen) is None:
            _stuck_popup(bot, screen, state)
        else:
            state.update(previous=None, static=0)
    return screen, None


def _wait_refine_button(bot):
    """Chờ nút Refine giữa đáy (sau khi bấm Cancel / Confirm, hoặc đầu vòng): thấy ngay thì thôi, không thì chờ 1 s rồi tìm, tối đa REFINE_BUTTON_TRIES lần. Vị trí
    nút hoặc None. Bấm Cancel ở kết quả mà dòng mới "cao hơn dòng cũ" thì game hỏi "The new attribute is higher than the old one. Are you sure you want to maintain it?"
    (ô "Don't show this again for today" + Cancel / Confirm): tích ô rồi Confirm = giữ dòng cũ (đúng ý Cancel), nên mỗi lần chụp cũng bấm qua hộp đó (`_pass_warning`).
    Hộp thoại lạ khác: màn đứng yên qua UNKNOWN_POPUP_CHECKS lần kiểm tra mà vẫn không thấy nút Refine thì bấm Back một lần (`_stuck_popup`)."""
    state = {"previous": None, "static": 0, "backs": 0}
    for attempt in range(REFINE_BUTTON_TRIES + 1):
        if attempt:
            bot.sleep(1)
        screen = bot.screenshot()
        if _pass_warning(bot, screen):
            state.update(previous=None, static=0)
            continue
        pos = bot.find(REFINE_BUTTON, threshold=REFINE_BUTTON_THRESHOLD, region=REFINE_BUTTON_REGION, screen=screen)
        if pos is not None:
            return pos
        _stuck_popup(bot, screen, state)
    return None


def _refine_until(bot, label: str, goal: dict, catalog: tuple, unrefined: bool = False):
    """Màn Refine Equipment: khoá các dòng yêu cầu (bật Lock) đang có; dòng Original đã đủ mức dừng thì thôi; không thì bấm Refine, đọc 4 dòng New: đủ -> Confirm và
    dừng; có thêm dòng yêu cầu cần khoá -> Confirm rồi khoá dòng mới; còn lại -> Cancel, Refine tiếp. Tối đa `goal["max_refines"]` lần (None = tới khi đủ). Mỗi lần
    bấm Refine chờ nút Confirm 1 s x 10 lần rồi bấm lại; sau Cancel / Confirm chờ nút Refine 1 s x 10 lần."""
    stop = goal[STOP_KEY]
    need = (stop["gold"], stop["orange"])
    wanted = {line[ATTRIBUTE_KEY]: (line[COLOR_KEY], line[KIND_KEY]) for line in goal[LINES_KEY]}
    lock_names = {line[ATTRIBUTE_KEY] for line in goal[LINES_KEY] if line[LOCK_KEY]}
    locked = 0
    # Rời màn Refine mà chưa Cancel / Confirm (vd dừng vì dòng vàng lạ) thì khi quay lại trang bị đó kết quả New cũ vẫn còn, Cancel / Confirm hiện sẵn và không có nút Refine:
    # đọc kết quả đó và xử lý như một kết quả vừa ra (đủ -> Confirm, dòng vàng lạ -> dừng, còn lại -> Cancel).
    pending = bot.find(CONFIRM, threshold=CONFIRM_THRESHOLD)
    if not unrefined and pending is None:       # chưa tinh luyện thì chưa có dòng nào để khoá hay so: chỉ việc bấm Refine
        original = read_original(bot.screenshot(), catalog)
        locked = _lock_lines(bot, label, original, wanted, lock_names, catalog)
        if locked is None:
            locked = 0
        elif lock_names:
            original = read_original(bot.screenshot(), catalog)
        if _unknown_gold(original):
            bot.record(f"{NAME}: {label}: a gold line could not be identified {_brief(original)}, stop refining this equipment")
            return
        if meets(original, wanted, *need):
            bot.record(f"{NAME}: {label}: current lines already meet {stop_label(*need)} {_brief(original)}, nothing to refine")
            return
        if _all_locked(original):
            bot.record(f"{NAME}: {label}: all {MAX_LINES} lines are locked, nothing to refine, skip")
            return
    limit = goal[MAX_REFINES_KEY]
    tried = 0
    while pending is not None or limit is None or tried < limit:
        if pending is not None:              # kết quả treo: không bấm Refine, xử lý luôn kết quả đang hiện
            screen, confirm = bot.screenshot(), pending
            pending = None
        else:
            button = _wait_refine_button(bot)
            if button is None:
                bot.record(f"{NAME}: {label}: Refine button not found after {tried} refine(s)")
                return
            bot.tap(*button)
            tried += 1
            screen, confirm = _wait_result(bot, catalog, unrefined)
            unrefined = False
        if confirm is None:                  # không ra Confirm: lần đầu dòng áp thẳng thành Original, hoặc bấm không ăn -> vòng sau bấm Refine lại
            if meets(read_original(screen, catalog), wanted, *need):
                bot.record(f"{NAME}: {label}: lines meet {stop_label(*need)} after {tried} refine(s)")
                return
            continue
        new = _read_stable(bot, screen, catalog)
        if _unknown_gold(new):
            # Có dòng VÀNG mà không nhận ra là dòng nào: không đoán được có phải dòng cần không nên dừng trang bị này, chuyển trang bị khác (không bấm Cancel / Confirm: kết quả
            # còn nguyên cho người dùng xem, khi quay lại trang bị đó vẫn còn Cancel / Confirm). Dòng màu khác không nhận ra tên thì vẫn Cancel và tinh luyện bình thường.
            bot.record(f"{NAME}: {label}: a gold line could not be identified after {tried} refine(s) {_brief(new)}, stop refining this equipment")
            return
        if meets(new, wanted, *need):
            bot.tap(*confirm)
            _wait_refine_button(bot)
            bot.record(f"{NAME}: {label}: {stop_label(*need)} reached after {tried} refine(s) {_brief(new)}, confirmed")
            return
        if lock_names and _lockable(new, wanted, lock_names) > locked:       # có thêm dòng yêu cầu cần khoá: giữ kết quả rồi khoá dòng mới
            bot.tap(*confirm)
            bot.record(f"{NAME}: {label}: new wanted line after {tried} refine(s) {_brief(new)}, confirm and lock it")
            if _wait_refine_button(bot) is None:
                bot.record(f"{NAME}: {label}: Refine button not found after confirming")
                return
            original = read_original(bot.screenshot(), catalog)
            now = _lock_lines(bot, label, original, wanted, lock_names, catalog)
            if now is None:
                bot.record(f"{NAME}: {label}: cannot read the lines after confirming, stop")
                return
            locked = now
            after = read_original(bot.screenshot(), catalog)
            if meets(after, wanted, *need):
                bot.record(f"{NAME}: {label}: lines meet {stop_label(*need)} after {tried} refine(s)")
                return
            if _all_locked(after):             # khoá hết 4 dòng thì không Refine được nữa (nút Refine xám): bỏ qua trang bị như bình thường
                bot.record(f"{NAME}: {label}: all {MAX_LINES} lines are locked after {tried} refine(s), skip")
                return
            continue
        cancel = bot.find(CANCEL)
        if cancel is None:
            bot.record(f"{NAME}: {label}: Cancel not found after {tried} refine(s)")
            return
        bot.log(f"{NAME}: {label}: refine {tried}: {_brief(new)}")
        bot.tap(*cancel)                     # nút Refine được chờ ở đầu vòng sau
    bot.record(f"{NAME}: {label}: {limit} refines without reaching {stop_label(*need)}")


def _enabled(settings: dict) -> bool:
    return READY and bool(goals(settings))


JOB = {"run": run, "enabled": _enabled}
