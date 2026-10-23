"""
run.py — "Gather Resources" activity: gửi từng đội quân (mỗi dòng ở tab một đội) đi thu thập mỏ đã chọn ở tab. Xem FLOW.md.

Cấu hình (tab Gather Resources): {"squads": [{"resource": "food", "level": 10}, ...]}; đội n = dòng thứ n.

Mỗi đội: ra bản đồ thế giới -> kính lúp -> chọn loại mỏ -> chỉnh cấp (đọc ô số, bấm "+" / "−" đúng chênh lệch) -> tích "Only
search ... full resources" -> Search -> mỏ được kéo vào giữa, menu tròn mở -> Occupy -> màn March: đọc giờ thu thập và giờ đi,
bấm March luôn (quân / tướng do game chọn sẵn, không chọn preset). Lưu giờ đội về (bây giờ + đi + thu thập + về) vào DB; tới giờ đó worker gọi lại để gửi đội đi tiếp.
Nút March xám (hết lính) thì dừng, mọi đội chờ NO_TROOP_WAIT; game báo hết đường march thì dừng, mọi đội chờ MARCH_FULL_WAIT;
worker chuyển sang việc khác.
"""
import time

from ...common import delay, go_home
from ...common.go_home import EXIT_DIALOG, EXIT_THRESHOLD
from ...ocr.read_march_time import run as read_march_time
from ...ocr.read_level import run as read_level
from ..result import save_errors
from .constants import (AFTER_OCCUPY_TRIES, AFTER_OCCUPY_WAIT, BUTTON_THRESHOLD, CITY_MENU, FAIL_WAIT, FREE_MARGIN, FREE_PREFIX, GATHER_TIME, KEY, LEVEL_BOX,
                        LEVEL_MAX_TAPS, LEVEL_READ_TRIES, LEVEL_STUCK, LEVEL_TAP_WAIT, MARCH_BAR, MARCH_BUTTON, MARCH_FULL,
                        MARCH_FULL_WAIT, MARCH_TIME, MARCH_TITLE, MAX_TROOP, MENU, MENU_SETTLE, MINUS, NO_TARGET,
                        NO_TARGET_THRESHOLD, NO_TROOP_BACKS, NO_TROOP_WAIT, NO_TROOPS, OCCUPY, OCCUPY_TRIES, PANEL, PLUS, RESOURCES, SEARCH_BUTTON,
                        SEARCH_ICON, SEARCH_TRIES, SEND_TRIES, SQUADS_KEY, TARGET_TAKEN, THRESHOLD, TO_WORLD_TAP, TO_WORLD_TRIES,
                        TYPE_FLING_TIME, TYPE_FLING_TO_START, TYPE_FLINGS, TYPE_ICON_UP, TYPE_LABEL, TYPE_MAX_STEPS, TYPE_ROW,
                        TYPE_SWIPE_TIME, TYPE_SWIPE_TO_END, TYPE_SWIPE_TO_START, TYPE_THRESHOLD, UNCHECKED, WAIT_INTERVAL, WAIT_TRIES)


class _Stop(Exception):
    """Không gửi thêm đội nào được trong lượt này: mọi đội đến hạn chờ `wait` giây."""

    def __init__(self, reason: str, wait: int):
        super().__init__(reason)
        self.reason, self.wait = reason, wait


def _out_of_troops() -> _Stop:      # nút March xám: thành hết lính
    return _Stop("hết lính", NO_TROOP_WAIT)


def squads(settings: dict) -> list[dict]:
    """Các dòng cấu hình, mỗi dòng một đội; "troop" = số thứ tự dòng (1..), dùng làm khoá giờ rảnh trong DB."""
    rows = [s for s in settings.get(SQUADS_KEY) or [] if s.get("resource")][:MAX_TROOP]
    return [{**s, "troop": n} for n, s in enumerate(rows, 1)]


# ---- giờ đội rảnh (DB) ----
def free_at(bot, troop: int) -> float | None:
    """Giờ (epoch giây) đội `troop` rảnh, None nếu chưa gửi lần nào."""
    prefix = FREE_PREFIX.format(troop=troop)
    times = [int(key[len(prefix):]) for key in bot.daily_keys() if key.startswith(prefix) and key[len(prefix):].isdigit()]
    return max(times) if times else None


def set_free_at(bot, troop: int, when: float):
    prefix = FREE_PREFIX.format(troop=troop)
    for key in bot.daily_keys():
        if key.startswith(prefix):
            bot.forget_daily(key)
    bot.mark_daily_done(f"{prefix}{int(when)}")


def due_squads(bot, settings: dict) -> list[dict]:
    """Các đội đã tới giờ rảnh (hoặc chưa gửi lần nào)."""
    now = time.time()
    return [s for s in squads(settings) if (free_at(bot, s["troop"]) or 0) <= now]


