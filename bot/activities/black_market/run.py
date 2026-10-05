"""
run.py — activity "Black Market": `run(bot, settings)` (settings của tab Black Market, ui/tabs/black_market_tab.py):
{"check_gold": bool, "refresh": "ALL"/"10"/..., "quantity_buy": "ALL"/"10"/..., "resources": bool,
 "items": {item id: bool}} — danh mục vật phẩm: items.json.

1. Mở màn Black Market: đang ở đó thì thôi; không thì Back về màn chính -> đưa Chợ vào giữa (_market): Chợ trên màn ->
   bản đồ thành của máy (DB, city_map.py: đi từ công trình đã biết đang thấy) -> Go nhiệm vụ mua Black Market /
   Tax -> Go nhiệm vụ Gold Levy (Thành chính; chưa có bản đồ thì quét thành, lưu DB) -> không nhiệm vụ nào có Go: không
   làm, ghi log -> bấm Chợ -> icon "Black Market".
2. Mỗi bước chụp 1 ảnh:
   - số dư (OCR): kim cương < GEMS_MIN -> dừng; vàng < GOLD_MIN và tích CheckGold -> dừng;
   - đủ Quantity Buy -> dừng;
   - quét 6 ô (scan): lấy toạ độ các ô có món được tích, còn mua được (nút giá xanh), chưa thử trong bộ hàng này;
     bỏ ô giá kim cương của món không được mua bằng kim cương (Resource, Chips: `buy_with_gems` false) -> bấm ô đầu
     -> chờ hộp "Are you sure ...?" (tối đa CONFIRM_WAIT giây) -> Confirm (+1 lần mua); không hiện -> bỏ ô đó;
   - hết ô để mua -> Instant Refresh (đủ số lần Refresh thì dừng) -> bộ hàng mới, quét lại.
3. Dừng: Back (đóng màn Black Market).
"""
from dataclasses import dataclass

import numpy as np

from ...ocr.read_balance import read_gems, read_gold
from ..daily_activities.constants import MAIN_MORE
from ..event.kings_path.black_market.constants import (
    BUY_WAIT,
    CONFIRM,
    GEM,
    GEM_THRESHOLD,
    INSTANT_REFRESH,
    MENU_BLACK_MARKET,
    SLOT_GREEN,
    SLOT_HALF,
    SLOTS,
    TITLE,
)
from ..event.city_building import BUILDING_THRESHOLD, KEEP, MARKET
from .city_map import centre, city_screen, goto, locate, scan
from ..daily_activities.black_market import TASK as BLACK_MARKET_TASK
from ..daily_activities.common import open_task, task_cards, task_titles
from ..daily_activities.gold_levy import TASK as GOLD_LEVY_TASK
from ..daily_activities.resource_tax import TASK as RESOURCE_TAX_TASK
from ..daily_activities.constants import TASK_OPENED
from ..event.kings_path.black_market.run import _refresh
from ..event.kings_path.constants import SCREEN_WAIT
from .constants import (
    CATALOG,
    GEMS_MIN,
    GOLD_MIN,
    GOLD_PACK_IDS,
    ICON_AREA,
    ITEM_THRESHOLD,
    LABEL_AREA,
    LABEL_THRESHOLD,
    MAX_IDLE_STEPS,
    MENU_THRESHOLD,
    NAME,
    NO_LIMIT,
    RESOURCE_IDS,
    RESOURCE_LABEL,
)

HOME_BACKS = 5     # số lần Back tối đa để về màn chính trước khi tìm Chợ
CONFIRM_WAIT = 5   # giây chờ hộp xác nhận sau khi bấm một ô
MARKET_WAIT = 10   # giây chờ thấy Chợ sau khi bấm Go nhiệm vụ mua Black Market / Tax


@dataclass
class Wanted:
    """Một món được tích: id, ảnh icon (đường dẫn dưới Images/), có được mua bằng kim cương không."""
    id: str
    icons: list[str]
    gems_ok: bool


