"""
run.py — "Craft" activity: chế tạo các trang bị đã tích ở tab Craft (settings {"items": {id: số lượng}}). Xem FLOW.md.

Chỉ làm MỘT lần (mỗi lần Start), độ ưu tiên thấp nhất: worker chỉ tới nó khi mọi nhiệm vụ khác đã làm xong (dòng "Craft" ở
bot/worker/priority.py: priority 0, once). Chưa tích trang bị nào thì nhiệm vụ không vào danh sách.

Lò rèn chỉ chế tạo MỘT trang bị một lúc, nên mỗi vòng làm đúng một cái, rồi tăng tốc cho xong mới làm cái tiếp:
1. Tới Lò rèn (city_map.reach_building: thấy thì kéo vào giữa; có route thì đi theo route; CHƯA có route thì tự tìm route, lưu DB) -> bấm Lò rèn
   -> menu. Menu có "Speed Up" = Lò rèn đang chế tạo dở: tăng tốc cho xong trước (bước 4). Có "Craft" -> bấm, vào màn Craft (luôn ở loại Nhẫn).
2. Chọn trang bị: bấm vòng chọn loại ở đáy (trái / phải, nhận loại đang mở bằng ảnh Craft/Category/<loại>.png) tới đúng loại -> vuốt hàng trang bị
   về đầu -> tìm icon trang bị cần làm (vuốt sang trái tới khi hàng không đổi) -> bấm icon -> so ảnh tên (Craft/<loại>/name/...) với tên ở đầu
   màn: khớp mới làm tiếp, không khớp thì thử chỗ khác.
3. Nút bên phải đáy màn, theo màu: xanh lá "Quick Compose" -> bấm (nút đổi thành Begin) rồi Begin; vàng "Begin" -> bấm; xám / đen -> chưa chế tạo
   được, bỏ qua trang bị này. Bấm Begin xong game về thành, Lò rèn đang chế tạo.
4. Tăng tốc: bấm Lò rèn -> "Speed Up" -> màn "Crafting Speedup" -> "Finish All" (vật phẩm tăng tốc, như Heal / train lính) -> về thành -> bấm
   bóng trang bị nổi trên Lò rèn -> "Congratulations on getting" -> Confirm. Rồi làm trang bị kế (số lượng > 1 thì lặp lại cả vòng).
Bị ngắt giữa chừng (boss / 120 giây) rồi gọi lại từ đầu: số còn lại của từng trang bị nhớ theo thiết bị (_remaining; trừ khi Lò rèn chế tạo xong, _pending), Lò rèn đang chế tạo dở thì
tăng tốc trước, nên không làm lặp.
"""
from functools import lru_cache

import cv2
import numpy as np

