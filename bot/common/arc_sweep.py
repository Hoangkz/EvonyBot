"""
arc_sweep.py — kéo bản đồ thế giới để quét hết một hình quạt quanh chỗ camera đang đứng (dò boss; chưa có phần nhận boss,
chỉ lo kéo camera, nhận boss gắn qua `on_step`).

Gốc = chỗ camera đứng lúc gọi (tâm hình tròn). Góc tính THEO MÀN HÌNH nhìn từ trên xuống (bỏ méo của góc nhìn xéo), 0 .. 360: 0° = ngang
sang phải, 90° = thẳng lên, 180° = sang trái, 270° = xuống; quạt đi từ góc bắt đầu NGƯỢC chiều kim đồng hồ trên màn hình tới góc kết thúc
(345 -> 15 = 30° quanh hướng phải; 60 -> 120 = 60° quanh hướng lên; 0 -> 360 = cả vòng). Bên trong đổi sang góc toạ độ game
(screen_to_world_deg: góc game = -45 - góc màn hình, vì "phải" trên màn hình = hướng X tăng, Y giảm). Bán kính tính
bằng "km" của game = khoảng cách Euclid trong toạ độ X:Y (1 km = 1 đơn vị toạ độ).

Bản đồ thế giới nhìn xéo: cuộn sang phải thì X tăng, Y giảm; cuộn xuống thì X, Y cùng tăng. Đo ở zoom hiện tại:
    px_ngang = 54 * (dX - dY)      px_dọc = 33 * (dX + dY)        (px ngón tay)

MỌI cú kéo đều dài STEP px, ngang hoặc dọc, không cú ngắn, không kéo bù; riêng cú dọc cuối của mỗi tầng (ngay trước cú ngang sang tầng kế)
được gộp với cú ngang đó thành MỘT cú chéo (STEP, STEP) khi ô ở góc không còn cần ghé. Màn hình nhìn được
VIEW px nên hai màn kề nhau chỉ chồng ở rìa. Bản đồ là lưới ô STEP x STEP px quanh gốc; ô nào có màn hình chạm vào quạt thì phải ghé.
Đường đi (sweep_path) là chuỗi ô kề nhau, quét từng "tầng" ô theo hướng ra xa (gần trước xa sau, không bao giờ kéo về phía gốc),
trong tầng đi từ đầu này sang đầu kia (kiểu cắt cỏ). Hàm thử 4 cách (tầng theo cột / hàng, chiều + / -), loại cách bỏ sót vùng quạt,
chọn cách ít cú kéo nhất.
Mỗi ô gọi on_step. Sau mỗi cú kéo đọc X:Y thật (bot/ocr/read_camera.py) chỉ để ghi log độ lệch so với ô dự tính.
"""
import heapq
import math

import numpy as np

from ..ocr import read_camera
from ..city.city_map import SWIPE_CENTER, _moved

HOME_ICON = "CityMap/worldHome.png"   # nút hình toà thành ở thanh dưới bản đồ thế giới: bấm để camera về thành của mình
HOME_WAIT = 2.5              # giây chờ camera chạy về thành sau khi bấm
RADIUS = 300                 # km: bán kính quét mặc định
PX_X, PX_Y = 54, 33          # px ngón tay mỗi đơn vị toạ độ (xem trên); đo lại từ 74 cú kéo thật trên 21913 (60 / 30 cũ làm camera trôi ~10% mỗi cú)
SWIPE_AREA = (8, 60, 388, 640)  # (x1, y1, x2, y2) px: vùng ngón tay được phép đi (đầu và cuối cú kéo), bản đồ chạy gần hết màn hình 396 x 704
MIN_SWIPE = 110              # px: cú kéo ngắn hơn mức này dễ bị game coi là bấm: gộp với cú kề
SWIPE_FULL_V = 520           # px: một cú kéo dọc dài tối đa (đầu / cuối trong y 90 .. 610 quanh SWIPE_CENTER), dài hơn cú ngang vì bản đồ nhìn được cao hơn rộng
SWIPE_FULL = 340             # px: một cú kéo dài tối đa theo ngang (đầu / cuối trong x 20 .. 360, không chạm nút UI) = gần hết màn hình
STEP_FRAC = 0.95             # mỗi cú chỉ kéo chừng này so với SWIPE_FULL (không kéo hết màn hình): hai màn kề nhau chồng nhiều hơn nên chịu được camera lệch vài km
STEP = round(SWIPE_FULL * STEP_FRAC)   # px: độ dài mỗi cú kéo (323 với 0,95)
VIEW = (396, 590)            # px: phần bản đồ nhìn được: cả bề rộng màn hình 396, cao y ~ 50 .. 640 (đo từ ảnh chụp thật: chỉ thanh tài nguyên trên, khung chat dưới và các nút hai bên đứng yên đè lên bản đồ, màn hình 396 x 704)
MAP_SIZE = 1200              # toạ độ bản đồ thế giới 0 .. 1199; ô có tâm ngoài bản đồ không gọi on_step
SWIPE_TIME = 1.2             # giây: thời gian một cú kéo
SWIPE_WAIT = 1.2             # giây chờ camera dừng sau một cú
RETRY_SHIFTS = [(0, 0), (0, -30), (0, 30), (-60, 0), (60, 0)]    # điểm đầu trúng icon thế giới thì game coi là bấm: dời cả cú kéo (cùng độ dài) rồi thử lại
COVER_SAMPLES = 1500         # số điểm lấy mẫu trong quạt để kiểm tra một cách đi có phủ kín không
RESYNC_DRIFT = 6             # km: camera lệch ô dự tính hơn mức này thì gọi resync (nhập toạ độ chậm hơn kéo nên chỉ làm khi thật sự trôi)
COVER_MIN = 0.995            # tỉ lệ quạt tối thiểu phải nằm trong tầm nhìn
MERGE_LOSS_MAX = 3.0         # km2: một lần gộp chéo được bỏ sót tối đa chừng này (~ 7% một màn hình), để không dồn hở vào một chỗ
EDGE_MARGIN = 3.0            # km: phần quạt cách hai mép bên (tia góc bắt đầu / kết thúc) gần hơn mức này không bắt buộc phải thấy (đứng ở trong cũng thấy mép) khi quét no_back
FWD_STEPS = tuple(STEP - 10 * k for k in range(9))   # px: thử độ dài cú kéo từ lớn tới nhỏ (STEP, STEP - 10, ...) cho tới khi phủ đủ (mọi cú trong một đường đi cùng độ dài)
UI_BLOCKS = [(322, 35, 396, 300), (322, 440, 396, 704), (0, 440, 75, 704), (0, 35, 80, 130), (150, 525, 322, 704)]    # (x1, y1, x2, y2) vùng nút giao diện (đo trên 21913, ảnh 396 x 704; vùng cuối là nút về thành, cờ, tim và thanh toạ độ / chat ở giữa đáy màn hình): cú kéo bắt đầu ở đây thì game coi là bấm nút
FWD_CUT_EXTRA = 6.0          # km: khi cắt mẫu theo bán kính, còn lấy thêm một tầng nếu tâm nó cách gốc không quá bán kính + chừng này
FWD_SPAN_MAX = 90            # độ: quạt rộng hơn mức này không quét no_back (phần phía sau gốc cần đi lùi), dùng cách theo vành / cắt cỏ
RING_BAND = 8                # km: bề dày vành của cách quét theo vành cũ (_rings, khi không dùng no_back)
STAGE_FIRST = 10             # km: chặng đầu tiên của quét gần -> xa: thấy hết cung trong bán kính này trước
STAGE_STEP = 5               # km: các chặng sau tăng thêm chừng này (10, 15, 20, ... tới bán kính cần quét): xong một chặng thì toàn bộ cung trong bán kính của chặng đã được thấy
PIECE_DEG = 30               # độ: cung rộng hơn mức này chia thành các phần nhỏ đều nhau <= chừng này (<= FWD_SPAN_MAX)
BAND_KM = 50                 # km: cung rộng (nhiều phần) quét theo từng dải bán kính rộng chừng này: xong dải gần gốc của MỌI phần (về thành giữa các phần) mới sang dải xa hơn (0 = quét xong từng phần mới sang phần khác)
REVISIT_COST = 6             # khi phải đi vòng, qua một ô đã đi tốn chừng này lần một ô chưa đi (tránh đường đi đè lên nhau)
CIRC_INSET = 2.0             # km: kiểu quét theo vòng tròn: tâm camera cách hai mép bên của cung ít nhất chừng này (màn hình đứng bên trong vẫn thấy mép)
TAIL_MIN_FRAC = 0.2           # bỏ các cú cuối chỉ phủ thêm < chừng này (so với diện tích một màn hình) phần quạt mới
DIAG_LOSS = 0.003            # tỉ lệ diện tích quạt tối đa được phép mất khi gộp cú chéo ở sát mép (tổng cộng, thêm vào phần mất sẵn có; tổng phủ vẫn >= COVER_MIN)
LANE_MAX = 12                # số cú tối đa của đoạn đi thẳng theo phân giác ở đầu đường đi
LANE_SPAN_MAX = 60           # độ: quạt rộng hơn mức này thì không đi thẳng theo phân giác (cung đã rộng hơn màn hình ngay gần gốc)