# ---- luồng ----
@save_errors(KEY)   # lỗi thì lưu `gather_resources_error` vào DB
def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Gather Resources" tab's config. Gửi mọi đội đã tới giờ."""
    pending = due_squads(bot, settings)
    if not pending:
        return
    if not _to_world(bot):
        bot.log("Gather Resources: không ra được bản đồ thế giới, lượt sau thử lại")
        return
    for squad in pending:
        troop = squad["troop"]
        try:
            seconds = _send(bot, squad["resource"], int(squad.get("level") or 1), troop)
        except _Stop as stop:
            bot.record(f"Gather Resources: {stop.reason}, chờ {stop.wait // 60} phút")
            for s in squads(settings):
                if (free_at(bot, s["troop"]) or 0) <= time.time():
                    set_free_at(bot, s["troop"], time.time() + stop.wait)
            return
        if seconds is None:
            bot.record(f"Gather Resources: không gửi được Troop {troop}, thử lại sau {FAIL_WAIT // 60} phút")
            set_free_at(bot, troop, time.time() + FAIL_WAIT)
            continue
        bot.record(f"Gather Resources: Troop {troop} đi thu thập {squad['resource']} Lv {squad.get('level')}, "
                   f"về sau {seconds // 60} phút")


def _send(bot, resource: str, level: int, troop: int) -> int | None:
    """Gửi một đội. Trả số giây tới lúc đội về, None nếu không gửi được; ném _Stop khi hết lính / hết đường march."""
    for _ in range(SEND_TRIES):
        if not _open_search(bot) or not _pick_type(bot, resource):
            return None
        if not _set_level(bot, level):
            return None
        box = bot.find(UNCHECKED, threshold=0.9, region=PANEL)
        if box is not None:
            bot.tap(*box)
            delay(bot, 1)
        result = _occupy(bot, resource)
        if result == MARCH:
            return _march(bot, troop)
        if result == NOT_FOUND:
            return None
    return None      # Occupy mà không sang màn March (bấm trượt khi menu còn trượt...): đã thử lại cả lượt


def _to_world(bot) -> bool:
    """Tới bản đồ thế giới: thấy kính lúp (hoặc bảng Search đang mở) là xong. Màn March còn mở (lượt trước bị ngắt) thì Back;
    màn thành sạch (có "•••", không kính lúp, không hộp "thoát game") thì bấm quả địa cầu góc dưới phải; màn khác (popup, hộp
    thoát game, launcher, ...) thì go_home (Back / Cancel / mở game). Không bấm mù góc dưới phải khi chưa chắc ở màn thành: ở màn March đó là nút March, ở popup là vật phẩm."""
    for _ in range(TO_WORLD_TRIES):
        screen = bot.screenshot()
        if (bot.find(SEARCH_ICON, threshold=THRESHOLD, screen=screen) is not None
                or bot.find(SEARCH_BUTTON, threshold=THRESHOLD, screen=screen, region=PANEL) is not None):
            return True
        if bot.find(MARCH_TITLE, threshold=THRESHOLD, screen=screen) is not None:
            bot.back()
        elif (bot.find(EXIT_DIALOG, threshold=EXIT_THRESHOLD, screen=screen) is None
              and bot.find(CITY_MENU, threshold=THRESHOLD, screen=screen) is not None):
            bot.tap_percent(*TO_WORLD_TAP)
            _wait_for(bot, SEARCH_ICON)
            continue
        else:
            go_home(bot, screen)
        delay(bot, 2)
    return False


def _open_search(bot) -> bool:
    """Bấm kính lúp tới khi bảng Search hiện (thấy nút Search)."""
    for _ in range(SEARCH_TRIES):
        screen = bot.screenshot()
        if bot.find(SEARCH_BUTTON, threshold=THRESHOLD, screen=screen, region=PANEL) is not None:
            return True
        icon = bot.find(SEARCH_ICON, threshold=THRESHOLD, screen=screen)
        if icon is None:
            if not _to_world(bot):
                return False
            continue
        bot.tap(*icon)
        if _wait_for(bot, SEARCH_BUTTON) is not None:
            return True
    return False


