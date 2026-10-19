"""
city_map.py — (Event / nhiệm vụ Daily vẫn đi bằng nút Go; dùng cho Black Market và tìm route khi rảnh) bản đồ thành theo từng thiết bị: biết công trình nào ở đâu để đi tới bất kỳ công trình nào (VD Chợ cho
activity Black Market) từ chỗ camera đang đứng, không cần nút Go của nhiệm vụ.

Ô đất trong thành ở cùng chỗ trên mọi tài khoản (chỉ khác ô nào xây công trình gì; Thành chính / Đền thờ / Tường thành /
Battlefield / Art Hall / Trap Factory đứng yên). Toạ độ bản đồ = toạ độ "ngón tay" tính từ Thành chính ở giữa màn
(CENTER): công trình b ở toạ độ V_b nghĩa là từ Thành chính ở giữa, vuốt tổng cộng V_b (ngón tay, px) thì b vào giữa.
Vuốt chậm (SWIPE_TIME) thì nội dung dịch gần đúng bằng cú vuốt.

- scan(bot, name): đang ở Thành chính (VD sau Go nhiệm vụ Gold Levy) -> đi vòng các ô theo city_tour.py của civ (civ<N>/), mỗi ô kéo
  bù công trình giữa màn vào giữa; ghi mọi công trình nhận ra được (ảnh mẫu civ / ảnh tự học của event/city_building) với toạ
  độ bản đồ; công trình đã ghi thấy lại thì dùng để chỉnh vị trí camera (không dồn sai số). Trả {công trình: [x, y]}.
- goto(bot, name, building, city_map): tìm trên màn một công trình đã có trong bản đồ -> biết camera đang ở đâu ->
  vuốt thẳng (chia đều thành vài cú) tới `building` -> kéo bù vào giữa. Trả vị trí `building` trên màn, hoặc None.
Mỗi bước kiểm tra còn ở màn thành (city_screen: hộp thoát game -> Cancel, popup khác -> Back). Đo trên 21913 / 21943.
"""
import math

import numpy as np

from ..activities.daily_activities.constants import MAIN_MORE
from ..common.go_home import TO_CITY, TO_CITY_REGION, TO_CITY_WAIT
from ..activities.event.city_building import (
    ACADEMY,
    ARCHER_CAMP,
    ARCHER_TOWER,
    ART_HALL,
    BARRACKS,
    BATTLEFIELD,
    BUILDING_THRESHOLD,
    TRAP_FACTORY,
    DRAGON_CLIFF,
    EMBASSY,
    FORGE,
    HOLY_PALACE,
    HOSPITAL,
    ICE_LAND,
    KEEP,
    MARKET,
    PASTURE,
    PRISON,
    RALLY_SPOT,
    RESEARCH_FACTORY,
    SHRINE,
    STABLES,
    SUBORDINATE_CITY,
    TAVERN,
    TRIUMPHAL_ARCH,
    VICTORY_COLUMN,
    WALLS,
    WAR_HALL,
    WATCHTOWER,
    WONDER,
    WORKSHOP,
    _assign,
    _best_match,
    _candidates,
)

from .tours import FIXED_NAMES, TOURS
# Công trình nhận ra khi quét / đi (có ảnh mẫu trong Images/Building/civ<N>/ hoặc ảnh tự học).
BUILDINGS = (KEEP, MARKET, HOSPITAL, FORGE, BARRACKS, STABLES, ARCHER_CAMP, WORKSHOP, TRAP_FACTORY, ACADEMY, SHRINE,
             ART_HALL, BATTLEFIELD, PASTURE, WALLS, EMBASSY, PRISON, TAVERN, RESEARCH_FACTORY, HOLY_PALACE, ICE_LAND,
             RALLY_SPOT, VICTORY_COLUMN, TRIUMPHAL_ARCH, WATCHTOWER, ARCHER_TOWER, DRAGON_CLIFF, SUBORDINATE_CITY,
             WONDER, WAR_HALL)
