"""
run.py — Daily Activities "Resource Tax": handler các action riêng của nhiệm vụ (Chợ -> Tax).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Sau Go: Chợ ở giữa màn hình -> common bấm giữa -> menu Chợ, icon "Tax" -> màn Tax (4 dòng trên ->
dưới: Lúa / Gỗ / Đá / Sắt) -> tax_all thu theo group "City Tax" ở tab Daily Activities:
1. Loại tích Free trước: bấm Tax của dòng -> popup, ô số mặc định = số lượt free còn lại -> bấm "+"
   thêm n lần (số lần chọn, phần thêm tốn kim cương) -> Tax: thu hết free rồi cộng n, không đọc số free.
   Hết free (nút dòng thành kim cương) thì thu như loại thường.
2. Các loại còn lại có n > 0: popup -> chỉnh ô số về đúng n -> Tax. Ô số chỉnh bằng "+" / "−" theo
   chênh lệch với số OCR đọc được, đọc lại kiểm tra (SET_TRIES vòng).
Thu xong (hay lỗi giữa chừng) vẫn đánh dấu xong hôm nay (mark_daily_done) rồi Back tới khi màn Tax đóng:
không đi lại, tránh thu (tốn kim cương) hai lần.
Ảnh và phần nhận popup đóng / băng quà / hộp xác nhận kim cương dùng chung với King's Path City Tax.
"""
from ....ocr import read_tax_count
from ...event.kings_path.city_tax.constants import (
    CLOSE_BACKS,
    COUNT_BOX,
    MINUS_OFFSET,
    PLUS_OFFSET,
    POPUP,
    POPUP_TAX,
    ROW_TAX,
    SCREEN_WAIT,
    STEP_WAIT,
    TAX_ROWS,
    TAX_MENU,
    TAX_SCREEN,
    TAX_STEP_WAIT,
    TAX_WAIT,
)
from ...event.city_building import MARKET
from ...event.kings_path.building import open_building
from ...event.kings_path.city_tax.run import _popup_closed, _row_buttons
from ..common import Task, mark_task_done
from .constants import (
    ACTIONS,
    BACKS_AFTER_TAX,
    DONE_IMAGES,
    FOLDER,
    KEY,
    LABEL,
    SET_TRIES,
    TAX_DEFAULT,
    TAX_FREE_DEFAULT,
    TAX_FREE_KEY,
    TAX_KEY,
    TAX_RESOURCES,
)

ROW_FREE_DY = 10   # nút "Tax" (còn lượt free) lệch nút của dòng tối đa chừng này px theo y