from ...city.city_map import reach_building
from ...context.templates import TEMPLATE_DIR, read_image
from ..event.city_building import FORGE
from ..event.gather_troops.train_troop.constants import (
    CHECKBOX_OFF,
    FINISH_ALL,
    FINISH_ALL_POS,
    FINISH_ALL_TITLE,
    SPEEDUP_SETTINGS,
    SPEEDUP_SETTINGS_POS,
)
from ..event.gather_troops.train_troop.constants import CONFIRM as FINISH_CONFIRM
from ..event.gather_troops.train_troop.constants import CONFIRM_POS as FINISH_CONFIRM_POS
from ..event.kings_path.building import open_menu
from ..event.kings_path.constants import SCREEN_WAIT
from ..event.kings_path.refine.constants import CRAFT_TITLE, MENU_CRAFT
from ..result import save_errors
from .constants import item_name
from .constants import (
    ACTION_WAIT,
    ACTIVE_HALF,
    ACTIVE_POS,
    BEGIN,
    BEGIN_BUTTON,
    BEGIN_INTERVAL,
    BEGIN_THRESHOLD,
    BEGIN_TIMEOUT,
    BUTTON_BOX,
    BUTTON_POS,
    CAROUSEL,
    CATEGORY_DIR,
    CATEGORY_THRESHOLD,
    COLLECT_POS,
    COLLECT_TRIES,
    COLLECT_WAIT,
    COLOR_MIN_SATURATION,
    CONFIRM,
    CONFIRM_POS,
    CONGRATS,
    DISABLED,
    FOLDER,
    GOLD_HUE,
    GREEN_HUE,
    ICON_THRESHOLD,
    ITEM_WAIT,
    ITEMS_KEY,
    ITEMS_REGION,
    ITEMS_SAME,
    ITEMS_SWIPE_LEFT,
    ITEMS_SWIPE_RIGHT,
    ITEMS_SWIPE_TIME,
    ITEMS_SWIPE_WAIT,
    ITEMS_SWIPES,
    ITEM_PATCH,
    KEY,
    LEFT_TYPE_POS,
    LOCK,
    LOCK_MARGIN,
    LOCK_THRESHOLD,
    MENU_SPEED_UP,
    NAME,
    QUICK_COMPOSE,
    RIGHT_TYPE_POS,
    SPEEDUP_STEPS,
    SPEEDUP_TITLE,
    SPEEDUP_WAIT,
    START_TYPE,
    STEP_WAIT,
    TITLE_REGION,
    TITLE_THRESHOLD,
    TYPE_CHECKS,
    TYPE_WAIT,
)

# Số còn lại cần chế tạo của từng trang bị, theo thiết bị (id(bot)): bị ngắt rồi gọi lại thì làm tiếp phần còn lại.
_remaining: dict[int, dict[str, int]] = {}
# Trang bị vừa bấm Begin mà chưa tăng tốc xong, theo thiết bị: chỉ trừ vào _remaining khi Lò rèn thật sự đã chế tạo xong (xem consume_pending). Bị ngắt
# ngay sau khi bấm Begin (không biết click đã tới chưa) thì lượt sau nhìn menu Lò rèn: có "Speed Up" = đã bắt đầu -> tăng tốc rồi mới trừ; không có = chưa
# bắt đầu -> bỏ dấu này, trang bị vẫn còn trong danh sách cần làm.
_pending: dict[int, str] = {}
# Tổng số đã chế tạo xong / số cần làm của từng trang bị trong lượt này, theo thiết bị: để ghi log "đã chế tạo X (1/2)" và tổng kết cuối.
_done: dict[int, dict[str, int]] = {}
_total: dict[int, dict[str, int]] = {}


def selected(settings: dict) -> dict[str, int]:
    """{id trang bị: số lượng} của các trang bị đã tích."""
    return {item_id: int(qty) for item_id, qty in (settings.get(ITEMS_KEY) or {}).items() if int(qty) > 0}


def category_of(item_id: str) -> str:
    """"ring/01_Fighter's_Ring" -> "ring"."""
    return item_id.split("/", 1)[0]


def icon_path(item_id: str) -> str:
    return f"{FOLDER}/{item_id}.png"


def name_path(item_id: str) -> str:
    category, stem = item_id.split("/", 1)
    return f"{FOLDER}/{category}/name/{stem}.png"


@lru_cache(maxsize=None)
def _icon_core(item_id: str):
    """Phần giữa icon (28x28, bỏ viền: món đang chọn có viền vàng) dùng để tìm trên hàng trang bị; None nếu thiếu ảnh."""
    image = read_image(TEMPLATE_DIR / icon_path(item_id))
    return None if image is None else image[8:36, 8:36]


def button_state(screen: np.ndarray) -> str:
    """Nút bên phải đáy màn theo màu: QUICK_COMPOSE (xanh lá), BEGIN (vàng) hoặc DISABLED (xám / đen, hoặc màu khác)."""
    x0, y0, x1, y1 = BUTTON_BOX
    hue, sat, _ = cv2.cvtColor(screen[y0:y1, x0:x1], cv2.COLOR_BGR2HSV).reshape(-1, 3).mean(axis=0)
    if sat < COLOR_MIN_SATURATION:
        return DISABLED
    if GREEN_HUE[0] <= hue <= GREEN_HUE[1]:
        return QUICK_COMPOSE
    if GOLD_HUE[0] <= hue <= GOLD_HUE[1]:
        return BEGIN
    return DISABLED