CENTER = (197, 345)          # giữa màn: chỗ công trình đứng sau Go (đo ảnh mẫu civ1 keep 1,00)
SWIPE_CENTER = (190, 340)    # cú vuốt tách nhỏ đối xứng quanh đây (không chạm nút UI)
MAX_SWIPE = (240, 260)       # một cú tách nhỏ dài tối đa (điểm đầu / cuối trong x 70 .. 310, y 210 .. 470)
SWIPE_TIME = 2.5             # giây: vuốt chậm, gần như hết quán tính
SWIPE_WAIT = 2               # giây chờ camera dừng sau một cú
TOLERANCE = 25               # px lệch giữa màn cho phép; hơn thì kéo bù
PLOT_RADIUS = (110, 110)     # công trình của ô đang quét: cách giữa màn không quá chừng ấy (mỗi trục)
CENTER_TRIES = 2             # số cú kéo bù tối đa
GOTO_TRIES = 3               # số lượt (tìm mốc -> vuốt) tối đa khi đi tới công trình
SEARCH_LIMIT = 40           # số cú vuốt tối đa khi dò mốc (find_keep)
BOSS_CHECK_EVERY = 3         # cứ chừng ấy cú vuốt thì gọi bot.swipe_watch (kiểm tra boss mới, xem scan_city)
TO_CITY_TRIES = 3
HOME_BACKS = 6               # số lần Back tối đa để về màn thành (scan_city)
CITY_BACKS = 3               # số lần Back tối đa để đóng popup che màn thành
EXIT_DIALOG = "en/exitGame.png"     # "Are you sure you want to exit the game?" (Back ở màn thành mở hộp này)
EXIT_CANCEL = "en/exitCancel.png"
EXIT_THRESHOLD = 0.85


def city_screen(bot):
    """Ảnh màn hình khi đang ở màn thành (nút "•••" hiện). Hộp hỏi thoát game -> Cancel; popup khác che -> Back, tối
    đa CITY_BACKS lần. Không Back khi màn thành đã sạch (Back lúc đó mở hộp hỏi thoát game)."""
    screen = bot.screenshot()
    for _ in range(CITY_BACKS):
        if bot.find(EXIT_DIALOG, threshold=EXIT_THRESHOLD, screen=screen) is not None:
            cancel = bot.find(EXIT_CANCEL, threshold=EXIT_THRESHOLD, screen=screen)
            if cancel is not None:
                bot.tap(*cancel, delay=1)
                screen = bot.screenshot()
                continue
        if bot.find(MAIN_MORE, screen=screen) is not None:
            break
        bot.back(delay=1)
        screen = bot.screenshot()
    return screen


def locate(bot, screen, building: str):
    """(điểm khớp, tâm) tốt nhất của `building` trên `screen` (ảnh mẫu civ / ảnh tự học), hoặc (0, None)."""
    best = (0.0, None)
    for _owner, image in _candidates(bot, (building,)):
        score, pos = bot.best_match(image, screen=screen)
        if pos is not None and score > best[0]:
            best = (score, pos)
    return best


def visible(bot, screen, buildings=None) -> dict:
    """{công trình: tâm trên màn} các công trình trong `buildings` (mặc định BUILDINGS) nhận ra được trên `screen`."""
    found = {}
    for building in BUILDINGS if buildings is None else buildings:
        score, pos = locate(bot, screen, building)
        if pos is not None and score >= BUILDING_THRESHOLD:
            found[building] = pos
    return found


def split(finger) -> list[tuple[int, int]]:
    """Cú vuốt tổng `finger` chia đều thành ít cú thẳng hàng nhất, mỗi cú vừa MAX_SWIPE."""
    fx, fy = finger
    n = max(math.ceil(abs(fx) / MAX_SWIPE[0]), math.ceil(abs(fy) / MAX_SWIPE[1]))
    return [(round(fx / n), round(fy / n))] * n if n else []


def _swiped(bot):
    """Sau mỗi cú vuốt: cứ BOSS_CHECK_EVERY cú thì gọi bot.swipe_watch() nếu có (scan_city gán; xem đó)."""
    watch = getattr(bot, "swipe_watch", None)
    if watch is None:
        return
    bot.swipe_count = getattr(bot, "swipe_count", 0) + 1
    if bot.swipe_count % BOSS_CHECK_EVERY == 0:
        watch(bot)


