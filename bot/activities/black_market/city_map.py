"""
city_map.py — (chỉ activity Black Market; Event / nhiệm vụ Daily vẫn đi bằng nút Go) bản đồ thành theo từng thiết bị: biết công trình nào ở đâu để đi tới bất kỳ công trình nào (VD Chợ cho
activity Black Market) từ chỗ camera đang đứng, không cần nút Go của nhiệm vụ.

Ô đất trong thành ở cùng chỗ trên mọi tài khoản (chỉ khác ô nào xây công trình gì; Thành chính / Đền thờ / Tường thành /
Battlefield / Art Hall / Defense Force đứng yên). Toạ độ bản đồ = toạ độ "ngón tay" tính từ Thành chính ở giữa màn
(CENTER): công trình b ở toạ độ V_b nghĩa là từ Thành chính ở giữa, vuốt tổng cộng V_b (ngón tay, px) thì b vào giữa.
Vuốt chậm (SWIPE_TIME) thì nội dung dịch gần đúng bằng cú vuốt.

- scan(bot, name): đang ở Thành chính (VD sau Go nhiệm vụ Gold Levy) -> đi vòng các ô theo city_tour.json, mỗi ô kéo
  bù công trình giữa màn vào giữa; ghi mọi công trình nhận ra được (ảnh mẫu civ / ảnh tự học của event/city_building) với toạ
  độ bản đồ; công trình đã ghi thấy lại thì dùng để chỉnh vị trí camera (không dồn sai số). Trả {công trình: [x, y]}.
- goto(bot, name, building, city_map): tìm trên màn một công trình đã có trong bản đồ -> biết camera đang ở đâu ->
  vuốt thẳng (chia đều thành vài cú) tới `building` -> kéo bù vào giữa. Trả vị trí `building` trên màn, hoặc None.
Mỗi bước kiểm tra còn ở màn thành (city_screen: hộp thoát game -> Cancel, popup khác -> Back). Đo trên 21913 / 21943.
"""
import json
import math
from pathlib import Path

from ..daily_activities.constants import MAIN_MORE
from ..event.city_building import (
    ACADEMY,
    ARCHER_CAMP,
    ARCHER_TOWER,
    ART_HALL,
    BARRACKS,
    BATTLEFIELD,
    BUILDING_THRESHOLD,
    DEFENSE_FORCE,
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
    _candidates,
)

TOUR = json.loads(Path(__file__).with_name("city_tour.json").read_text(encoding="utf-8"))
# Công trình nhận ra khi quét / đi (có ảnh mẫu trong Images/Event/Building/civ<N>/ hoặc ảnh tự học).
BUILDINGS = (KEEP, MARKET, HOSPITAL, FORGE, BARRACKS, STABLES, ARCHER_CAMP, WORKSHOP, DEFENSE_FORCE, ACADEMY, SHRINE,
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


def swipe(bot, finger):
    """Một cú vuốt chậm `finger` (ngón tay, px) đối xứng quanh SWIPE_CENTER."""
    city_screen(bot)
    cx, cy = SWIPE_CENTER
    fx, fy = finger
    bot.swipe(int(cx - fx / 2), int(cy - fy / 2), int(cx + fx / 2), int(cy + fy / 2),
              duration=SWIPE_TIME, delay=SWIPE_WAIT)


def swipe_from_to(bot, start, end):
    """Một cú vuốt chậm đúng điểm đầu / cuối (cú đo sẵn trong city_tour.json)."""
    city_screen(bot)
    bot.swipe(*start, *end, duration=SWIPE_TIME, delay=SWIPE_WAIT)


def _offset(pos):
    return pos[0] - CENTER[0], pos[1] - CENTER[1]


def centre(bot, building: str, pos):
    """Kéo bù `building` (đang ở `pos`) vào giữa màn. Trả (vị trí mới, cú vuốt tổng đã dùng)."""
    used = [0, 0]
    for _ in range(CENTER_TRIES):
        dx, dy = _offset(pos)
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


def scan(bot, name: str) -> dict:
    """Đang ở Thành chính (giữa màn): đi vòng các ô (city_tour.json), ghi toạ độ bản đồ mọi công trình nhận ra được.
    Trả {công trình: [x, y]} ({} nếu không thấy Thành chính lúc bắt đầu)."""
    screen = city_screen(bot)
    score, keep = locate(bot, screen, KEEP)
    if keep is None or score < BUILDING_THRESHOLD:
        bot.record(f"{name}: city scan needs the Keep at the centre, not found")
        return {}
    city_map = {KEEP: [0, 0]}
    cam = list(_offset(keep))      # toạ độ bản đồ của giữa màn hiện tại
    for plot in TOUR:
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
            _, (ux, uy) = centre(bot, middle[0], middle[1])
            cam[0] += ux
            cam[1] += uy
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
    for _ in range(GOTO_TRIES):
        screen = city_screen(bot)
        score, pos = locate(bot, screen, building)
        if pos is not None and score >= BUILDING_THRESHOLD:
            return centre(bot, building, pos)[0]
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