def active_category(bot, screen) -> str | None:
    """Loại trang bị đang mở (vòng giữa): ảnh Craft/Category/<loại>.png khớp cao nhất, hoặc None."""
    x, y = ACTIVE_POS
    area = bot.crop(screen, x - ACTIVE_HALF, y - ACTIVE_HALF, 2 * ACTIVE_HALF, 2 * ACTIVE_HALF)
    scores = {kind: bot.best_match(f"{CATEGORY_DIR}/{kind}.png", screen=area)[0] for kind in CAROUSEL}
    kind = max(scores, key=scores.get)
    return kind if scores[kind] >= CATEGORY_THRESHOLD else None


def goto_category(bot, target: str) -> bool:
    """Bấm vòng nhỏ bên trái / phải của vòng chọn loại tới khi loại đang mở là `target`. False nếu vòng không đổi sau TYPE_CHECKS lần kiểm tra."""
    for _ in range(len(CAROUSEL) + 2):
        current = active_category(bot, bot.screenshot())
        if current == target:
            return True
        if current is None:
            bot.sleep(1)
            continue
        step_right = CAROUSEL.index(target) > CAROUSEL.index(current)
        bot.tap(*(RIGHT_TYPE_POS if step_right else LEFT_TYPE_POS), delay=TYPE_WAIT)
        for _ in range(TYPE_CHECKS):
            if active_category(bot, bot.screenshot()) != current:
                break
            bot.sleep(1)
        else:
            bot.record(f"{NAME}: equipment type still {current} after {TYPE_CHECKS} checks")
            return False
    return False


def _patch(screen: np.ndarray) -> np.ndarray:
    """Một trang bị ở giữa hàng (ITEM_PATCH): vuốt mà ô này không đổi nghĩa là danh sách không cuộn nữa."""
    x0, y0, x1, y1 = ITEM_PATCH
    return screen[y0:y1, x0:x1].astype(np.int16)


def _swipe_items(bot, swipe: tuple) -> bool:
    """Vuốt hàng trang bị một cú (chậm); True nếu có cuộn. Trang bị ở giữa hàng không đổi sau cú vuốt = đã ở cuối bên phải / trái rồi (False): không vuốt tiếp."""
    before = _patch(bot.screenshot())
    bot.swipe_percent(*swipe, duration=ITEMS_SWIPE_TIME, delay=ITEMS_SWIPE_WAIT)
    return float(np.abs(_patch(bot.screenshot()) - before).mean()) >= ITEMS_SAME


def items_to_start(bot):
    """Vuốt hàng trang bị sang phải tới khi hàng không đổi nữa: về đầu danh sách."""
    for _ in range(ITEMS_SWIPES):
        if not _swipe_items(bot, ITEMS_SWIPE_RIGHT):
            return


def candidates(bot, screen, item_id: str) -> list[tuple[int, int]]:
    """Tâm các chỗ trên hàng trang bị khớp icon của `item_id`, trái -> phải."""
    core = _icon_core(item_id)
    if core is None:
        return []
    return sorted(bot.find_all(core, threshold=ICON_THRESHOLD, screen=screen, region=ITEMS_REGION))


def first_lock_x(bot, screen) -> int | None:
    """Tâm x của ổ khoá trái nhất trên hàng trang bị (Craft/lock.png), None nếu hàng không có ô khoá nào."""
    hits = bot.find_all(LOCK, threshold=LOCK_THRESHOLD, screen=screen, region=ITEMS_REGION)
    return min((x for x, _ in hits), default=None)


def title_matches(bot, item_id: str) -> bool:
    """Tên ở đầu màn có phải tên của `item_id` không (ảnh tên Craft/<loại>/name/...)."""
    return bot.best_match(name_path(item_id), region=TITLE_REGION)[0] >= TITLE_THRESHOLD