# Điểm đầu thay thế khi một cú vuốt không làm màn hình đổi (điểm đầu trúng icon / rương / dấu hỏi nên game coi là bấm): dịch điểm
# đầu và cuối cùng một độ, giữ nguyên hướng và độ dài.
RETRY_SHIFTS = [(0, 0), (0, -110), (0, 110), (-70, -60), (70, 60)]
MOVED_DIFF = 6               # độ khác nhau trung bình (0-255) của hai ảnh (bỏ thanh trên / dưới) coi là màn hình đã đổi


def _moved(before, after) -> bool:
    """Màn hình có đổi giữa `before` và `after` không (vùng giữa, bỏ thanh trên và nút dưới)."""
    return float(np.abs(before[130:560].astype(np.int16) - after[130:560].astype(np.int16)).mean()) > MOVED_DIFF


def _swipe_checked(bot, start, end):
    """Vuốt từ `start` tới `end`; nếu màn hình không đổi thì vuốt lại bằng điểm đầu khác (RETRY_SHIFTS) vì có thể điểm đầu trúng
    icon trong thế giới (game coi là bấm). Không kiểm tra được (ảnh không phải ma trận, VD test) thì vuốt một lần."""
    before = city_screen(bot)
    checkable = isinstance(before, np.ndarray)
    for dx, dy in RETRY_SHIFTS:
        x1, y1, x2, y2 = start[0] + dx, start[1] + dy, end[0] + dx, end[1] + dy
        if (dx, dy) != (0, 0) and not all(8 <= x <= 388 and 135 <= y <= 555 for x, y in ((x1, y1), (x2, y2))):
            continue      # điểm đầu thay thế phải nằm trong vùng vuốt an toàn (cú gốc luôn được vuốt đúng như đo)
        bot.swipe(x1, y1, x2, y2, duration=SWIPE_TIME, delay=SWIPE_WAIT)
        if not checkable:
            break
        after = bot.screenshot()
        if _moved(before, after):
            break
        bot.log(f"city swipe did not move the screen, retry with another start point ({dx}, {dy})")
    _swiped(bot)


def swipe(bot, finger):
    """Một cú vuốt chậm `finger` (ngón tay, px) đối xứng quanh SWIPE_CENTER."""
    cx, cy = SWIPE_CENTER
    fx, fy = finger
    _swipe_checked(bot, (int(cx - fx / 2), int(cy - fy / 2)), (int(cx + fx / 2), int(cy + fy / 2)))


def swipe_from_to(bot, start, end):
    """Một cú vuốt chậm đúng điểm đầu / cuối (cú đo sẵn trong city_tour.py)."""
    _swipe_checked(bot, start, end)


def _offset(pos):
    return pos[0] - CENTER[0], pos[1] - CENTER[1]


def centre(bot, building: str, pos, anchor_shift=None):
    """Kéo bù `building` (đang ở `pos`) vào giữa màn (công trình trong `anchor_shift` = ANCHOR_SHIFT của civ: tới tâm riêng của
    nó). Trả (vị trí mới, cú vuốt tổng đã dùng)."""
    used = [0, 0]
    shift = (anchor_shift or {}).get(building, (0, 0))
    for _ in range(CENTER_TRIES):
        dx, dy = _offset(pos)
        dx, dy = dx - shift[0], dy - shift[1]
        if abs(dx) <= TOLERANCE and abs(dy) <= TOLERANCE:
            break
        finger = (max(-MAX_SWIPE[0], min(MAX_SWIPE[0], -dx)), max(-MAX_SWIPE[1], min(MAX_SWIPE[1], -dy)))
        swipe(bot, finger)
        used[0] += finger[0]
        used[1] += finger[1]
        score, new = locate(bot, city_screen(bot), building)
        if new is None or score < BUILDING_THRESHOLD:
            break
        pos = new
    return pos, tuple(used)