@dataclass
class Target:
    """Một ô cần mua: số thứ tự ô, toạ độ (tâm nút giá), id món."""
    slot: int
    pos: tuple[int, int]
    item: str


def run(bot, settings: dict):
    """`bot` là BotContext của thiết bị; `settings` là cấu hình tab Black Market."""
    wanted = wanted_items(settings)
    if not wanted:
        bot.log(f"{NAME}: no item selected")
        return
    if not _open(bot):
        return
    buy(bot, settings, wanted)


def wanted_items(settings: dict) -> list[Wanted]:
    """Các món được tích (ô Resource = 4 gói tài nguyên lương thực / gỗ / đá / quặng)."""
    ticked = {k for k, v in (settings.get("items") or {}).items() if v}
    if settings.get("resources", True):
        ticked |= set(RESOURCE_IDS)
    return [Wanted(it["id"], it["icons"], bool(it.get("buy_with_gems"))) for it in CATALOG["items"]
            if it["id"] in ticked]


def _open(bot) -> bool:
    """Tới màn Black Market (xem đầu file, bước 1). True nếu tới nơi."""
    if bot.find(TITLE) is not None:
        return True
    for _ in range(HOME_BACKS):
        if bot.find(MAIN_MORE) is not None:
            break
        bot.back(delay=1)
    market = _market(bot)
    if market is None:
        return False
    bot.tap(*market)
    icon = bot.wait_for(MENU_BLACK_MARKET, timeout=SCREEN_WAIT, threshold=MENU_THRESHOLD)
    if icon is None:
        bot.record(f"{NAME}: Black Market icon not shown after tapping the Market")
        return False
    bot.tap(*icon)
    if bot.wait_for(TITLE, timeout=SCREEN_WAIT) is None:
        bot.record(f"{NAME}: Black Market screen not shown")
        return False
    return True


def _market(bot):
    """Đưa Chợ vào giữa màn, trả vị trí (None + ghi log nếu không được):
    1. Chợ có trên màn -> kéo vào giữa.
    2. Máy đã có bản đồ thành (bot.city_map, DB) -> đi từ công trình đã biết đang thấy trên màn (city_map.goto).
    3. Không được: Go nhiệm vụ mua Black Market / Tax (game kéo Chợ vào giữa); không có thì Go nhiệm vụ Gold Levy (về
       Thành chính): chưa có bản đồ -> quét thành, lưu DB (bot.set_city_map) -> đi thẳng tới Chợ.
    4. Không nhiệm vụ nào còn Go -> không làm Black Market."""
    score, pos = locate(bot, city_screen(bot), MARKET)
    if pos is not None and score >= BUILDING_THRESHOLD:
        return centre(bot, MARKET, pos)[0]
    city_map = dict(getattr(bot, "city_map", None) or {})
    if MARKET in city_map:
        pos = goto(bot, NAME, MARKET, city_map)
        if pos is not None:
            return pos
    pos = _market_by_task(bot)
    if pos is not None:
        return pos
    if not _keep_by_levy(bot):
        bot.record(f"{NAME}: no Black Market / Tax / Gold Levy task with Go, skip Black Market")
        return None
    if MARKET not in city_map:
        city_map = scan(bot, NAME)
        if not city_map:
            return None
        bot.set_city_map(city_map)
        if MARKET not in city_map:
            bot.record(f"{NAME}: Market not found while scanning the city")
            return None
    pos = goto(bot, NAME, MARKET, city_map)
    if pos is None:
        bot.record(f"{NAME}: cannot reach the Market with the city map")
    return pos