def wait_for_begin(bot, item_id: str) -> bool:
    """Sau Quick Compose: wait_for nút Begin vàng hiện (kiểm tra mỗi BEGIN_INTERVAL giây, tối đa BEGIN_TIMEOUT giây); tên vẫn đúng mới tính."""
    pos = bot.wait_for(BEGIN_BUTTON, timeout=BEGIN_TIMEOUT, threshold=BEGIN_THRESHOLD, interval=BEGIN_INTERVAL)
    return pos is not None and title_matches(bot, item_id)


def start_craft(bot, item_id: str) -> bool:
    """Trang bị đã chọn (tên đúng): theo nút bên phải đáy màn — xanh lá Quick Compose thì bấm (nút đổi thành Begin), vàng Begin thì bấm, xám / đen thì
    bỏ qua. True nếu đã bấm Begin và game rời màn Craft (về thành: Lò rèn đang chế tạo)."""
    state = button_state(bot.screenshot())
    if state == DISABLED:
        bot.record(f"{NAME}: {item_id}: Begin disabled (not enough materials?), skip")
        return False
    if state == QUICK_COMPOSE:
        bot.log(f"{NAME}: {item_id}: Quick Compose")
        bot.tap(*BUTTON_POS)
        if not wait_for_begin(bot, item_id):
            bot.record(f"{NAME}: {item_id}: Begin not shown after Quick Compose, skip")
            return False
    bot.log(f"{NAME}: {item_id}: Begin")
    _pending[id(bot)] = item_id             # đặt TRƯỚC khi bấm: bị ngắt giữa lúc bấm / chờ thì lượt sau biết đang làm trang bị nào
    bot.tap(*BUTTON_POS, delay=ACTION_WAIT)
    if bot.find(CRAFT_TITLE) is not None:
        _pending.pop(id(bot), None)
        bot.record(f"{NAME}: {item_id}: Craft screen still shown after Begin, skip")
        return False
    return True


def craft_category(bot, category: str, wanted: dict[str, int]) -> str | None:
    """Trong loại `category` (đã mở): đi hết hàng trang bị từ đầu, gặp trang bị cần làm thì chọn -> kiểm tra tên -> bấm nút. Trả id trang bị vừa bấm
    Begin (game đã về thành), hoặc None khi hết trang bị làm được trong loại này. Trang bị không làm được / không thấy thì xoá khỏi `wanted`."""
    items_to_start(bot)
    for swipes in range(ITEMS_SWIPES + 1):
        screen = bot.screenshot()
        lock_x = first_lock_x(bot, screen)      # từ ô khoá đầu tiên tới hết danh sách đều chưa mở: không chế tạo được
        for item_id in [i for i in wanted if category_of(i) == category]:
            for pos in candidates(bot, screen, item_id):
                if lock_x is not None and pos[0] >= lock_x - LOCK_MARGIN:
                    bot.record(f"{NAME}: {item_id}: locked, skip")
                    wanted.pop(item_id)
                    break
                bot.tap(*pos, delay=ITEM_WAIT)
                if not title_matches(bot, item_id):
                    continue            # icon giống nhau của trang bị khác: thử chỗ khớp tiếp theo
                if start_craft(bot, item_id):
                    return item_id
                wanted.pop(item_id)     # Begin xám / không ghép được: bỏ qua trang bị này
                break
            screen = bot.screenshot()
        if not any(category_of(i) == category for i in wanted):
            return None
        if lock_x is not None:                  # còn trang bị chưa thấy mà đã tới ô khoá: các trang bị còn lại nằm sau ô khoá, bỏ qua hết, không vuốt tiếp
            for item_id in [i for i in wanted if category_of(i) == category]:
                bot.record(f"{NAME}: {item_id}: behind a locked item, skip")
                wanted.pop(item_id)
            return None
        if swipes < ITEMS_SWIPES and not _swipe_items(bot, ITEMS_SWIPE_LEFT):
            break
    for item_id in [i for i in wanted if category_of(i) == category]:
        bot.record(f"{NAME}: {item_id}: not found in the list, skip")
        wanted.pop(item_id)
    return None