def scan(bot, name: str, tour) -> dict:
    """Đang ở Thành chính (giữa màn): đi vòng các ô của `tour` (city_tour.py của civ), ghi toạ độ bản đồ mọi công trình nhận ra được.
    Trả {công trình: [x, y]} ({} nếu không thấy Thành chính lúc bắt đầu)."""
    screen = city_screen(bot)
    score, keep = locate(bot, screen, KEEP)
    if keep is None or score < BUILDING_THRESHOLD:
        bot.record(f"{name}: city scan needs the Keep at the centre, not found")
        return {}
    city_map = {KEEP: [0, 0]}
    cam = list(_offset(keep))      # toạ độ bản đồ của giữa màn hiện tại
    for plot in tour.DATA:
        for start, end in plot["swipes"]:
            swipe_from_to(bot, start, end)
            cam[0] += end[0] - start[0]
            cam[1] += end[1] - start[1]
        screen = city_screen(bot)
        found = visible(bot, screen)
        _anchor(cam, found, city_map)
        for building, pos in found.items():
            if building not in city_map:
                dx, dy = _offset(pos)
                city_map[building] = [cam[0] - dx, cam[1] - dy]
                bot.log(f"{name}: plot {plot['plot']}: {building} at {city_map[building]}")
        near = {b: p for b, p in found.items()
                if abs(_offset(p)[0]) <= PLOT_RADIUS[0] and abs(_offset(p)[1]) <= PLOT_RADIUS[1]}
        middle = min(near.items(), key=lambda kv: abs(_offset(kv[1])[0]) + abs(_offset(kv[1])[1]), default=None)
        if middle is not None:      # công trình của ô (gần giữa màn) -> kéo bù, không kéo về công trình ô khác
            _, (ux, uy) = centre(bot, middle[0], middle[1], tour.ANCHOR_SHIFT)
            cam[0] += ux
            cam[1] += uy
    for building, view in tour.FIXED.items():      # công trình cố định: không quét, thêm sẵn toạ độ đã đo
        city_map.setdefault(building, list(view))
    bot.record(f"{name}: city scanned, {len(city_map)} buildings: {', '.join(sorted(city_map))}")
    return city_map


def _anchor(cam: list, found: dict, city_map: dict):
    """Chỉnh toạ độ camera theo công trình đã có trong bản đồ đang thấy trên màn (không dồn sai số vuốt)."""
    known = [(building, pos) for building, pos in found.items() if building in city_map]
    if not known:
        return
    xs = [city_map[b][0] + _offset(p)[0] for b, p in known]
    ys = [city_map[b][1] + _offset(p)[1] for b, p in known]
    cam[0], cam[1] = round(sum(xs) / len(xs)), round(sum(ys) / len(ys))


def goto(bot, name: str, building: str, city_map: dict):
    """Đưa `building` vào giữa màn dùng bản đồ `city_map`: tìm trên màn một công trình đã có trong bản đồ, vuốt thẳng
    tới. Trả vị trí `building` trên màn, hoặc None (không có trong bản đồ / không thấy mốc nào trên màn)."""
    if building not in city_map:
        return None
    target = city_map[building]
    shifts = None
    for _ in range(GOTO_TRIES):
        screen = city_screen(bot)
        if shifts is None:
            shifts = getattr(tour_of(bot, screen), "ANCHOR_SHIFT", {})
        score, pos = locate(bot, screen, building)
        if pos is not None and score >= BUILDING_THRESHOLD:
            return centre(bot, building, pos, shifts)[0]
        found = visible(bot, screen, [b for b in city_map if b != building])
        if not found:
            bot.log(f"{name}: no known building on screen")
            return None
        cam = [0, 0]
        _anchor(cam, found, city_map)
        moves = split((target[0] - cam[0], target[1] - cam[1]))
        bot.log(f"{name}: go to {building} from {', '.join(found)}: {len(moves)} swipe(s) {moves[:1]}")
        for move in moves:
            swipe(bot, move)
    score, pos = locate(bot, city_screen(bot), building)
    return pos if pos is not None and score >= BUILDING_THRESHOLD else None