def world_to_px(u: float, v: float) -> tuple[float, float]:
    """Camera dời (dX, dY) = (u, v) đơn vị toạ độ -> dời bao nhiêu px trên màn hình."""
    return PX_X * (u - v), PX_Y * (u + v)


def px_to_world(px: float, py: float) -> tuple[float, float]:
    a, b = px / PX_X, py / PX_Y
    return (a + b) / 2, (b - a) / 2


def screen_to_world_deg(start_deg: float, end_deg: float) -> tuple[float, float]:
    """Quạt theo góc màn hình (0° = phải, ngược chiều kim đồng hồ trên màn hình) -> quạt theo góc toạ độ game (0° = X tăng) cùng độ rộng.
    Nhìn từ trên xuống, ngược chiều kim đồng hồ trên màn hình = thuận chiều trong toạ độ game nên đảo đầu cuối: game = -45 - màn hình."""
    span = 360.0 if end_deg - start_deg >= 360 else (end_deg - start_deg) % 360
    world_start = (-45 - end_deg) % 360 if span < 360 else 0.0
    return world_start, world_start + span


def in_sector(u: float, v: float, start_deg: float, end_deg: float, radius: float) -> bool:
    """(u, v) (toạ độ game so với gốc) nằm trong quạt từ start_deg ngược chiều kim đồng hồ tới end_deg (góc game), bán kính `radius`."""
    r = math.hypot(u, v)
    if r > radius:
        return False
    span = 360.0 if end_deg - start_deg >= 360 else (end_deg - start_deg) % 360
    if r < 1e-9 or span >= 360:
        return True
    return (math.degrees(math.atan2(v, u)) - start_deg) % 360 <= span + 1e-9


def _on_map(origin, u: float, v: float) -> bool:
    """Điểm cách gốc (u, v) toạ độ có nằm trong bản đồ không (không biết gốc thì coi là có)."""
    return origin is None or (0 <= origin[0] + u < MAP_SIZE and 0 <= origin[1] + v < MAP_SIZE)


def _span(start_deg: float, end_deg: float) -> float:
    return 360.0 if end_deg - start_deg >= 360 else (end_deg - start_deg) % 360


def _seen(centers, x: float, y: float) -> bool:
    """Điểm (x, y) px (so với gốc) có nằm trong màn hình của một tâm camera nào trong `centers` không."""
    return any(abs(x - cx) <= VIEW[0] / 2 and abs(y - cy) <= VIEW[1] / 2 for cx, cy in centers)


def _wedge_box(start_deg: float, end_deg: float, radius: float):
    """Hộp bao (px so với gốc) của quạt, nới thêm một màn hình mỗi phía: (xmin, xmax, ymin, ymax)."""
    span = _span(start_deg, end_deg)
    n = max(2, int(span) + 1)
    pts = [(0.0, 0.0)] + [(radius * math.cos(math.radians(start_deg + span * k / (n - 1))),
                           radius * math.sin(math.radians(start_deg + span * k / (n - 1)))) for k in range(n)]
    pxs = [world_to_px(*p) for p in pts]
    xs, ys = [p[0] for p in pxs], [p[1] for p in pxs]
    return min(xs) - VIEW[0], max(xs) + VIEW[0], min(ys) - VIEW[1], max(ys) + VIEW[1]


def _lane(start_deg: float, end_deg: float, m: int, tilt: float = 0.0):
    """m + 1 điểm (px so với gốc) trên đường thẳng theo phân giác của quạt (lệch `tilt` độ), cách nhau STEP px (mỗi bước một cú kéo STEP px theo hướng đó)."""
    mid = start_deg + _span(start_deg, end_deg) / 2 + tilt
    dx, dy = world_to_px(math.cos(math.radians(mid)), math.sin(math.radians(mid)))
    n = math.hypot(dx, dy)
    return [(k * STEP * dx / n, k * STEP * dy / n) for k in range(m + 1)]


_SAMPLES5 = [(fx, fy) for fx in (-.5, -.25, 0, .25, .5) for fy in (-.5, -.25, 0, .25, .5)]
_SAMPLES15 = [(k / 14 - .5, l / 14 - .5) for k in range(15) for l in range(15)]


def _needed_cells(start_deg: float, end_deg: float, radius: float, origin, anchor, lane) -> set[tuple[int, int]]:
    """Ô lưới (i, j) (tâm = anchor + (i*STEP, j*STEP) px) có màn hình chạm vào phần quạt chưa được `lane` (các điểm dừng trên đường thẳng đầu) thấy,
    và có tâm trong bản đồ."""
    ax, ay = anchor
    xmin, xmax, ymin, ymax = _wedge_box(start_deg, end_deg, radius)
    cells = set()
    for j in range(math.floor((ymin - ay) / STEP), math.ceil((ymax - ay) / STEP) + 1):
        for i in range(math.floor((xmin - ax) / STEP), math.ceil((xmax - ax) / STEP) + 1):
            cx, cy = ax + i * STEP, ay + j * STEP
            if not _on_map(origin, *px_to_world(cx, cy)):
                continue
            for fx, fy in _SAMPLES5:
                x, y = cx + fx * VIEW[0], cy + fy * VIEW[1]
                if in_sector(*px_to_world(x, y), start_deg, end_deg, radius) and not _seen(lane, x, y):
                    cells.add((i, j))
                    break
    return cells


def _prune(cells: set, start_deg: float, end_deg: float, radius: float, origin, anchor, lane) -> set:
    """Bỏ các ô thừa: ô mà phần quạt trong màn hình của nó (lấy mẫu 15x15) đã được các ô còn lại và `lane` thấy hết (đứng ở trong cũng thấy mép
    quạt). Xét ô xa trục quạt trước nên ô sát mép bị bỏ trước."""
    ax, ay = anchor
    mid = start_deg + _span(start_deg, end_deg) / 2
    mx, my = math.cos(math.radians(mid)), math.sin(math.radians(mid))
    kept = set(cells)

    def off_axis(c):                                         # khoảng cách tâm ô tới trục quạt (km)
        u, v = px_to_world(ax + c[0] * STEP, ay + c[1] * STEP)
        return abs(u * my - v * mx)

    for cell in sorted(cells - {(0, 0)}, key=lambda c: -off_axis(c)):
        i, j = cell
        others = list(lane) + [(ax + a * STEP, ay + b * STEP) for a in (i - 1, i, i + 1) for b in (j - 1, j, j + 1)
                               if (a, b) != cell and (a, b) in kept]
        cx, cy = ax + i * STEP, ay + j * STEP
        redundant = True
        for fx, fy in _SAMPLES15:
            x, y = cx + fx * VIEW[0], cy + fy * VIEW[1]
            u, v = px_to_world(x, y)
            if in_sector(u, v, start_deg, end_deg, radius) and _on_map(origin, u, v) and not _seen(others, x, y):
                redundant = False
                break
        if redundant:
            kept.discard(cell)
    return kept