def craft_next(bot, wanted: dict[str, int]) -> str | None:
    """Màn Craft đang mở: làm MỘT trang bị trong `wanted` (loại gần loại đang mở trước). Trả id trang bị đã bấm Begin, hoặc None."""
    current = active_category(bot, bot.screenshot()) or START_TYPE
    while wanted:
        category = min({category_of(i) for i in wanted}, key=lambda c: abs(CAROUSEL.index(c) - CAROUSEL.index(current)))
        if not goto_category(bot, category):
            return None                 # kẹt ở vòng chọn loại: lượt sau làm lại
        started = craft_category(bot, category, wanted)
        if started is not None:
            return started
        current = category
    return None


def finish_all(bot) -> bool:
    """Màn Crafting Speedup (như Healing / Training Speedup): lần đầu Speedup Settings -> hộp Finish All: tích ô nếu chưa tích -> Confirm; rồi
    Finish All. True nếu đã bấm Finish All."""
    if bot.wait_for(SPEEDUP_TITLE, timeout=SCREEN_WAIT) is None:
        bot.record(f"{NAME}: Crafting Speedup screen not shown")
        return False
    settings_done = False
    for _ in range(SPEEDUP_STEPS):
        screen = bot.screenshot()
        if bot.find(FINISH_ALL_TITLE, screen=screen) is not None:
            box = bot.find(CHECKBOX_OFF, screen=screen)
            if box is not None:
                bot.tap(*box, delay=1)
            pos = bot.find(FINISH_CONFIRM, screen=bot.screenshot())
            bot.tap(*(FINISH_CONFIRM_POS if pos is None else pos), delay=SPEEDUP_WAIT)
            settings_done = True
        elif bot.find(SPEEDUP_TITLE, screen=screen) is not None:
            if not settings_done:
                pos = bot.find(SPEEDUP_SETTINGS, screen=screen)
                bot.tap(*(SPEEDUP_SETTINGS_POS if pos is None else pos), delay=SPEEDUP_WAIT)
                continue
            bot.log(f"{NAME}: Finish All")
            pos = bot.find(FINISH_ALL, screen=screen)
            bot.tap(*(FINISH_ALL_POS if pos is None else pos), delay=SPEEDUP_WAIT)
            return True
        else:
            bot.log(f"{NAME}: left Crafting Speedup screen")
            return True
    bot.record(f"{NAME}: Finish All not reached")
    return False


def collect(bot) -> bool:
    """Sau Finish All: bóng trang bị vừa làm xong nổi trên Lò rèn (giữa màn) -> bấm -> hộp "Congratulations on getting" -> Confirm."""
    bot.sleep(COLLECT_WAIT)
    for _ in range(COLLECT_TRIES):
        bot.tap(*COLLECT_POS, delay=2)
        if bot.find(CONGRATS) is not None:
            pos = bot.find(CONFIRM)
            bot.tap(*(CONFIRM_POS if pos is None else pos), delay=STEP_WAIT)
            return True
    bot.record(f"{NAME}: finished item not collected")
    return False


def consume_pending(bot):
    """Trang bị đang chế tạo (_pending) đã tăng tốc xong: trừ 1 vào số còn lại (về 0 thì bỏ khỏi danh sách)."""
    item_id = _pending.pop(id(bot), None)
    wanted = _remaining.get(id(bot), {})
    if item_id in wanted:
        wanted[item_id] -= 1
        if wanted[item_id] <= 0:
            wanted.pop(item_id)
        done = _done.setdefault(id(bot), {})
        done[item_id] = done.get(item_id, 0) + 1
        total = _total.get(id(bot), {}).get(item_id, done[item_id])
        bot.record(f"{NAME}: crafted {item_name(item_id.split('/', 1)[1])} ({done[item_id]}/{total})")   # History: lưu DB
        bot.craft_done(item_id)         # UI: tab Craft trừ 1 số lượng (về 0 thì bỏ tích) và lưu DB, lần Start sau không làm lại