def spiral_swipes(limit: int = SEARCH_LIMIT) -> list[tuple[int, int]]:
    """Các cú vuốt (ngón tay dx, dy) đi vòng xoáy vuông quanh chỗ đang đứng: phải 1, xuống 1, trái 2, lên 2, phải 3, xuống 3...
    Ô ngang = 1 cú MAX_SWIPE[0] (240 px, màn rộng 396 nên hai bước liền kề chồng nhau); ô dọc = 2 cú MAX_SWIPE[1] (520 px, màn
    cao 704). Vòng xoáy phủ kín một vùng quanh chỗ đứng (không như đường vuông thưa), dừng ở `limit` cú. Mô phỏng: từ mọi chỗ
    trong thành thấy một trong bốn mốc cố định sau tối đa ~19 cú."""
    moves, dirs, length, turn = [], [(1, 0), (0, 1), (-1, 0), (0, -1)], 1, 0
    while len(moves) < limit:
        for _ in range(2):
            ux, uy = dirs[turn % 4]
            for _ in range(length):
                moves += [(ux * MAX_SWIPE[0], 0)] if ux else [(0, uy * MAX_SWIPE[1])] * 2
            turn += 1
        length += 1
    return moves[:limit]


def civ_of(bot, screen) -> int | None:
    """Nền văn minh của thành đang hiện: bot.civilization nếu đã biết, không thì civ của ảnh mẫu (Thành chính / công trình cố định)
    khớp nhất trên `screen` (từ BUILDING_THRESHOLD). None nếu chưa biết."""
    civ = getattr(bot, "civilization", None)
    if civ:
        return civ
    best_score, best_civ = BUILDING_THRESHOLD, None
    for owner, image in _candidates(bot, (KEEP, *FIXED_NAMES)):
        score, pos = bot.best_match(image, screen=screen)
        if owner and pos is not None and score >= best_score:
            best_score, best_civ = score, owner
    return best_civ


def update_civ(bot, name: str, screen) -> int | None:
    """Nhận nền văn minh của thành đang hiện từ Thành chính / công trình cố định, so ảnh mẫu của MỌI nền văn minh (không chỉ
    civ đã lưu). Khác civ đang lưu (hoặc chưa lưu) thì cập nhật DB (city_building._assign: bot.set_civilization). Trả civ vừa
    cập nhật, None nếu không đổi / không nhận ra."""
    names = (KEEP, *FIXED_NAMES)
    if _best_match(bot, _candidates(bot, names), screen) is not None and getattr(bot, "civilization", None):
        return None      # thấy ảnh của civ đã lưu: đúng rồi, không đổi
    best = _best_match(bot, _candidates(bot, names, others=True), screen)   # không thấy civ đã lưu: thử ảnh các civ còn lại
    if best is None:
        best = _best_match(bot, _candidates(bot, names), screen)           # chưa lưu civ: ảnh của mọi civ
    old = getattr(bot, "civilization", None)
    if best is None or best[1] is None or best[1] == old:
        return None
    bot.record(f"{name}: civilization changed {old} -> {best[1]}")
    _assign(bot, name, best[1])
    if old:
        bot.set_city_map({})    # bản đồ thành cũ thuộc civ cũ, không còn đúng
    return best[1]


def tour_of(bot, screen):
    """Dữ liệu route (module civ<N>/city_tour.py) của thành đang hiện: theo civ_of; chưa biết civ thì dùng civ1; civ chưa đo đủ -> None."""
    civ = civ_of(bot, screen)
    return TOURS.get(civ if civ is not None else 1)