def _pick_type(bot, resource: str) -> bool:
    """Bấm loại mỏ ở hàng chọn (Summon, Monster, Terminator, Farm, Sawmill, Quarry, Iron Mine, Gems Mine, quái...). Mỗi bước chụp
    một ảnh: thấy loại cần tìm thì bấm. Thấy loại mỏ khác thì so thứ tự lúa, gỗ, đá, sắt, gem: cần loại nằm trước (VD thấy sắt, cần
    lúa) thì kéo chậm sang trái, nằm sau (VD thấy lúa, cần gem) thì kéo chậm sang phải. Không thấy loại mỏ nào (đang ở nhóm quái
    cuối hàng) thì kéo dài một cú về đầu hàng."""
    order = [r for r, _ in RESOURCES]
    target = order.index(resource)
    for _ in range(TYPE_MAX_STEPS + 1):
        screen = bot.screenshot()
        seen = [i for i, r in enumerate(order)
                if bot.find(TYPE_LABEL.format(resource=r), threshold=TYPE_THRESHOLD, screen=screen, region=TYPE_ROW) is not None]
        if target in seen:
            pos = bot.find(TYPE_LABEL.format(resource=resource), threshold=TYPE_THRESHOLD, screen=screen, region=TYPE_ROW)
            height = bot.window_size()[1]
            bot.tap(pos[0], pos[1] - int(height * TYPE_ICON_UP / 100))
            delay(bot, 1.5)
            return True
        if not seen:
            _fling_to_start(bot)
        elif target < min(seen):
            bot.swipe_percent(*TYPE_SWIPE_TO_START, duration=TYPE_SWIPE_TIME)
            delay(bot, 1)
        else:      # nằm sau các loại đang thấy (hoặc giữa: chữ bị cắt ở mép) -> sang phải
            bot.swipe_percent(*TYPE_SWIPE_TO_END, duration=TYPE_SWIPE_TIME)
            delay(bot, 1)
    bot.log(f"Gather Resources: không thấy loại {resource} ở bảng Search")
    return False


def _fling_to_start(bot):
    """Kéo nhanh hàng loại về đầu hàng (Summon .. Farm)."""
    for _ in range(TYPE_FLINGS):
        bot.swipe_percent(*TYPE_FLING_TO_START, duration=TYPE_FLING_TIME)
        delay(bot, 1)


def _set_level(bot, level: int) -> bool:
    """Chỉnh cấp bằng OCR ô số bên phải nút "+": mỗi lần bấm "+" / "−" MỘT cái rồi chụp đọc lại, đúng cấp thì dừng (không bấm mù
    nhiều cái liền). Đọc không ra (LEVEL_READ_TRIES lần), số không đổi sau LEVEL_STUCK lần bấm, hoặc quá LEVEL_MAX_TAPS lần bấm thì
    bỏ: False."""
    level = max(1, level)
    screen = bot.screenshot()
    plus = bot.find(PLUS, threshold=THRESHOLD, screen=screen, region=PANEL)
    minus = bot.find(MINUS, threshold=THRESHOLD, screen=screen, region=PANEL)
    if plus is None or minus is None:
        bot.log("Gather Resources: không thấy nút +/− cấp")
        return False
    last, stuck = None, 0
    for _ in range(LEVEL_MAX_TAPS + 1):
        shown = _read_level(screen)
        for _ in range(LEVEL_READ_TRIES - 1):
            if shown is not None:
                break
            bot.sleep(WAIT_INTERVAL)
            screen = bot.screenshot()
            shown = _read_level(screen)
        if shown is None:
            bot.log("Gather Resources: không đọc được ô cấp")
            return False
        if shown == level:
            return True
        stuck = stuck + 1 if shown == last else 0
        if stuck >= LEVEL_STUCK:
            bot.log(f"Gather Resources: bấm mà ô cấp vẫn {shown}, cần {level}")
            return False
        last = shown
        bot.tap(*(plus if shown < level else minus), delay=LEVEL_TAP_WAIT)
        screen = bot.screenshot()
    bot.log(f"Gather Resources: bấm {LEVEL_MAX_TAPS} lần mà ô cấp chưa tới {level}")
    return False


def _read_level(screen) -> int | None:
    shown = read_level(_crop(screen, LEVEL_BOX))
    return shown if shown else None


MARCH, NOT_FOUND, FAILED = "march", "not_found", "failed"   # kết quả của _occupy


