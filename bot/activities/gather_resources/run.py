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
from ...context.templates import TEMPLATE_DIR
from ...ocr.read_march_time import run as read_march_time
from ...ocr.read_number import run as read_number
from ..result import save_errors
from .constants import (BUTTON_THRESHOLD, CENTER, CITY_MENU, FAIL_WAIT, FREE_MARGIN, FREE_PREFIX, GATHER_TIME, KEY,
                        LEVEL_BOX, LEVEL_FIX_TRIES, LEVEL_RESET_TAPS, LEVEL_TAP_WAIT, MARCH_BAR, MARCH_BUTTON, MARCH_TIME,
                        MARCH_FULL, MARCH_FULL_WAIT, MARCH_TITLE, MENU, MENU_SETTLE, MINUS, NO_TARGET, NO_TARGET_THRESHOLD,
                        NO_TROOP_WAIT, NO_TROOPS, OCCUPY, TARGET_TAKEN,
                        PANEL, PLUS, RSS_THRESHOLD, RSS_TILE,
                        SEARCH_BUTTON, SEARCH_ICON, SEARCH_SETTLE, SEARCH_TRIES, SEND_TRIES, SQUADS_KEY, MAX_TROOP, THRESHOLD, TO_WORLD_TAP,
                        TO_WORLD_TRIES, TYPE_ICON_UP, TYPE_LABEL, TYPE_ROW, TYPE_SWIPE_TIME, TYPE_SWIPE_TO_END,
                        TYPE_SWIPE_TO_START, TYPE_SWIPES_END, TYPE_SWIPES_START, TYPE_THRESHOLD, UNCHECKED, WAIT_INTERVAL,
                        WAIT_TRIES)


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
            seconds = _send(bot, squad["resource"], int(squad.get("level") or 1))
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
        set_free_at(bot, troop, time.time() + seconds + FREE_MARGIN)
        bot.record(f"Gather Resources: Troop {troop} đi thu thập {squad['resource']} Lv {squad.get('level')}, "
                   f"về sau {seconds // 60} phút")


def _send(bot, resource: str, level: int) -> int | None:
    """Gửi một đội. Trả số giây tới lúc đội về, None nếu không gửi được; ném _Stop khi hết lính / hết đường march."""
    for _ in range(SEND_TRIES):
        if not _open_search(bot) or not _pick_type(bot, resource):
            return None
        _set_level(bot, level)
        box = bot.find(UNCHECKED, threshold=0.9, region=PANEL)
        if box is not None:
            bot.tap(*box)
            delay(bot, 1)
        result = _occupy(bot, resource)
        if result == MARCH:
            return _march(bot)
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
    """Bấm loại mỏ ở hàng chọn. Hàng cuộn được (Summon, Monster, ..., Farm, Sawmill, Quarry, Iron Mine, ..., quái): không thấy chữ
    thì vuốt chậm từng nấc về đầu hàng, rồi về cuối hàng."""
    label = TYPE_LABEL.format(resource=resource)
    swipes = [None] + [TYPE_SWIPE_TO_START] * TYPE_SWIPES_START + [TYPE_SWIPE_TO_END] * TYPE_SWIPES_END
    for swipe in swipes:
        if swipe is not None:
            bot.swipe_percent(*swipe, duration=TYPE_SWIPE_TIME)
            delay(bot, 1)
        pos = bot.find(label, threshold=TYPE_THRESHOLD, region=TYPE_ROW)
        if pos is not None:
            height = bot.window_size()[1]
            bot.tap(pos[0], pos[1] - int(height * TYPE_ICON_UP / 100))
            delay(bot, 1.5)
            return True
    bot.log(f"Gather Resources: không thấy loại {resource} ở bảng Search")
    return False


def _set_level(bot, level: int):
    """Đổi loại mỏ thì cấp về 1. Đọc ô số cấp bên phải nút "+", bấm "+" / "−" đúng chênh lệch rồi đọc lại (game có lúc lỡ một
    lần bấm). Không đọc được ô số thì bấm "−" LEVEL_RESET_TAPS lần cho về 1 rồi "+" (cấp − 1) lần."""
    level = max(1, level)
    screen = bot.screenshot()
    plus = bot.find(PLUS, threshold=THRESHOLD, screen=screen, region=PANEL)
    minus = bot.find(MINUS, threshold=THRESHOLD, screen=screen, region=PANEL)
    if plus is None or minus is None:
        return
    for _ in range(LEVEL_FIX_TRIES):
        shown = _read_level(screen)
        if shown == level:
            return
        if shown is None:
            bot.log("Gather Resources: không đọc được ô cấp, bấm − về 1 rồi + lên")
            for _ in range(LEVEL_RESET_TAPS):
                bot.tap(*minus, delay=LEVEL_TAP_WAIT)
            shown = 1
        for _ in range(abs(shown - level)):
            bot.tap(*(plus if shown < level else minus), delay=LEVEL_TAP_WAIT)
        delay(bot, 0.5)
        screen = bot.screenshot()
    bot.log(f"Gather Resources: ô cấp hiện {_read_level(screen)}, cần {level}")