def summary(bot):
    """Cuối lượt: một dòng History tổng kết trang bị đã chế tạo (không có gì thì không ghi)."""
    done = _done.pop(id(bot), {})
    _total.pop(id(bot), None)
    if done:
        text = ", ".join(f"{item_name(item_id.split('/', 1)[1])} x{count}" for item_id, count in done.items())
        bot.record(f"{NAME}: summary: {text}")


def finish_crafting(bot, speed_up) -> bool:
    """Lò rèn đang chế tạo: bấm "Speed Up" (vị trí `speed_up` trong menu) -> Crafting Speedup -> Finish All (xong thì trừ số còn lại) -> nhận trang bị."""
    bot.tap(*speed_up, delay=STEP_WAIT)
    if not finish_all(bot):
        return False
    consume_pending(bot)
    return collect(bot)


def forge_speed_up(bot) -> bool:
    """Lò rèn (đang ở giữa màn, vừa bấm Begin) -> menu -> Speed Up -> Finish All -> nhận trang bị."""
    key, pos = open_menu(bot, NAME, FORGE, {"speed_up": MENU_SPEED_UP})
    return key == "speed_up" and finish_crafting(bot, pos)


@save_errors(KEY)   # lỗi thì lưu `craft_error` vào DB
def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Craft" tab's config."""
    wanted = _remaining.setdefault(id(bot), selected(settings))
    if not wanted:
        _remaining.pop(id(bot), None)
        return
    _total.setdefault(id(bot), dict(wanted))
    craft_rounds(bot, wanted)
    summary(bot)                        # bị ngắt (ngoại lệ) thì không tới đây: số đã làm giữ nguyên cho lượt sau


def craft_rounds(bot, wanted: dict[str, int]):
    bot.log(f"{NAME}: {len(wanted)} items ticked ({sum(wanted.values())} to craft)")
    for _ in range(sum(wanted.values()) + len(wanted) + 2):   # mỗi vòng một trang bị (hoặc tăng tốc cái đang làm dở); trần để không lặp mãi
        if not wanted:
            _remaining.pop(id(bot), None)
            return
        if not reach_building(bot, NAME, FORGE):
            bot.record(f"{NAME}: cannot reach the Forge (route not found), try again next Start")
            return
        key, pos = open_menu(bot, NAME, FORGE, {"speed_up": MENU_SPEED_UP, "craft": MENU_CRAFT})
        if key is None:
            return
        if key == "speed_up":           # đang chế tạo dở (có sẵn hoặc lượt trước bị ngắt): tăng tốc cho xong rồi mới làm tiếp
            if not finish_crafting(bot, pos):
                return
            continue
        _pending.pop(id(bot), None)     # Lò rèn rảnh: lượt trước bị ngắt trước khi Begin có hiệu lực -> trang bị đó vẫn còn trong danh sách
        bot.tap(*pos, delay=STEP_WAIT)
        if bot.wait_for(CRAFT_TITLE, timeout=SCREEN_WAIT) is None:
            bot.record(f"{NAME}: Craft screen not shown")
            return
        started = craft_next(bot, wanted)
        if started is None:
            if bot.find(CRAFT_TITLE) is not None:
                bot.back(delay=STEP_WAIT)       # không còn trang bị nào làm được: đóng màn Craft
            _remaining.pop(id(bot), None)
            return
        bot.record(f"{NAME}: {started}: crafting started")      # chưa trừ: trừ sau khi tăng tốc xong (consume_pending)
        if not forge_speed_up(bot):
            return
    bot.record(f"{NAME}: stopped after too many rounds")


# Dòng cho bot/worker/priority.py: chỉ cần tích ít nhất một trang bị.
JOB = {"run": run, "enabled": lambda settings: bool(selected(settings))}