def _snake(cells: set, major: int, sign: int):
    """Đường đi qua các ô kề nhau (mỗi bước ±1 theo i hoặc j). Tầng = ô cùng giá trị sign * c[major], đi theo tầng tăng dần từ 0; mỗi tầng quét từ một đầu sang
    đầu kia. Sang tầng mới: đi ngang nốt ở tầng cũ tới đầu GẦN NHẤT của tầng mới (qua các ô chưa thăm khi tầng mới rộng hơn) rồi mới tiến, để vào tầng ở một
    đầu thay vì giữa tầng (giữa tầng thì phải đi tới một đầu rồi quay lại qua chính ô đó: nhánh cụt). Trả (đường đi bắt đầu ở (0, 0), các ô bỏ sót vì nằm ở tầng < 0)."""
    levels: dict[int, list[int]] = {}
    for c in cells:
        m = sign * c[major]
        if m >= 0:
            levels.setdefault(m, []).append(c[1 - major])
    dropped = [c for c in cells if sign * c[major] < 0]
    if not levels:
        return [(0, 0)], dropped

    def cell(m, n):
        return (sign * m, n) if major == 0 else (n, sign * m)

    path, m, n = [(0, 0)], 0, 0
    for level in range(max(levels) + 1):
        rng = levels.get(level)
        lo, hi = (min(rng), max(rng)) if rng else (n, n)
        if level > 0:
            entry = lo if abs(n - lo) <= abs(n - hi) else hi          # đầu gần nhất của tầng mới
            while n != entry:                                          # đi ngang nốt ở tầng cũ
                n += 1 if entry > n else -1
                path.append(cell(m, n))
            m = level
            path.append(cell(m, n))
        for target in ((lo, hi) if abs(n - lo) <= abs(n - hi) else (hi, lo)):
            while n != target:
                n += 1 if target > n else -1
                path.append(cell(m, n))
    return path, dropped


def _merge_diagonals(path, start_deg: float, end_deg: float, radius: float, origin, anchor, lane, budget: float = 0.0):
    """Cú dọc cuối của một tầng + cú ngang sang tầng kế gộp thành một cú chéo (STEP, STEP): bỏ ô ở góc (nơi lẽ ra dừng giữa hai cú), thường là ô
    sát mép quạt. Gộp được khi phần quạt mà ô đó phủ mà các ô còn lại và `lane` không thấy có diện tích (km2) còn trong `budget` (tổng cộng mọi
    chỗ gộp); budget = 0 thì chỉ gộp khi không mất chút nào."""
    ax, ay = anchor
    kept = set(path)
    point_area = VIEW[0] * VIEW[1] / len(_SAMPLES15) / (2 * PX_X * PX_Y)      # km2 một điểm lấy mẫu đại diện

    def lost_area(cell):
        i, j = cell
        others = list(lane) + [(ax + a * STEP, ay + b * STEP) for a in (i - 1, i, i + 1) for b in (j - 1, j, j + 1)
                               if (a, b) != cell and (a, b) in kept]
        lost = 0
        for fx, fy in _SAMPLES15:
            x, y = ax + i * STEP + fx * VIEW[0], ay + j * STEP + fy * VIEW[1]
            u, v = px_to_world(x, y)
            if in_sector(u, v, start_deg, end_deg, radius) and _on_map(origin, u, v) and not _seen(others, x, y):
                lost += 1
        return lost * point_area

    out, k = [path[0]], 1
    while k < len(path):
        if k + 1 < len(path):
            a, b, c = out[-1], path[k], path[k + 1]
            if a[0] == b[0] and b[1] != a[1] and c[1] == b[1] and c[0] != b[0] and path.count(b) == 1:
                lost = lost_area(b)
                if lost <= min(budget, MERGE_LOSS_MAX) + 1e-9:
                    budget -= lost
                    kept.discard(b)
                    out.append(c)                            # a -> c một cú chéo
                    k += 2
                    continue
        out.append(path[k])
        k += 1
    return out


def _covered(centers, start_deg: float, end_deg: float, radius: float, origin=None, rmax=None, edge_margin: float = 0.0, rmin: float = 0.0) -> float:
    """Tỉ lệ điểm mẫu của quạt (chỉ tới khoảng cách `rmax` nếu có) nằm trong tầm nhìn khi camera đứng ở các tâm `centers` (px so với gốc).
    Mẫu rải đều theo góc và theo KHOẢNG CÁCH (không theo diện tích) để vùng gần gốc, nơi quạt hẹp, cũng được kiểm tra dày như vùng xa."""
    rng = np.random.default_rng(0)
    span = _span(start_deg, end_deg)
    n = COVER_SAMPLES * 2
    reach = min(radius, rmax if rmax is not None else radius)
    ang = np.radians(start_deg + span * rng.uniform(0, 1, n))
    r = rmin + (reach - rmin) * rng.uniform(0, 1, n)
    pts = np.stack([r * np.cos(ang), r * np.sin(ang)], axis=1)
    if edge_margin > 0 and span < 360:                       # bỏ phần sát hai mép bên: không bắt buộc phải thấy
        off = np.radians(np.minimum(ang_off := np.degrees(ang) - start_deg, span - ang_off).clip(0, 90))
        keep = r * np.sin(off) >= edge_margin
        pts, r = pts[keep], r[keep]
    if origin is not None:                                   # vùng ngoài bản đồ không có gì để thấy
        pts = pts[(pts[:, 0] + origin[0] >= 0) & (pts[:, 0] + origin[0] < MAP_SIZE) & (pts[:, 1] + origin[1] >= 0) & (pts[:, 1] + origin[1] < MAP_SIZE)]
    if not len(pts):
        return 1.0
    seen = np.zeros(len(pts), bool)
    for cx, cy in set((round(x, 1), round(y, 1)) for x, y in centers):
        dx = PX_X * (pts[:, 0] - pts[:, 1]) - cx
        dy = PX_Y * (pts[:, 0] + pts[:, 1]) - cy
        seen |= (np.abs(dx) <= VIEW[0] / 2) & (np.abs(dy) <= VIEW[1] / 2)
    return float(seen.mean())


def _outside(centers, start_deg: float, end_deg: float) -> float:
    """Tổng khoảng cách (km) từ các tâm camera tới quạt, tính cho tâm nằm ngoài mép: càng nhỏ càng ít kéo ra tận mép / ra ngoài cung."""
    span = _span(start_deg, end_deg)
    if span >= 360:
        return 0.0
    mid = start_deg + span / 2
    total = 0.0
    for x, y in centers:
        u, v = px_to_world(x, y)
        r = math.hypot(u, v)
        if r < 1e-9:
            continue
        diff = abs((math.degrees(math.atan2(v, u)) - mid + 180) % 360 - 180) - span / 2
        if diff > 0:
            total += r * math.sin(math.radians(min(diff, 90)))
    return total