def find_keep(bot, name: str):
    """Đưa Thành chính vào giữa màn (bước đầu của quét route: các ô sau đều đi từ Thành chính). Mọi nhiệm vụ đã xong nên không
    còn nút Go để nhờ game kéo Thành chính vào giữa, phải tự tìm:
    0. Mỗi màn: nhận nền văn minh (update_civ), khác civ trong DB thì cập nhật.
    1. Thấy Thành chính -> kéo bù vào giữa.
    2. Thấy một công trình cố định (FIXED: Tường thành / Research Factory / Tavern) -> kéo nó vào giữa màn rồi vuốt đúng
       đường cố định về Thành chính (ROUTES, đo sẵn) -> kéo bù Thành chính vào giữa.
    3. Không thấy mốc nào -> dò vòng xoáy (spiral_swipes, mỗi cú xong kiểm tra lại), thấy một mốc là dừng và về Thành chính ngay.
    Trả dữ liệu route của civ (module civ<N>/city_tour.py) khi Thành chính đã ở giữa màn; None nếu dò hết mà không thấy, civ chưa có
    route, hoặc đi xong mà không thấy Thành chính."""
    for move in [None, *spiral_swipes()]:
        if move is not None:
            swipe(bot, move)
        screen = city_screen(bot)
        update_civ(bot, name, screen)   # civ khác civ trong DB -> cập nhật (trước khi tìm, vì ảnh mẫu tìm theo civ đã lưu)
        found = visible(bot, screen, [KEEP, *FIXED_NAMES])
        if not found:
            continue
        civ = civ_of(bot, screen)
        tour = TOURS.get(civ if civ is not None else 1)
        if tour is None:
            bot.record(f"{name}: civ {civ} has no route data yet (only civ {', '.join(map(str, TOURS))}), skip city scan")
            return None
        if KEEP in found:
            return tour if centre(bot, KEEP, found[KEEP], tour.ANCHOR_SHIFT)[0] is not None else None
        anchor = next((b for b in tour.FIXED if b in found), None)
        if anchor is None:
            continue      # mốc thấy được không thuộc civ này (nhận nhầm): dò tiếp
        pos, _ = centre(bot, anchor, found[anchor], tour.ANCHOR_SHIFT)
        bot.log(f"{name}: {anchor} found, fixed route to the Keep: {len(tour.ROUTES[(anchor, KEEP)])} swipe(s)")
        for finger in tour.ROUTES[(anchor, KEEP)]:
            swipe(bot, finger)
        score, keep = locate(bot, city_screen(bot), KEEP)
        if keep is None or score < BUILDING_THRESHOLD:
            bot.log(f"{name}: Keep not recognised after the fixed route, keep searching")
            continue
        centre(bot, KEEP, keep, tour.ANCHOR_SHIFT)
        return tour
    return None


def ensure_city(bot, name: str):
    """Đang ở bản đồ thế giới (có nút toà thành ở góc dưới phải, TO_CITY) thì bấm nút đó để về thành (camera thành đặt về chỗ
    mặc định của game, bước tìm Thành chính lo phần còn lại)."""
    for _ in range(TO_CITY_TRIES):
        button = bot.find(TO_CITY, region=TO_CITY_REGION)
        if button is None:
            return
        bot.log(f"{name}: on the world map, tap the city button")
        bot.tap(*button, delay=TO_CITY_WAIT)


def scan_city(bot, name: str, watch=None) -> bool:
    """Quét route công trình rồi lưu bản đồ thành vào DB (bot.set_city_map; không lưu file). Gọi khi hết nhiệm vụ và Join Boss
    rảnh, máy chưa có bản đồ. Ở vị trí bất kỳ:
    0. ensure_city: đang ở bản đồ thế giới thì bấm nút về thành.
    1. find_keep: tìm Thành chính (thấy Thành chính / một công trình cố định thì đi thẳng tới Thành chính; không thấy gì thì dò
       vòng xoáy quanh chỗ đứng).
    2. scan: đi từng ô route (city_tour.py của civ), ghi toạ độ công trình nhận ra.
    3. lưu bản đồ vào DB.
    `watch(bot)`: gọi lúc bắt đầu và cứ BOSS_CHECK_EVERY cú vuốt (kiểm tra boss mới, worker làm: số boss tăng thì vào Join Boss
    tới khi rảnh rồi mới vuốt tiếp). Trả True khi đã quét và lưu; False khi chưa quét được (không tìm được Thành chính...)."""
    bot.swipe_watch = watch
    bot.swipe_count = 0
    try:
        ensure_city(bot, name)
        for _ in range(HOME_BACKS):
            if bot.find(MAIN_MORE) is not None:
                break
            bot.back(delay=1)
        if bot.find(MAIN_MORE) is None:
            bot.record(f"{name}: scan city: not at the city screen")
            return False
        if watch is not None:
            watch(bot)      # ghi số boss ban đầu
        tour = find_keep(bot, name)
        if tour is None:
            bot.record(f"{name}: scan city: cannot find the Keep (no Keep / fixed building found, or civ has no route data), skip")
            return False
        found = scan(bot, name, tour)
        if not found:
            return False
        bot.set_city_map(found)
        return True
    finally:
        bot.swipe_watch = None