def _read_level(screen) -> int | None:
    shown = read_number(_crop(screen, LEVEL_BOX))
    return shown if shown > 0 else None


MARCH, NOT_FOUND, FAILED = "march", "not_found", "failed"   # kết quả của _occupy


def _occupy(bot, resource: str) -> str:
    """Bấm Search; mỏ tìm được kéo vào giữa và menu tròn mở -> Occupy. Menu chưa mở thì bấm vào mỏ (ảnh mỏ ở giữa màn) rồi tìm
    Occupy lại; không thấy ảnh mỏ thì không bấm mù (giữa màn có thể là quái / thành người khác). MARCH khi đã sang màn March,
    NOT_FOUND khi game báo "No matching targets", FAILED nếu không được."""
    tile = RSS_TILE.format(resource=resource)
    has_tile = (TEMPLATE_DIR / tile).exists()
    for _ in range(SEARCH_TRIES):
        search = bot.find(SEARCH_BUTTON, threshold=THRESHOLD, region=PANEL)
        if search is None:
            return FAILED      # bảng Search đã đóng (bấm nhầm ra chỗ khác)
        bot.tap(*search)
        delay(bot, SEARCH_SETTLE)   # menu / mỏ cũ còn trên màn ngay sau khi bấm: đừng nhận nhầm
        found = _wait_any(bot, [(OCCUPY, THRESHOLD, MENU), (NO_TARGET, NO_TARGET_THRESHOLD, None)])
        if found is not None and found[0] == NO_TARGET:
            bot.log(f"Gather Resources: không có mỏ {resource} phù hợp gần thành")
            return NOT_FOUND
        if found is None:
            # Menu tròn không tự mở: bấm vào mỏ ở giữa màn (chỉ khi thấy ảnh mỏ; bấm mỏ lúc menu đang tự mở thì menu đóng lại).
            pos = bot.find(tile, threshold=RSS_THRESHOLD, region=CENTER) if has_tile else None
            if pos is None:
                continue
            bot.tap(*pos)
            if _wait_for(bot, OCCUPY) is None:
                continue
        delay(bot, MENU_SETTLE)   # menu còn đang trượt ra: chờ đứng yên rồi tìm lại vị trí Occupy
        pos = bot.find(OCCUPY, threshold=THRESHOLD, region=MENU)
        if pos is None:
            continue
        bot.tap(*pos)
        found = _wait_any(bot, [(MARCH_TITLE, THRESHOLD, None), (MARCH_FULL, NO_TARGET_THRESHOLD, None),
                                (TARGET_TAKEN, NO_TARGET_THRESHOLD, None)])
        if found is None:
            continue
        if found[0] == MARCH_FULL:
            raise _Stop("hết đường march", MARCH_FULL_WAIT)
        if found[0] == TARGET_TAKEN:      # Search lại vẫn ra đúng mỏ này: bỏ đội này lượt này
            bot.log(f"Gather Resources: mỏ {resource} tìm được đã có đội mình đang tới")
            return NOT_FOUND
        return MARCH
    return FAILED


def _march(bot) -> int | None:
    """Màn March: đọc giờ, bấm March luôn (không chọn preset). Số giây tới lúc đội về; None nếu không March được."""
    screen = bot.screenshot()
    if _no_troops(bot, screen):
        bot.back()
        delay(bot, 2)
        raise _out_of_troops()
    gather = read_march_time(_crop(screen, GATHER_TIME))
    march = read_march_time(_crop(screen, MARCH_TIME))
    button = bot.find(MARCH_BUTTON, threshold=BUTTON_THRESHOLD, screen=screen, region=MARCH_BAR)
    if button is None:
        bot.back()
        delay(bot, 2)
        return None
    bot.tap(*button)
    if not _wait_gone(bot, MARCH_TITLE):     # vẫn ở màn March: không March được
        bot.log("Gather Resources: bấm March mà vẫn ở màn March")
        bot.back()
        delay(bot, 2)
        return None
    if gather is None or march is None:
        bot.log(f"Gather Resources: không đọc được giờ (thu thập {gather}, đi {march}), coi như 1 giờ")
        return 3600
    return gather + 2 * march


def _wait_for(bot, template: str):
    """bot.wait_for: xem lại mỗi WAIT_INTERVAL giây, tối đa WAIT_TRIES lần."""
    return bot.wait_for(template, timeout=WAIT_TRIES * WAIT_INTERVAL, threshold=THRESHOLD, interval=WAIT_INTERVAL)


def _wait_any(bot, targets: list[tuple]) -> tuple[str, tuple] | None:
    """Như _wait_for nhưng chờ ảnh đầu tiên hiện trong `targets` [(ảnh, ngưỡng, vùng)]: (ảnh, vị trí) hoặc None."""
    for attempt in range(WAIT_TRIES):
        screen = bot.screenshot()
        for template, threshold, region in targets:
            pos = bot.find(template, threshold=threshold, screen=screen, region=region)
            if pos is not None:
                return template, pos
        if attempt < WAIT_TRIES - 1:
            bot.sleep(WAIT_INTERVAL)
    return None


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