def _occupy(bot, resource: str) -> str:
    """Bấm Search; mỏ tìm được kéo vào giữa và menu tròn tự mở -> Occupy. Sau khi bấm Search: cứ 1 giây chụp một lần, tối đa
    OCCUPY_TRIES lần, chờ Occupy (hoặc "No matching targets"); không ra thì bấm Search lại (tối đa SEARCH_TRIES lượt). MARCH khi đã
    sang màn March, NOT_FOUND khi không có mỏ / mỏ trùng, FAILED nếu không được."""
    for _ in range(SEARCH_TRIES):
        search = bot.find(SEARCH_BUTTON, threshold=THRESHOLD, region=PANEL)
        if search is None:
            return FAILED      # bảng Search đã đóng (bấm nhầm ra chỗ khác)
        bot.tap(*search)
        # Chờ trước rồi mới chụp (menu / mỏ cũ còn trên màn ngay sau khi bấm): mỗi 1 giây, tối đa OCCUPY_TRIES lần.
        found = None
        for _ in range(OCCUPY_TRIES):
            bot.sleep(WAIT_INTERVAL)
            screen = bot.screenshot()
            if bot.find(NO_TARGET, threshold=NO_TARGET_THRESHOLD, screen=screen) is not None:
                bot.log(f"Gather Resources: không có mỏ {resource} phù hợp gần thành")
                return NOT_FOUND
            found = bot.find(OCCUPY, threshold=THRESHOLD, screen=screen, region=MENU)
            if found is not None:
                break
        if found is None:
            continue          # Occupy không ra: bấm Search lại
        delay(bot, MENU_SETTLE)   # menu còn đang trượt ra: chờ đứng yên rồi tìm lại vị trí Occupy
        pos = bot.find(OCCUPY, threshold=THRESHOLD, region=MENU)
        if pos is None:
            continue
        bot.tap(*pos)
        # Sau Occupy: chờ AFTER_OCCUPY_WAIT rồi mới chụp (thông báo chỉ hiện ~1 giây), tối đa AFTER_OCCUPY_TRIES lần.
        for _ in range(AFTER_OCCUPY_TRIES):
            bot.sleep(AFTER_OCCUPY_WAIT)
            screen = bot.screenshot()
            if bot.find(MARCH_FULL, threshold=NO_TARGET_THRESHOLD, screen=screen) is not None:
                raise _Stop("hết đường march", MARCH_FULL_WAIT)
            if bot.find(TARGET_TAKEN, threshold=NO_TARGET_THRESHOLD, screen=screen) is not None:
                bot.log(f"Gather Resources: mỏ {resource} tìm được đã có đội mình đang tới")     # Search lại vẫn ra mỏ này
                return NOT_FOUND
            if bot.find(MARCH_TITLE, threshold=THRESHOLD, screen=screen) is not None:
                return MARCH
        # Không thấy gì: bấm Search lại (vòng ngoài)
    return FAILED


def _march(bot, troop: int) -> int | None:
    """Màn March: đọc giờ, bấm March luôn (không chọn preset). Số giây tới lúc đội về; None nếu không March được. Giờ đội về được
    lưu vào DB NGAY TRƯỚC khi bấm March: bị ngắt sau khi bấm (việc khác tới lượt, Stop...) thì vẫn biết đội đã đi, không gửi thêm."""
    screen = bot.screenshot()
    if _no_troops(bot, screen):
        for _ in range(NO_TROOP_BACKS):      # đóng màn March, bảng Search
            bot.back()
            delay(bot, 1)
        raise _out_of_troops()
    gather = read_march_time(_crop(screen, GATHER_TIME))
    march = read_march_time(_crop(screen, MARCH_TIME))
    button = bot.find(MARCH_BUTTON, threshold=BUTTON_THRESHOLD, screen=screen, region=MARCH_BAR)
    if button is None:
        bot.back()
        delay(bot, 2)
        return None
    if gather is None or march is None:
        bot.log(f"Gather Resources: không đọc được giờ (thu thập {gather}, đi {march}), coi như 1 giờ")
        seconds = 3600
    else:
        seconds = gather + 2 * march
    set_free_at(bot, troop, time.time() + seconds + FREE_MARGIN)
    bot.tap(*button)
    if not _wait_gone(bot, MARCH_TITLE):     # vẫn ở màn March: không March được
        bot.log("Gather Resources: bấm March mà vẫn ở màn March")
        bot.back()
        delay(bot, 2)
        return None
    return seconds


def _wait_for(bot, template: str):
    """bot.wait_for: xem lại mỗi WAIT_INTERVAL giây, tối đa WAIT_TRIES lần."""
    return bot.wait_for(template, timeout=WAIT_TRIES * WAIT_INTERVAL, threshold=THRESHOLD, interval=WAIT_INTERVAL)


def _wait_gone(bot, template: str) -> bool:
    """Chờ `template` biến mất (mỗi WAIT_INTERVAL giây, tối đa WAIT_TRIES lần)."""
    for attempt in range(WAIT_TRIES):
        if bot.find(template, threshold=THRESHOLD) is None:
            return True
        if attempt < WAIT_TRIES - 1:
            bot.sleep(WAIT_INTERVAL)
    return False


def _no_troops(bot, screen=None) -> bool:
    return bot.find(NO_TROOPS, threshold=BUTTON_THRESHOLD, screen=screen, region=MARCH_BAR) is not None


def _crop(screen, box):
    x0, y0, x1, y1 = box
    return screen[y0:y1, x0:x1]


# Dòng cho bot/worker/priority.py: việc theo giờ — tới lượt khi có đội đã về (giờ rảnh lưu trong DB); không bao giờ "xong".
JOB = {
    "run": run,
    "enabled": lambda settings: bool(squads(settings)),
    "due": lambda ctx, settings: bool(due_squads(ctx, settings)),
    "done": lambda ctx, settings: False,
}