def _market_by_task(bot):
    """Bấm Go nhiệm vụ Daily mua Black Market, không có thì Tax (cả hai ở Chợ: game kéo Chợ vào giữa) -> chờ thấy Chợ.
    Trả vị trí Chợ, hoặc None (không nhiệm vụ nào còn Go / không thấy Chợ)."""
    for task in (BLACK_MARKET_TASK, RESOURCE_TAX_TASK):
        pos = _go_to(bot, task, MARKET)
        if pos is not None:
            return pos
    return None


def _keep_by_levy(bot) -> bool:
    """Bấm Go nhiệm vụ Daily Gold Levy -> game kéo Thành chính vào giữa. True nếu đã thấy Thành chính."""
    return _go_to(bot, GOLD_LEVY_TASK, KEEP) is not None


def _go_to(bot, task, building):
    """Go nhiệm vụ `task` -> chờ thấy `building` (tối đa MARKET_WAIT giây). Trả vị trí, hoặc None."""
    if open_task(bot, task_titles(task), task_cards(task)) != TASK_OPENED:
        bot.log(f"{NAME}: {task.label} task has no Go")
        return None
    bot.log(f"{NAME}: Go of {task.label} task -> {building}")
    for _ in range(MARKET_WAIT):
        score, pos = locate(bot, city_screen(bot), building)
        if pos is not None and score >= BUILDING_THRESHOLD:
            return pos
        bot.sleep(1)
    bot.record(f"{NAME}: {building} not shown after Go of {task.label} task")
    return None


def buy(bot, settings: dict, wanted: list[Wanted]) -> int:
    """Đang ở màn Black Market: mua các món `wanted` (Instant Refresh khi hết ô để mua) tới khi gặp điều kiện dừng ->
    Back. Trả số lần đã mua."""
    check_gold = bool(settings.get("check_gold"))
    refresh_limit = _limit(settings.get("refresh"))
    buy_limit = _limit(settings.get("quantity_buy"))
    bought = refreshes = idle = 0
    tried: set[int] = set()   # ô đã bấm trong bộ hàng hiện tại
    while idle < MAX_IDLE_STEPS:
        idle += 1
        screen = bot.screenshot()
        if bot.find(TITLE, screen=screen) is None:
            bot.record(f"{NAME}: not on Black Market screen, stop")
            return bought
        low = _low_balance(screen, check_gold)
        if low:
            return _stop(bot, f"{low}, bought {bought}", bought)
        if buy_limit != NO_LIMIT and bought >= buy_limit:
            return _stop(bot, f"Quantity Buy reached ({bought})", bought)
        targets = [t for t in scan(bot, screen, wanted) if t.slot not in tried]
        if targets:
            target = targets[0]
            tried.add(target.slot)
            bot.log(f"{NAME}: buy {target.item} (slot {target.slot + 1})")
            bot.tap(*target.pos)
            confirm = bot.wait_for(CONFIRM, timeout=CONFIRM_WAIT)
            if confirm is None:
                bot.log(f"{NAME}: no Confirm for slot {target.slot + 1}, skip it")
                continue
            bot.tap(*confirm, delay=BUY_WAIT)
            bought += 1
            idle = 0
            bot.log(f"{NAME}: bought {bought}" + ("" if buy_limit == NO_LIMIT else f" / {buy_limit}"))
            continue
        if refresh_limit != NO_LIMIT and refreshes >= refresh_limit:
            return _stop(bot, f"Refresh limit reached ({refreshes}), bought {bought}", bought)
        if bot.find(INSTANT_REFRESH, screen=screen) is None:
            return _stop(bot, f"no Instant Refresh, bought {bought}", bought)
        refreshes += 1
        bot.log(f"{NAME}: Instant Refresh {refreshes}" + ("" if refresh_limit == NO_LIMIT else f" / {refresh_limit}"))
        if not _refresh(bot, screen, NAME):
            return _stop(bot, f"items did not change after Refresh, bought {bought}", bought)
        tried.clear()
        idle = 0
    return _stop(bot, f"nothing done in {MAX_IDLE_STEPS} steps, bought {bought}", bought)