def _rings(cells, anchor, band: float):
    """Đường đi qua các ô lưới theo VÀNH khoảng cách tới gốc: xong hết các ô cách gốc [0, band) km mới sang [band, 2 band) ... (gần trước xa sau). Trong
    một vành đi theo góc, vành kế đi ngược lại; giữa hai ô liên tiếp đi từng bước sang ô kề (chéo khi cả hai trục đều lệch). Bắt đầu ở (0, 0)."""
    ax, ay = anchor
    bands: dict[int, list] = {}
    for c in cells:
        u, v = px_to_world(ax + c[0] * STEP, ay + c[1] * STEP)
        bands.setdefault(int(math.hypot(u, v) // band), []).append((math.atan2(v, u), c))
    path, cur = [(0, 0)], (0, 0)
    for n, k in enumerate(sorted(bands)):
        group = [c for _, c in sorted(bands[k])]
        if n % 2 or (group and max(abs(group[0][0] - cur[0]), abs(group[0][1] - cur[1])) >
                     max(abs(group[-1][0] - cur[0]), abs(group[-1][1] - cur[1]))):
            group.reverse()
        for target in group:
            while cur != target:
                cur = (cur[0] + (target[0] > cur[0]) - (target[0] < cur[0]), cur[1] + (target[1] > cur[1]) - (target[1] < cur[1]))
                path.append(cur)
    return path


def _fwd_frame(start_deg: float, end_deg: float, step: float):
    """Khung xoay theo phân giác của quạt (góc toạ độ game): (F, L) = cú TIẾN ra xa dọc phân giác và cú NGANG vuông góc với nó, tính bằng px ngón tay
    (camera dời), cùng độ dài `step`."""
    mid = math.radians(start_deg + _span(start_deg, end_deg) / 2)
    fx, fy = world_to_px(math.cos(mid), math.sin(mid))
    lx, ly = world_to_px(-math.sin(mid), math.cos(mid))
    fn, ln = math.hypot(fx, fy), math.hypot(lx, ly)
    return (fx / fn * step, fy / fn * step), (lx / ln * step, ly / ln * step)


def _unique_area(cell, rest, F, L, start_deg: float, end_deg: float, radius: float, origin, margin: float, rmin: float) -> float:
    """Diện tích (km2) phần quạt (bán kính `radius`, ngoài `rmin`, trừ mép `margin`, trong bản đồ) mà màn hình ở `cell` thấy mà các ô khác trong `rest` không thấy."""
    span = _span(start_deg, end_deg)
    point_area = VIEW[0] * VIEW[1] / len(_SAMPLES15) / (2 * PX_X * PX_Y)
    px = lambda c: (c[0] * F[0] + c[1] * L[0], c[0] * F[1] + c[1] * L[1])
    others = [px((cell[0] + di, cell[1] + dj)) for di in range(-2, 3) for dj in range(-2, 3) if (cell[0] + di, cell[1] + dj) in rest]
    cx, cy = px(cell)
    lost = 0
    for fx, fy in _SAMPLES15:
        x, y = cx + fx * VIEW[0], cy + fy * VIEW[1]
        u, v = px_to_world(x, y)
        if in_sector(u, v, start_deg, end_deg, radius) and math.hypot(u, v) >= rmin and _on_map(origin, u, v) \
                and (span >= 360 or margin <= 0 or _edge_dist(u, v, start_deg, span) >= margin) and not _seen(others, x, y):
            lost += 1
    return lost * point_area


def _drop_stubs(path, F, L, start_deg: float, end_deg: float, radius: float, origin, margin: float, rmin: float = 0.0):
    """Bỏ các NHÁNH CỤT thừa: đoạn đi vào một ô rồi quay ra ngay (A, B, A) mà phần quạt chỉ màn hình ở B thấy nhỏ hơn TAIL_MIN_FRAC màn hình: bỏ B và lần về A
    (đường đi không còn đè lên chính nó)."""
    limit = TAIL_MIN_FRAC * VIEW[0] * VIEW[1] / (2 * PX_X * PX_Y)
    path = list(path)
    changed = True
    while changed:
        changed = False
        for k in range(1, len(path) - 1):
            if path[k - 1] == path[k + 1] and path[k] != path[k - 1]:
                rest = set(path[:k]) | set(path[k + 1:])
                if _unique_area(path[k], rest, F, L, start_deg, end_deg, radius, origin, margin, rmin) < limit:
                    del path[k:k + 2]
                    changed = True
                    break
    return path


def _trim_tail(path, F, L, start_deg: float, end_deg: float, radius: float, origin, margin: float, rmin: float = 0.0):
    """Bỏ các cú kéo CUỐI CÙNG chỉ phủ thêm một vùng quạt rất nhỏ: lặp lại, bỏ ô cuối khi phần quạt (bán kính `radius`, trừ mép `margin`, trong bản đồ)
    mà màn hình ở ô đó thấy mà các ô còn lại của đường đi không thấy có diện tích < TAIL_MIN_FRAC * diện tích một màn hình."""
    path = list(path)
    limit = TAIL_MIN_FRAC * VIEW[0] * VIEW[1] / (2 * PX_X * PX_Y)
    while len(path) > 1:
        last = path[-1]
        rest = set(path[:-1])
        if last in rest:
            path.pop()                                         # đi lại ô đã qua: bỏ không mất gì
            continue
        if _unique_area(last, rest, F, L, start_deg, end_deg, radius, origin, margin, rmin) >= limit:
            break
        path.pop()
    return path


def _fwd_cells(start_deg: float, end_deg: float, radius: float, origin, F, L, margin: float) -> dict[tuple[int, int], float]:
    """{ô (i, j): r_cần} của khung xoay (tâm ô i * F + j * L px): các ô có màn hình (lấy mẫu 5x5) chạm vào quạt trong bán kính `radius`, cách hai mép bên >= `margin` km
    và trong bản đồ (nếu biết gốc). r_cần = khoảng cách gần gốc nhất của phần quạt mà màn hình ô đó thấy: ô chỉ cần cho các chặng bán kính >= r_cần.
    Vector hoá bằng numpy để chạy nhanh cả khi bán kính tới hàng trăm km."""
    span = _span(start_deg, end_deg)
    fkm, lkm = math.hypot(*px_to_world(*F)), math.hypot(*px_to_world(*L))
    imax, jmax = int((radius + 40) / fkm) + 2, int((radius + 40) / lkm) + 2
    I, J = np.meshgrid(np.arange(0, imax + 1), np.arange(-jmax, jmax + 1), indexing="ij")
    cx, cy = I * F[0] + J * L[0], I * F[1] + J * L[1]
    sx = np.array([f[0] for f in _SAMPLES5]) * VIEW[0]
    sy = np.array([f[1] for f in _SAMPLES5]) * VIEW[1]
    x, y = cx[..., None] + sx, cy[..., None] + sy
    u, v = (x / PX_X + y / PX_Y) / 2, (y / PX_Y - x / PX_X) / 2
    r = np.hypot(u, v)
    ang = (np.degrees(np.arctan2(v, u)) - start_deg) % 360
    ok = (r <= radius) & ((ang <= span + 1e-9) | (span >= 360))
    if span < 360 and margin > 0:
        off = np.minimum(ang, span - ang).clip(0, 90)
        ok &= r * np.sin(np.radians(off)) >= margin
    if origin is not None:
        ok &= (u + origin[0] >= 0) & (u + origin[0] < MAP_SIZE) & (v + origin[1] >= 0) & (v + origin[1] < MAP_SIZE)
    cu, cv = (cx / PX_X + cy / PX_Y) / 2, (cy / PX_Y - cx / PX_X) / 2
    keep = ok.any(axis=-1) & (np.hypot(cu, cv) <= radius + 40)
    if origin is not None:
        keep &= (cu + origin[0] >= 0) & (cu + origin[0] < MAP_SIZE) & (cv + origin[1] >= 0) & (cv + origin[1] < MAP_SIZE)
    need = np.where(ok, r, np.inf).min(axis=-1)
    ii, jj = np.nonzero(keep)
    return {(int(i), int(j) - jmax): float(need[i, j]) for i, j in zip(ii, jj)}


def _stage_groups(need: dict, lo: float = 0.0) -> dict[int, set]:
    """Chia các ô theo CHẶNG bán kính: chặng 0 = ô cần cho vùng trong STAGE_FIRST km, chặng k = ô cần cho vùng trong STAGE_FIRST + k * STAGE_STEP km
    mà chặng trước chưa cần. Chỉ lấy ô có r_cần > lo (lo > 0: bỏ phần đã quét ở dải trước)."""
    groups: dict[int, set] = {}
    for c, r in need.items():
        if r > lo:
            groups.setdefault(0 if r <= STAGE_FIRST else math.ceil((r - STAGE_FIRST) / STAGE_STEP - 1e-9), set()).add(c)
    return groups


def _zigzag_groups(groups: dict, F, L):
    """Đường đi RÍC RẮC qua các nhóm ô (chặng) theo thứ tự nhóm tăng dần, ít nhánh cụt / ít quay lại màn đã qua: xong hết nhóm gần mới sang nhóm xa. Trong một nhóm
    mỗi bước sang một ô KỀ CHƯA ĐI (ưu tiên ô có ít ô kề chưa đi hơn để không bỏ sót ô lẻ, rồi giữ hướng đi dọc vòng cung, nhóm kế đi ngược lại); chỉ khi không còn ô
    kề chưa đi mới đi vòng qua các ô khác theo đường ngắn nhất tới ô chưa đi gần nhất. Chỉ bước theo trục i hoặc j (cú tiến / ngang của khung xoay). Bắt đầu ở (0, 0)."""
    angle: dict = {}

    def ang_of(c):                                          # góc (toạ độ game) của tâm ô c, nhớ lại
        if c not in angle:
            u, v = px_to_world(c[0] * F[0] + c[1] * L[0], c[0] * F[1] + c[1] * L[1])
            angle[c] = math.atan2(v, u)
        return angle[c]

    visited = {(0, 0)}
    path, cur = [(0, 0)], (0, 0)
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    nbrs = lambda c: [(c[0] + d[0], c[1] + d[1]) for d in steps]
    for n, k in enumerate(sorted(groups)):
        todo = groups[k] - visited
        sign = 1 if n % 2 == 0 else -1                      # nhóm chẵn đi theo chiều góc tăng, nhóm lẻ ngược lại
        while todo:
            cand = [c for c in nbrs(cur) if c in todo]
            if cand:
                def key(c):
                    free = sum(1 for d in nbrs(c) if d in todo)
                    return (free, -sign * (ang_of(c) - ang_of(cur)))   # ít ô kề chưa đi trước; rồi theo chiều của nhóm
                cur = min(cand, key=key)
                path.append(cur)
                visited.add(cur)
                todo.discard(cur)
                continue
            # kẹt (hoặc mới bắt đầu nhóm xa gốc): đường rẻ nhất tới ô chưa đi gần nhất; đi qua ô đã đi tốn gấp REVISIT_COST lần nên ưu tiên đường mới (không đè lên đường cũ)
            prev, best, heap, found = {cur: None}, {cur: 0}, [(0, cur)], None
            while heap:
                cost, c = heapq.heappop(heap)
                if cost > best.get(c, 1e18):
                    continue
                if c in todo:
                    found = c
                    break
                for d in nbrs(c):
                    if abs(d[0]) >= 100000 or abs(d[1]) >= 100000:
                        continue
                    nc = cost + (REVISIT_COST if d in visited else 1)
                    if nc < best.get(d, 1e18):
                        best[d] = nc
                        prev[d] = c
                        heapq.heappush(heap, (nc, d))
            walk = []
            c = found
            while c != cur:
                walk.append(c)
                c = prev[c]
            for c in reversed(walk):
                cur = c
                path.append(cur)
                visited.add(cur)
                todo.discard(cur)
    return path


def _fwd_lattice(start_deg: float, end_deg: float, radius: float, origin=None, ui_check: bool = False, zigzag: bool = False, rmin: float = 0.0):
    """(step, đường đi theo ô (i, j)) không bao giờ kéo ngược về gốc: khung xoay theo phân giác (xem _fwd_frame), ô (i, j) có tâm i * F + j * L; mỗi cú
    hoặc TIẾN (i + 1) hoặc đi NGANG (j +- 1), không có thành phần hướng về gốc. Phần sát hai mép bên (EDGE_MARGIN km) không bắt buộc phải thấy.
    Thử độ dài cú kéo FWD_STEPS từ lớn xuống nhỏ, lấy độ dài lớn nhất phủ đủ (ít cú nhất).
    zigzag=True: quét GẦN -> XA theo chặng bán kính STAGE_FIRST, STAGE_FIRST + STAGE_STEP, ... (_stage_groups): xong chặng nào thì toàn bộ cung trong bán kính
    chặng đó đã được thấy, rồi mới sang chặng xa hơn; trong chặng đi ríc rắc (_zigzag_groups). False: quét theo tầng thẳng (_snake), ít cú hơn.
    rmin > 0: chỉ quét phần quạt ngoài bán kính rmin (dải xa; đường đi vẫn bắt đầu từ gốc nên gồm cả đoạn tiến tới dải).
    ui_check=True: bỏ độ dài cú kéo nào mà có loại cú (tiến / ngang sang hai bên) không tìm được chỗ bắt đầu né nút giao diện (safe_shift); kết quả có thêm
    {loại cú: dời}. None nếu quạt quá rộng."""
    span = _span(start_deg, end_deg)
    if span > FWD_SPAN_MAX:
        return None
    for step in FWD_STEPS:
        F, L = _fwd_frame(start_deg, end_deg, step)
        shifts = None
        if ui_check:
            shifts = {m: safe_shift(round(-v[0]), round(-v[1])) for m, v in (("F", F), ("L", L), ("l", (-L[0], -L[1])))}
            if any(sh is None for sh in shifts.values()):
                continue
        need = _fwd_cells(start_deg, end_deg, radius, origin, F, L, EDGE_MARGIN)
        need = {c: r for c, r in need.items() if r > rmin}
        if not need:
            continue
        path = _zigzag_groups(_stage_groups(need), F, L) if zigzag else _snake(set(need), 0, 1)[0]
        path = _trim_tail(_drop_stubs(path, F, L, start_deg, end_deg, radius, origin, EDGE_MARGIN), F, L, start_deg, end_deg, radius, origin, EDGE_MARGIN)
        px_path = [(i * F[0] + j * L[0], i * F[1] + j * L[1]) for i, j in path]
        if rmin <= 0 and _covered(px_path, start_deg, end_deg, radius, origin, None, EDGE_MARGIN) < COVER_MIN:
            continue                                       # (dải xa rmin > 0 không tự phủ đủ: một phần do các ô của dải trước đảm nhiệm)
        return (step, path, shifts) if ui_check else (step, path)
    return None


def _fwd_path(start_deg: float, end_deg: float, radius: float, origin=None, zigzag: bool = False):
    """(đường đi px, 0) của _fwd_lattice, hoặc None."""
    found = _fwd_lattice(start_deg, end_deg, radius, origin, False, zigzag)
    if found is None:
        return None
    step, path = found[:2]
    F, L = _fwd_frame(start_deg, end_deg, step)
    return [(i * F[0] + j * L[0], i * F[1] + j * L[1]) for i, j in path], 0


def _edge_dist(u: float, v: float, start_deg: float, span: float) -> float:
    """Khoảng cách (km) từ điểm (u, v) tới tia mép bên gần nhất của quạt (điểm trong quạt)."""
    r = math.hypot(u, v)
    a = (math.degrees(math.atan2(v, u)) - start_deg) % 360
    return r * math.sin(math.radians(min(max(min(a, span - a), 0), 90)))


def _best_path(start_deg: float, end_deg: float, radius: float, origin=None, near_first: bool = True, no_back: bool = False, zigzag: bool = False):
    """(đường đi, m) ít cú nhất phủ kín quạt (góc toạ độ game), hoặc None. Đường đi = các điểm dừng (px so với gốc), m + 1 điểm đầu nằm
    trên đường thẳng theo phân giác (vùng gần gốc, cung còn hẹp hơn màn hình), phần sau là lưới ô quét kiểu cắt cỏ bắt đầu từ điểm thứ m + 1.
    Thử vài độ dài m của đường thẳng, cùng 4 cách quét lưới (tầng theo cột / hàng, chiều + / -), loại cách bỏ sót vùng quạt."""
    span = _span(start_deg, end_deg)
    if no_back:
        found = _fwd_path(start_deg, end_deg, radius, origin, zigzag)
        if found is not None:
            return found
    tilts = [0.0] + [t for k in (2, 4, 6) for t in (k, -k) if k <= span / 2]
    best = None
    for tilt in (tilts if span <= LANE_SPAN_MAX else [0.0]):
        lane_full = _lane(start_deg, end_deg, LANE_MAX, tilt)
        m_max = 0
        if span <= LANE_SPAN_MAX:
            for m in range(1, LANE_MAX + 1):
                reach = math.hypot(*px_to_world(*lane_full[m]))
                if reach > radius or _covered(lane_full[:m + 1], start_deg, end_deg, radius, origin, reach) < COVER_MIN:
                    break
                m_max = m
        for m in sorted({m_max, max(0, m_max - 1), 0}):
            lane = lane_full[:m + 1]
            anchor = lane[-1]
            cells = _prune(_needed_cells(start_deg, end_deg, radius, origin, anchor, lane), start_deg, end_deg, radius, origin, anchor, lane)
            for major, sign in ([(0, 1)] if near_first else [(0, 1), (0, -1), (1, 1), (1, -1)]):
                if True:
                    path = _rings(cells, anchor, RING_BAND) if near_first else _snake(cells, major, sign)[0]
                    px_path = lane[:-1] + [(anchor[0] + i * STEP, anchor[1] + j * STEP) for i, j in path]
                    if _covered(px_path, start_deg, end_deg, radius, origin) < COVER_MIN:
                        continue
                    area = 0.5 * radius * radius * math.radians(span)                  # diện tích quạt (km2)
                    for budget in (DIAG_LOSS * area, 0.0):                              # gộp chéo có hao hụt nhỏ; nếu phủ tụt dưới mức thì gộp không hao hụt
                        merged = _merge_diagonals(path, start_deg, end_deg, radius, origin, anchor, lane, budget)
                        px_path = lane[:-1] + [(anchor[0] + i * STEP, anchor[1] + j * STEP) for i, j in merged]
                        if _covered(px_path, start_deg, end_deg, radius, origin) >= COVER_MIN:
                            break
                    score = (len(px_path), _outside(px_path, start_deg, end_deg))
                    if best is None or score < best[2]:
                        best = (px_path, m, score)
    return best[:2] if best else None


def sweep_path(start_deg: float, end_deg: float, radius: float = RADIUS, origin=None, near_first: bool = True) -> list[tuple[float, float]]:
    """Các điểm dừng (px so với gốc, bắt đầu (0, 0)) để thấy hết quạt (góc toạ độ game), ít cú nhất; mỗi bước giữa hai điểm là một cú kéo STEP px
    (hoặc cú chéo (STEP, STEP)). Một đường đi không phủ nổi (quạt vắt qua cả hai trục) thì chỉ có điểm gốc."""
    best = _best_path(start_deg, end_deg, radius, origin, near_first)
    return best[0] if best else [(0.0, 0.0)]


def _plan(start_deg: float, end_deg: float, radius: float, origin=None, near_first: bool = True, no_back: bool = False, zigzag: bool = False) -> list:
    """Các (đường đi, m) phủ quạt theo GÓC MÀN HÌNH start_deg .. end_deg (end > start). Thử nguyên quạt trước; không được thì chia tại góc 0 / 90 /
    180 / 270 của màn hình gần giữa quạt nhất (không có thì chia đôi), rồi lập đường đi cho từng nửa."""
    best = _best_path(*screen_to_world_deg(start_deg, end_deg), radius, origin, near_first, no_back, zigzag)
    if best is not None:
        return [best]
    if end_deg - start_deg < 1:
        return [([(0.0, 0.0)], 0)]                           # quạt quá hẹp mà vẫn không phủ nổi: thôi
    cuts = [c * 90 for c in range(math.floor(start_deg / 90) + 1, math.ceil(end_deg / 90)) if start_deg < c * 90 < end_deg]
    mid = (start_deg + end_deg) / 2
    cut = min(cuts, key=lambda c: abs(c - mid)) if cuts else mid
    return _plan(start_deg, cut, radius, origin, near_first, no_back, zigzag) + _plan(cut, end_deg, radius, origin, near_first, no_back, zigzag)


def safe_shift(fx: int, fy: int, margin: int = 6):
    """Dời (sx, sy) nhỏ nhất của cú kéo ngón tay (fx, fy) (đối xứng quanh SWIPE_CENTER) sao cho điểm đầu và cuối nằm trong vùng kéo an toàn và điểm đầu
    không trúng nút giao diện (UI_BLOCKS, nới `margin` px); None nếu không có."""
    cx, cy = SWIPE_CENTER
    best = None
    for sx in range(-200, 201, 5):
        for sy in range(-200, 201, 5):
            x1, y1, x2, y2 = cx - fx // 2 + sx, cy - fy // 2 + sy, cx + fx // 2 + sx, cy + fy // 2 + sy
            if not all(SWIPE_AREA[0] <= x <= SWIPE_AREA[2] and SWIPE_AREA[1] <= y <= SWIPE_AREA[3] for x, y in ((x1, y1), (x2, y2))):
                continue
            if any(bx1 - margin <= x1 <= bx2 + margin and by1 - margin <= y1 <= by2 + margin for bx1, by1, bx2, by2 in UI_BLOCKS):
                continue
            if best is None or math.hypot(sx, sy) < math.hypot(*best):
                best = (sx, sy)
    return best


def _swipe(bot, fx: int, fy: int, before=None, shift=None):
    """Một cú kéo ngón tay (fx, fy) đối xứng quanh SWIPE_CENTER. Màn không đổi (điểm đầu trúng icon nên game coi là bấm) thì dời cả cú
    kéo (RETRY_SHIFTS, vẫn cùng độ dài) rồi thử lại. `before` = ảnh trước cú kéo (không có thì chụp); `shift` = dời thử đầu tiên (mẫu cố định đã chọn chỗ né nút giao diện). Trả (màn đã đổi hay chưa, ảnh sau cú
    kéo) — ảnh này dùng luôn để đọc toạ độ camera, đỡ chụp thêm."""
    cx, cy = SWIPE_CENTER
    if before is None:
        before = bot.screenshot()
    after = before
    checkable = hasattr(before, "shape")
    for dx, dy in ([shift] if shift else []) + [r for r in RETRY_SHIFTS if r != shift]:
        x1, y1, x2, y2 = cx - fx // 2 + dx, cy - fy // 2 + dy, cx + fx // 2 + dx, cy + fy // 2 + dy
        if not all(SWIPE_AREA[0] <= x <= SWIPE_AREA[2] and SWIPE_AREA[1] <= y <= SWIPE_AREA[3] for x, y in ((x1, y1), (x2, y2))):
            continue
        bot.swipe(x1, y1, x2, y2, duration=SWIPE_TIME, delay=SWIPE_WAIT)
        after = bot.screenshot()
        if not checkable or _moved(before, after):
            return True, after
    return False, after


def go_home(bot) -> bool:
    """Bấm nút hình toà thành cho camera về thành của mình (toạ độ gốc "vị trí của tôi"). False nếu không thấy nút."""
    pos = bot.find(HOME_ICON, threshold=0.8)
    if pos is None:
        bot.log("arc: không thấy nút về thành")
        return False
    bot.tap(*pos, delay=HOME_WAIT)
    return True


def valid_camera(coords):
    """`coords` (X, Y) đọc từ thanh toạ độ nếu nằm trong bản đồ (0 .. MAP_SIZE - 1), không thì None: OCR đôi khi nhầm một chữ số (VD 0487 đọc thành 6487), toạ độ ngoài bản đồ chắc chắn sai."""
    if coords is None or not (0 <= coords[0] < MAP_SIZE and 0 <= coords[1] < MAP_SIZE):
        return None
    return coords


def _camera(bot, screen=None):
    """(X, Y) camera đọc từ thanh toạ độ trên `screen` (không có thì chụp), hoặc None (đọc không ra / ảnh không phải màn thật như trong test)."""
    if screen is None:
        screen = bot.screenshot()
    if not hasattr(screen, "shape"):
        return None
    return valid_camera(read_camera(screen))


def _walk(bot, path, origin, seen, on_step, resync, screen=None, shifts=None):
    """Đi hết `path` (các điểm dừng px so với gốc, điểm đầu là chỗ đang đứng): mỗi bước một cú kéo, ghi log độ lệch, gọi resync khi lệch nhiều và
    on_step ở ô mới ghé. Trả (số cú đã kéo, có bị on_step dừng không, ảnh màn hình cuối)."""
    swipes = 0
    for k, (x, y) in enumerate(path):
        if k:
            px0, py0 = path[k - 1]
            moved, screen = _swipe(bot, round(-(x - px0)), round(-(y - py0)), screen, shifts[k - 1] if shifts else None)
            if not moved:
                bot.log(f"arc: cú kéo tới điểm ({x:.0f}, {y:.0f}) px không làm màn đổi")
            swipes += 1
        target = px_to_world(x, y)
        if origin:
            now = _camera(bot, screen)
            if now is not None:
                bot.log(f"arc: X:{now[0]:04d} Y:{now[1]:04d} (ô dự tính {origin[0] + target[0]:.0f}, {origin[1] + target[1]:.0f}; "
                        f"lệch {now[0] - origin[0] - target[0]:+.0f}, {now[1] - origin[1] - target[1]:+.0f})")
                drift = math.hypot(now[0] - origin[0] - target[0], now[1] - origin[1] - target[1])
                if resync is not None and drift > RESYNC_DRIFT:
                    bot.log(f"arc: lệch {drift:.0f} km, đưa camera về ô dự tính")
                    resync(bot, round(origin[0] + target[0]), round(origin[1] + target[1]))
                    screen = None
        key = (round(x), round(y))
        if key in seen:
            continue                                         # đã ghé (đi ngang qua)
        seen.add(key)
        if on_step is not None and on_step(*target):
            return swipes, True, screen
    return swipes, False, screen


def _way_back(path, m: int):
    """Từ điểm cuối của `path` về gốc: quay về điểm thứ m (hết phần lưới) bằng các bước ngang rồi dọc mỗi bước STEP px, rồi đi ngược đường thẳng
    đầu về gốc."""
    ax, ay = path[m]
    x, y = path[-1]
    i, j = round((x - ax) / STEP), round((y - ay) / STEP)
    back = [(x, y)]
    while i:
        i += -1 if i > 0 else 1
        back.append((ax + i * STEP, ay + j * STEP))
    while j:
        j += -1 if j > 0 else 1
        back.append((ax + i * STEP, ay + j * STEP))
    return back + path[:m][::-1]


def _step_len(ux: float, uy: float) -> float:
    """Độ dài tối đa (px) của một cú kéo theo hướng đơn vị (ux, uy): STEP_FRAC của cú kéo dài nhất vừa vùng ngón tay (ngang SWIPE_FULL, dọc SWIPE_FULL_V)."""
    return STEP_FRAC * min(SWIPE_FULL / max(abs(ux), 1e-9), SWIPE_FULL_V / max(abs(uy), 1e-9))


_SHIFT_CACHE: dict = {}


def _box(dx: float, dy: float) -> bool:
    """Cú kéo ngón tay (dx, dy) có vừa giới hạn STEP_FRAC của cú kéo dài nhất (ngang SWIPE_FULL, dọc SWIPE_FULL_V) không."""
    return abs(dx) <= STEP_FRAC * SWIPE_FULL + 1e-6 and abs(dy) <= STEP_FRAC * SWIPE_FULL_V + 1e-6


def _can_swipe(dx: float, dy: float) -> bool:
    """Cú kéo camera dịch (dx, dy) px vừa giới hạn và có chỗ bắt đầu né nút giao diện (safe_shift, nhớ lại theo vector làm tròn 4 px)."""
    if not _box(dx, dy):
        return False
    key = (-round(dx), -round(dy))                  # đúng vector ngón tay sẽ kéo (làm tròn 1 px như lúc kéo thật), không làm tròn thô hơn: cú sát giới hạn dễ lệch khỏi chỗ an toàn
    if key not in _SHIFT_CACHE:
        _SHIFT_CACHE[key] = safe_shift(*key)
    return _SHIFT_CACHE[key] is not None


def _ring_points(rho: float, ws: float, we: float, inset: float):
    """Các điểm dừng (px so với gốc) dọc vòng tròn bán kính `rho` km, từ góc ws tới we (góc toạ độ game) lùi vào `inset` km ở hai mép bên. Mỗi dây cung xa nhất có thể
    (vừa giới hạn cú kéo ngang / dọc và né được nút giao diện: _can_swipe), nên cú dọc dài hơn cú ngang; cú quá ngắn (< MIN_SWIPE) được gộp với cú kề. Cung quá hẹp ở
    bán kính này thì chỉ một điểm ở phân giác."""
    span = _span(ws, we)
    full = span >= 360
    da = 0.0 if full or rho <= 0 else math.degrees(math.asin(min(1.0, inset / rho)))
    if not full and 2 * da >= span:
        mid = math.radians(ws + span / 2)
        return [world_to_px(rho * math.cos(mid), rho * math.sin(mid))]
    a0, a1 = ws + da, (ws + 360 if full else ws + span - da)
    n = max(64, int(math.radians(a1 - a0) * rho / 0.1) + 2)         # lấy mẫu mịn ~0,1 km
    ang = np.radians(np.linspace(a0, a1, n))
    u, v = rho * np.cos(ang), rho * np.sin(ang)
    pts = np.stack([PX_X * (u - v), PX_Y * (u + v)], axis=1)
    mh, mv = STEP_FRAC * SWIPE_FULL, STEP_FRAC * SWIPE_FULL_V
    out, i = [0], 0
    while i < n - 1:
        dxs, dys = np.abs(pts[i + 1:, 0] - pts[i, 0]), np.abs(pts[i + 1:, 1] - pts[i, 1])
        bad = np.nonzero((dxs > mh) | (dys > mv))[0]
        j = i + 1 + (int(bad[0]) - 1 if len(bad) else len(dxs) - 1)  # điểm xa nhất vẫn vừa khung
        j = max(j, i + 1)
        while j > i + 1 and not _can_swipe(pts[j, 0] - pts[i, 0], pts[j, 1] - pts[i, 1]):
            j -= 1                                                    # lùi tới điểm mà cú kéo có chỗ né nút
        out.append(j)
        i = j
    # gộp cú quá ngắn với cú kề nếu cú gộp vẫn hợp lệ
    changed = True
    while changed and len(out) > 2:
        changed = False
        for k in range(1, len(out)):
            seg = float(np.hypot(*(pts[out[k]] - pts[out[k - 1]])))
            if seg < MIN_SWIPE:
                lo, hi = (k - 1, k + 1) if k + 1 < len(out) else (k - 2, k)
                if lo >= 0 and hi < len(out) and _can_swipe(*(pts[out[hi]] - pts[out[lo]])):
                    del out[k if hi == k + 1 else k - 1]
                    changed = True
                    break
    return [(float(pts[j, 0]), float(pts[j, 1])) for j in out]


def circular_path(start_deg: float, end_deg: float, radius: float, origin=None, inset: float = CIRC_INSET):
    """Đường đi theo VÒNG TRÒN cho quạt (góc toạ độ game): camera đi dọc vòng tròn bán kính delta, 2 delta, ... quanh gốc (mỗi cú là một dây cung bám theo vòng, dài
    tối đa theo hướng của nó), hết cung thì kéo ra ngoài sang vòng tròn kế, vòng kế đi ngược lại. Gần -> xa tự nhiên; cung rộng đi liền, không cần chia phần hay về gốc.
    delta lớn nhất mà cú kéo ra ngoài vẫn vừa (tính theo hướng bán kính khắp cung), rồi giảm dần cho tới khi cung phủ đủ. Trả (đường đi px, delta) hoặc None."""
    span = _span(start_deg, end_deg)
    caps = []
    for k in range(13):                                             # delta tối đa = cú kéo ra ngoài dài nhất theo hướng bán kính, lấy hướng chặt nhất trong cung
        th = math.radians(start_deg + span * k / 12 if span < 360 else 30 * k)
        rx, ry = world_to_px(math.cos(th), math.sin(th))
        rn = math.hypot(rx, ry)
        caps.append(_step_len(rx / rn, ry / rn) / rn)
    cap = min(caps)
    for frac in (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5):
        delta = cap * frac
        path = [(0.0, 0.0)]
        for k in range(1, math.ceil(radius / delta) + 1):
            pts = _ring_points(min(k * delta, radius), start_deg, end_deg, inset)
            if k % 2 == 0:
                pts = pts[::-1]
            if origin is not None:                              # chỉ giữ điểm dừng trong bản đồ
                pts = [q for q in pts if _on_map(origin, *px_to_world(*q))]
                if not pts:
                    continue
            p0, p1 = path[-1], pts[0]
            d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            m = 1
            if d > 1e-9:
                m = max(1, math.ceil(max(abs(p1[0] - p0[0]) / (STEP_FRAC * SWIPE_FULL), abs(p1[1] - p0[1]) / (STEP_FRAC * SWIPE_FULL_V)) - 1e-9))   # kéo ra ngoài sang vòng mới (chia đều nếu dài hơn một cú)
                while m < 4 and not _can_swipe((p1[0] - p0[0]) / m, (p1[1] - p0[1]) / m):
                    m += 1                                       # cú dài quá nên điểm đầu rơi vào nút giao diện (không có chỗ bắt đầu an toàn): chia nhỏ thêm
            path.extend((p0[0] + (p1[0] - p0[0]) * i / m, p0[1] + (p1[1] - p0[1]) * i / m) for i in range(1, m + 1))
            path.extend(pts[1:])
        k = 1
        while k < len(path) - 1:                                        # gộp các cú quá ngắn (dễ bị coi là bấm) nếu cú gộp vẫn hợp lệ
            if math.hypot(path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1]) < MIN_SWIPE and _can_swipe(path[k + 1][0] - path[k - 1][0], path[k + 1][1] - path[k - 1][1]):
                del path[k]
            else:
                k += 1
        path = _split_unsafe(path)
        if _covered(path, start_deg, end_deg, radius, origin, None, inset) >= COVER_MIN:
            return path, round(delta, 2)
    return None


def _split_unsafe(path):
    """Cú nào của `path` không có chỗ bắt đầu an toàn (điểm đầu trúng nút giao diện: game coi là bấm, màn không đổi) thì chia đều thành 2-4 cú dọc theo đường thẳng cho tới khi kéo được (thêm vài
    cú, độ phủ không giảm)."""
    out = [path[0]]
    for p, q in zip(path, path[1:]):
        m = 1
        while m < 4 and not _can_swipe((q[0] - p[0]) / m, (q[1] - p[1]) / m):
            m += 1
        out.extend((p[0] + (q[0] - p[0]) * i / m, p[1] + (q[1] - p[1]) * i / m) for i in range(1, m + 1))
    return out


def _shifts_for(path):
    """Dời né nút giao diện (safe_shift) cho từng cú của đường đi: theo ĐÚNG vector ngón tay làm tròn 1 px như lúc kéo thật và như _can_swipe lúc lập đường đi (làm tròn thô hơn thì cú sát giới hạn
    bị tính khác, ra None dù đường đi đã tính là kéo được)."""
    out = []
    for p, q in zip(path, path[1:]):
        key = (round(-(q[0] - p[0])), round(-(q[1] - p[1])))
        if key not in _SHIFT_CACHE:
            _SHIFT_CACHE[key] = safe_shift(*key)
        out.append(_SHIFT_CACHE[key])
    return out


def _split_wide(start_deg: float, span: float, max_deg: float = FWD_SPAN_MAX):
    """Quạt rộng hơn FWD_SPAN_MAX chia thành các phần đều nhau, mỗi phần <= FWD_SPAN_MAX độ (bội của 15° nếu span là bội của 15°, để dùng mẫu cố định):
    [(góc bắt đầu, độ rộng), ...]."""
    n = math.ceil(span / max_deg - 1e-9)
    units = span / 15
    if abs(units - round(units)) < 1e-9:
        base, rem = divmod(int(round(units)), n)
        sizes = [(base + (1 if k < rem else 0)) * 15 for k in range(n)]
    else:
        sizes = [span / n] * n
    out, s0 = [], start_deg
    for size in sizes:
        out.append((s0, size))
        s0 += size
    return out


def plan_pieces(start_deg: float, span: float, radius: float, origin=None, near_first: bool = True, no_back: bool = True, zigzag: bool = True, band_km: float = BAND_KM, piece_deg: float = PIECE_DEG, circular: bool = False) -> list:
    """Các phần (đường đi px, m, dời né nút giao diện hoặc None, có phải đi ngược đường để về gốc) cần quét cho quạt theo GÓC MÀN HÌNH start_deg, rộng span.
    no_back và quạt rộng hơn FWD_SPAN_MAX: chia thành các phần <= FWD_SPAN_MAX độ (_split_wide), phần nào cũng không kéo ngược; về gốc giữa các phần
    bằng nút về thành hoặc đi ngược đường."""
    if circular and no_back:
        ws, we = screen_to_world_deg(start_deg, start_deg + span)
        found = circular_path(ws, we, radius, origin)
        if found is not None:
            return [(found[0], 0, _shifts_for(found[0]), False)]
    if no_back and span > piece_deg:
        parts = _split_wide(start_deg, span, min(piece_deg, FWD_SPAN_MAX))
        if band_km and radius > band_km:                         # theo dải bán kính: dải gần gốc của MỌI phần trước, rồi dải xa hơn
            edges = sorted({k * band_km for k in range(int(radius // band_km))} | {radius})
            pieces = []
            for r0, r1 in zip(edges, edges[1:]):
                for s0, size in parts:
                    ws, we = screen_to_world_deg(s0, s0 + size)
                    found = _fwd_lattice(ws, we, r1, origin, False, zigzag, r0)
                    if found is None or len(found[1]) < 2:
                        continue
                    step, cells = found
                    F, L = _fwd_frame(ws, we, step)
                    pieces.append(([(i * F[0] + j * L[0], i * F[1] + j * L[1]) for i, j in cells], 0, None, True))
            return pieces
        pieces = []
        for s0, size in parts:
            pieces.extend(plan_pieces(s0, size, radius, origin, near_first, no_back, zigzag, band_km, piece_deg, circular)[:1] or [])
        return [(path, m, shifts, True) for path, m, shifts, _ in pieces]
    try:
        planned = _plan(start_deg, start_deg + span, radius, origin, near_first, no_back, zigzag)
    except Exception:                                       # công thức lỗi: quạt này đứng yên
        planned = None
    if planned is None:
        return [([(0.0, 0.0)], 0, None, False)]
    return [(path, m, None, no_back and m == 0 and span <= FWD_SPAN_MAX) for path, m in planned]


def arc_sweep(bot, start_deg: float, end_deg: float, radius: float = RADIUS, on_step=None, home: bool = True, resync=None, near_first: bool = True, no_back: bool = True, zigzag: bool = True, band_km: float = BAND_KM, piece_deg: float = PIECE_DEG, circular: bool = True) -> int:
    """Kéo camera qua mọi ô cần thiết để thấy hết quạt từ start_deg ngược chiều kim đồng hồ TRÊN MÀN HÌNH tới end_deg (VD 345 -> 15, 0° = phải)
    bán kính `radius` km quanh chỗ đang đứng. Mọi cú kéo giống hệt nhau (xem đầu file). `on_step(u, v)` gọi lần đầu camera tới mỗi ô với
    (dX, dY) dự tính của ô đó so với gốc; trả True thì dừng sớm. Ô có tâm ngoài bản đồ không gọi on_step. Trả số cú kéo đã làm.
    Quạt mà một đường đi không phủ nổi (rộng hơn 180° hoặc vắt qua cả hai trục màn hình) được chia tại các góc 0/90/180/270 thành nhiều phần;
    xong mỗi phần camera về gốc rồi mới quét phần kế: home=True thì bấm nút về thành (gốc = thành), không thì kéo ngược (mỗi bước một cú STEP).
    no_back=True (quạt <= FWD_SPAN_MAX độ): không bao giờ kéo ngược về gốc, mỗi cú hoặc tiến ra xa theo phân giác hoặc đi ngang vuông góc với nó; hai mép bên (EDGE_MARGIN km) không bắt buộc phải thấy.
    circular=True (mặc định, với no_back): đi theo VÒNG TRÒN quanh gốc (circular_path): hết vòng bán kính delta thì kéo ra ngoài sang vòng kế; cung rộng cũng đi liền một mạch, không chia phần, không về gốc giữa chừng. False: các kiểu theo lưới bên dưới.
    piece_deg (mặc định PIECE_DEG): cung rộng hơn mức này chia thành các phần nhỏ đều nhau.
    band_km (cung rộng hơn piece_deg, mặc định BAND_KM): quét theo từng dải bán kính band_km: xong dải gần gốc của TẤT CẢ các phần (về thành giữa các phần) mới sang dải xa hơn; 0 thì quét xong từng phần mới sang phần khác.
    zigzag=True (với no_back): quét GẦN -> XA theo chặng bán kính STAGE_FIRST, +STAGE_STEP, ... (xong chặng nào thì cung trong bán kính đó đã thấy hết), ríc rắc trong chặng; False: quét theo tầng thẳng vuông góc với phân giác (ít cú hơn nhưng không theo chặng bán kính).
    near_first=True: quét hết khu gần gốc trước rồi mới mở rộng ra xa dần (theo vành RING_BAND km); False: quét kiểu cắt cỏ theo cột / hàng, ít cú hơn nhưng không theo thứ tự gần -> xa.
    resync(bot, x, y): hàm đưa camera về toạ độ (x, y) (VD nhập toạ độ trong game), gọi khi camera lệch ô dự tính hơn RESYNC_DRIFT; không có thì cứ đi tiếp.
    home=True: bấm nút hình toà thành cho camera về thành của mình trước khi quét (gốc = thành) và bấm lại khi quét xong / dừng sớm."""
    if home:
        go_home(bot)
    origin = _camera(bot)
    span = 360.0 if end_deg - start_deg >= 360 else (end_deg - start_deg) % 360
    pieces = plan_pieces(start_deg, span, radius, origin, near_first, no_back, zigzag, band_km, piece_deg, circular)
    if all(len(path) < 2 for path, _, _, _ in pieces):
        bot.log("arc: không lập được đường đi cho quạt này (công thức không ra và không có mẫu cố định)")
    swipes, seen, screen = 0, set(), None
    for n, (path, m, shifts, retrace) in enumerate(pieces):
        bot.log(f"arc: phần {n + 1}/{len(pieces)}: {len(path) - 1} cú kéo (đầu {m} cú thẳng theo phân giác), mỗi cú {STEP}px")
        done, stop, screen = _walk(bot, path, origin, seen, on_step, resync, screen, shifts)
        swipes += done
        if stop:
            break
        if n + 1 < len(pieces):                               # về gốc để quét phần kế
            if home and go_home(bot):                         # gốc = thành: bấm nút về thành nhanh hơn kéo ngược cả đường
                screen = None
                continue
            done, _, screen = _walk(bot, path[::-1] if retrace else _way_back(path, m), origin, seen, None, resync, screen)
            swipes += done
    if home:
        go_home(bot)
    return swipes