def handle(bot, action, pos, screen):
    if action == "tax_menu":
        bot.tap(*pos, delay=4)
    elif action == "tax":
        return tax_all(bot)
    elif action == "popup":
        bot.back(delay=1)
    return False


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go (hai phiên bản giống nhau từ đây): Chợ ở giữa ->
    open_building (nhận ra / tự học ảnh công trình, menu "Tax") -> màn Tax -> tax_all. Thu xong (hay lỗi
    giữa chừng) vẫn đánh dấu xong hôm nay, như tax_all. False nếu không vào được màn Tax."""
    if not open_building(bot, LABEL, MARKET, TAX_MENU, TAX_SCREEN):
        return False
    tax_all(bot)
    mark_task_done(bot, TASK)
    return True


def tax_plan(bot) -> tuple[dict[str, int], str | None]:
    """(số lần mỗi loại, loại tích Free hoặc None) từ group "City Tax" của tab Daily Activities."""
    daily = (getattr(bot, "settings", None) or {}).get("Daily Activities", {})
    data = daily.get(TAX_KEY)
    if not isinstance(data, dict):
        data = {}
    counts = {}
    for name in TAX_RESOURCES:
        try:
            counts[name] = max(0, int(data.get(name, TAX_DEFAULT)))
        except (TypeError, ValueError):
            counts[name] = TAX_DEFAULT
    free = data.get(TAX_FREE_KEY, TAX_FREE_DEFAULT)
    return counts, free if free in TAX_RESOURCES else None


def tax_all(bot) -> bool:
    """Đang ở màn Tax: thu loại Free trước, rồi các loại có số lần > 0. Luôn True (xong hôm nay)."""
    counts, free = tax_plan(bot)
    plan = ([(free, counts[free], True)] if free else []) + [
        (name, counts[name], False) for name in TAX_RESOURCES if name != free and counts[name] > 0]
    if not plan:
        bot.log(f"{LABEL}: nothing selected in {TAX_KEY}, skipped")
    for name, count, use_free in plan:
        if not _tax_row(bot, TAX_RESOURCES.index(name), count, use_free):
            break
    # Đánh dấu ngay: lượt sau không vào màn Tax thu lại (tốn kim cương hai lần).
    bot.mark_daily_done(LABEL)
    # Back ngay sau Okay / băng quà có khi bị game bỏ qua -> Back tới khi màn Tax đóng.
    for _ in range(BACKS_AFTER_TAX):
        if bot.find(TAX_SCREEN) is None:
            break
        bot.back(delay=2)
    return True


def _tax_row(bot, row: int, count: int, use_free: bool) -> bool:
    """Dòng thứ `row` (0..3) trên màn Tax: Tax -> popup -> ô số = `count` (`use_free` và còn free: số
    mặc định + `count`) -> Tax. True: xong dòng (hay không có gì để thu); False: lỗi, dừng."""
    tag = f"{LABEL} [{TAX_RESOURCES[row]}]"
    buttons = _row_buttons(bot)
    if len(buttons) < TAX_ROWS:
        bot.record(f"{tag}: {len(buttons)} Tax buttons found, expected {TAX_ROWS}")
        return False
    use_free = use_free and any(abs(y - buttons[row][1]) <= ROW_FREE_DY
                                for _, y in bot.find_all(ROW_TAX))
    if not use_free and count == 0:
        bot.record(f"{tag}: no free tax left, skipped")
        return True
    bot.tap(*buttons[row], delay=TAX_STEP_WAIT)
    popup = bot.wait_for(POPUP, timeout=SCREEN_WAIT)
    if popup is None:
        bot.record(f"{tag}: Tax popup not shown")
        return False
    bot.sleep(TAX_STEP_WAIT)   # popup hiện hẳn rồi mới bấm
    if use_free:
        px, py = popup[0] + PLUS_OFFSET[0], popup[1] + PLUS_OFFSET[1]
        for _ in range(count):
            bot.tap(px, py, delay=STEP_WAIT)
        if count:
            bot.sleep(TAX_STEP_WAIT)   # ô số cập nhật xong rồi mới bấm Tax
        done = f"all free + {count}"
    elif _set_count(bot, popup, count):
        done = f"x{count}"
    else:
        bot.record(f"{tag}: cannot set count to {count}, not taxing")
        bot.back(delay=1)
        return False
    button = bot.find(POPUP_TAX)
    if button is None:
        bot.record(f"{tag}: popup Tax button not found")
        bot.back(delay=1)
        return False
    bot.tap(*button, delay=TAX_WAIT + TAX_STEP_WAIT)
    if not _popup_closed(bot, popup):
        bot.record(f"{tag}: Tax popup still open, back x{CLOSE_BACKS}")
        for _ in range(CLOSE_BACKS):
            bot.back(delay=1)
        return False
    if bot.wait_for(TAX_SCREEN, timeout=SCREEN_WAIT) is None:
        bot.record(f"{tag}: not back on Tax screen")
        return False
    bot.sleep(TAX_STEP_WAIT)   # màn Tax ổn định rồi mới tìm nút dòng sau
    bot.record(f"{tag}: taxed {done}")
    return True


def _read_count(bot, popup) -> int | None:
    """Số trong ô số của popup Tax (vị trí đo từ chữ "Cost" ở `popup`), hoặc None."""
    x, y = popup
    return read_tax_count(bot.crop(bot.screenshot(), x + COUNT_BOX[0], y + COUNT_BOX[1],
                                   COUNT_BOX[2], COUNT_BOX[3]))


def _set_count(bot, popup, target: int) -> bool:
    """Ô số popup Tax về đúng `target`: đọc (OCR) -> bấm "+" / "−" bù chênh lệch -> đọc lại."""
    x, y = popup
    for _ in range(SET_TRIES):
        now = _read_count(bot, popup)
        if now is None:
            return False
        if now == target:
            return True
        dx, dy = PLUS_OFFSET if now < target else MINUS_OFFSET
        for _ in range(abs(target - now)):
            bot.tap(x + dx, y + dy, delay=STEP_WAIT)
        bot.sleep(TAX_STEP_WAIT)   # game cập nhật ô số chậm
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