def scan(bot, screen, wanted: list[Wanted]) -> list[Target]:
    """Các ô trên `screen` có món trong `wanted`, còn mua được (nút giá xanh), không phải ô giá kim cương của món
    không được mua bằng kim cương."""
    gems_ok = {w.id: w.gems_ok for w in wanted}
    labels = [path for pack in CATALOG["resource_packs"] for path in pack["label_templates"]]
    resources = any(w.id in RESOURCE_IDS for w in wanted)
    gold_icons = [p for it in CATALOG["items"] if it["id"] in GOLD_PACK_IDS for p in it["icons"]]
    targets = []
    for slot, (x, y) in enumerate(SLOTS):
        if not _green(screen, x, y):
            continue   # đã mua / không mua được
        item = _identify(bot, screen, x, y, wanted, labels if resources else [], gold_icons)
        if item is None:
            continue
        if not gems_ok.get(item, False) and _gem_price(bot, screen, x, y):
            continue   # Resource / Chips: không mua bằng kim cương
        targets.append(Target(slot, (x, y), item))
    return targets


def _identify(bot, screen, x, y, wanted, labels, gold_icons) -> str | None:
    """Id món được tích trong ô (x, y), hoặc None. Gói vàng (khớp icon vàng hơn) -> None."""
    dx, dy, w, h = ICON_AREA
    area = bot.crop(screen, x + dx, y + dy, w, h)
    score, item = max(((bot.best_match(icon, screen=area)[0], want.id)
                       for want in wanted for icon in want.icons), default=(0.0, None))
    gold = max((bot.best_match(icon, screen=area)[0] for icon in gold_icons), default=0.0)
    if score >= ITEM_THRESHOLD and score > gold:
        return item
    if labels and gold < ITEM_THRESHOLD:
        # Gói tài nguyên mức chưa có icon: nhận theo chữ số lượng.
        lx, ly, lw, lh = LABEL_AREA
        label_area = bot.crop(screen, x + lx, y + ly, lw, lh)
        if any(bot.best_match(path, screen=label_area)[0] >= LABEL_THRESHOLD for path in labels):
            return RESOURCE_LABEL
    return None


def _green(screen, x: int, y: int) -> bool:
    """Nút giá còn xanh (chưa mua)."""
    hw, hh = SLOT_HALF
    box = screen[y - hh:y + hh, x - hw:x + hw].astype(np.int16)
    return float((box[..., 1] - box[..., 2]).mean()) > SLOT_GREEN


def _gem_price(bot, screen, x: int, y: int) -> bool:
    """Nút giá có icon kim cương."""
    hw, hh = SLOT_HALF
    area = bot.crop(screen, x - hw, y - hh, 2 * hw, 2 * hh)
    return bot.find(GEM, threshold=GEM_THRESHOLD, screen=area) is not None


def _low_balance(screen, check_gold: bool) -> str | None:
    """Kim cương < GEMS_MIN (luôn) / vàng < GOLD_MIN (khi check_gold) -> lý do; đọc lỗi -> không coi là thiếu."""
    gems = read_gems(screen)
    if gems is not None and gems < GEMS_MIN:
        return f"gems {gems:,} < {GEMS_MIN:,}"
    if check_gold:
        gold = read_gold(screen)
        if gold is not None and gold < GOLD_MIN:
            return f"gold {gold:,} < {GOLD_MIN:,}"
    return None


def _stop(bot, reason: str, bought: int) -> int:
    """Ghi lý do dừng, Back (đóng màn Black Market); trả `bought`."""
    bot.record(f"{NAME}: {reason}, stop")
    bot.back(delay=1)
    return bought


def _limit(text) -> int:
    """Ô Refresh / Quantity Buy -> số lần (NO_LIMIT = "ALL")."""
    try:
        return int(text)
    except (TypeError, ValueError):
        return NO_LIMIT
