"""
arc_sweep.py — kéo bản đồ thế giới để quét hết một hình quạt quanh chỗ camera đang đứng (dò boss; chưa có phần nhận boss,
chỉ lo kéo camera, nhận boss gắn qua `on_step`).

Gốc = chỗ camera đứng lúc gọi (tâm hình tròn). Góc theo toạ độ game: 0° = hướng X tăng, 90° = hướng Y tăng. Bán kính tính
bằng "km" của game = khoảng cách Euclid trong toạ độ X:Y (đo trên 21913: km = hypot(X - Xnhà, Y - Ynhà), lệch tối đa ~1,7
do làm tròn) nên 1 km = 1 đơn vị toạ độ.

Bản đồ thế giới nhìn xéo: cuộn sang phải thì X tăng, Y giảm; cuộn xuống thì X, Y cùng tăng. Đo ở zoom hiện tại:
    px_ngang = 60 * (dX - dY)      px_dọc = 30 * (dX + dY)        (px ngón tay)
Vùng quạt được chia thành các ô theo màn hình (CELL px); camera đi qua tâm từng ô từ gần ra xa, mỗi ô gọi on_step.
Sau mỗi lần kéo đọc lại X:Y thật (bot/ocr/read_camera.py) để biết camera đang ở đâu và kéo bù khi lệch.
"""
import math

from ..ocr import read_camera
from ..city.city_map import RETRY_SHIFTS, SWIPE_CENTER, SWIPE_TIME, SWIPE_WAIT, _moved, split

RING = 10                    # km: bề dày một vành khuyên khi quét (gần -> xa)
RADIUS = 300                 # km: bán kính quét (tạm fix cứng)
PX_X, PX_Y = 60, 30          # px ngón tay mỗi đơn vị toạ độ (xem trên)
TOLERANCE = 3                # km: camera lệch ô cần tới hơn mức này thì kéo bù
FIX_TRIES = 2                # số lần kéo bù tối đa mỗi ô
CELL = (340, 400)            # px: một ô = phần màn hình nhìn được (bỏ viền UI), kéo từ tâm ô này sang tâm ô kế


def world_to_px(u: float, v: float) -> tuple[float, float]:
    """Camera dời (dX, dY) = (u, v) đơn vị toạ độ -> dời bao nhiêu px trên màn hình."""
    return PX_X * (u - v), PX_Y * (u + v)


def px_to_world(px: float, py: float) -> tuple[float, float]:
    a, b = px / PX_X, py / PX_Y
    return (a + b) / 2, (b - a) / 2


def in_sector(u: float, v: float, start_deg: float, end_deg: float, radius: float) -> bool:
    """(u, v) (toạ độ so với gốc) nằm trong hình quạt [start_deg, end_deg] bán kính `radius`."""
    r = math.hypot(u, v)
    if r > radius:
        return False
    if r < 1e-9 or abs(end_deg - start_deg) >= 360:
        return True
    half = abs(end_deg - start_deg) / 2
    mid = (start_deg + end_deg) / 2
    diff = (math.degrees(math.atan2(v, u)) - mid + 180) % 360 - 180
    return abs(diff) <= half + 1e-9


def sector_cells(start_deg: float, end_deg: float, radius: float = RADIUS) -> list[tuple[float, float]]:
    """Tâm (px so với gốc) các ô màn hình cần ghé để phủ kín hình quạt, từ gần ra xa (vành khuyên RING km một, trong vành đi theo góc, vành kế đi ngược lại)."""
    cw, ch = CELL
    reach_x = (radius * 2 * PX_X) // cw + 1       # px_ngang tối đa = 2 * 60 * radius
    reach_y = (radius * 2 * PX_Y) // ch + 1
    rows: dict[int, list[int]] = {}
    for j in range(-int(reach_y), int(reach_y) + 1):
        for i in range(-int(reach_x), int(reach_x) + 1):
            # lấy mẫu 3x3 trong ô (cả góc ô): có điểm trong quạt thì ô cần ghé
            for fx in (-0.5, 0, 0.5):
                for fy in (-0.5, 0, 0.5):
                    if in_sector(*px_to_world((i + fx) * cw, (j + fy) * ch), start_deg, end_deg, radius):
                        rows.setdefault(j, []).append(i)
                        break
                else:
                    continue
                break
    # gần trước xa sau: chia theo vành khuyên RING km quanh gốc; trong vành đi theo góc, vành kế đi ngược lại (không phải quay về)
    mid = (start_deg + end_deg) / 2

    def polar(cell):
        u, v = px_to_world(*cell)
        return math.hypot(u, v), (math.degrees(math.atan2(v, u)) - mid + 180) % 360 - 180

    rings: dict[int, list] = {}
    for cell in (c for j, xs in rows.items() for c in ((i * cw, j * ch) for i in xs)):
        r, ang = polar(cell)
        rings.setdefault(int(r // RING), []).append((ang, cell))
    cells = [(0.0, 0.0)] if (0, 0) in {c for _, g in rings.items() for _, c in g} else []     # ô gốc (chỗ đang đứng) trước
    for n, k in enumerate(sorted(rings)):
        cells.extend(cell for _, cell in sorted(rings[k], reverse=bool(n % 2)) if cell != (0, 0))
    return cells


def _drag(bot, camera):
    """Dời camera một đoạn `camera` (px): kéo ngón tay ngược lại, tách nhỏ nếu dài hơn MAX_SWIPE. Điểm đầu trúng icon thế giới
    thì game coi là bấm, màn không đổi -> thử lại bằng điểm đầu khác (RETRY_SHIFTS)."""
    for fx, fy in split((-camera[0], -camera[1])):
        cx, cy = SWIPE_CENTER
        before = bot.screenshot()
        checkable = hasattr(before, "shape")
        for dx, dy in RETRY_SHIFTS:
            x1, y1, x2, y2 = int(cx - fx / 2) + dx, int(cy - fy / 2) + dy, int(cx + fx / 2) + dx, int(cy + fy / 2) + dy
            if (dx, dy) != (0, 0) and not all(8 <= x <= 388 and 135 <= y <= 555 for x, y in ((x1, y1), (x2, y2))):
                continue
            bot.swipe(x1, y1, x2, y2, duration=SWIPE_TIME, delay=SWIPE_WAIT)
            if not checkable or _moved(before, bot.screenshot()):
                break


def _camera(bot):
    """(X, Y) camera đọc từ thanh toạ độ, hoặc None (đọc không ra / ảnh không phải màn thật như trong test)."""
    screen = bot.screenshot()
    return read_camera(screen) if hasattr(screen, "shape") else None


def arc_sweep(bot, start_deg: float, end_deg: float, radius: float = RADIUS, on_step=None) -> int:
    """Kéo camera qua mọi ô của hình quạt [start_deg, end_deg] (VD -15 .. 15) bán kính `radius` km quanh chỗ đang đứng.
    Sau mỗi lần kéo đọc toạ độ X:Y thật; lệch ô cần tới quá TOLERANCE thì kéo bù (tối đa FIX_TRIES lần). Đọc không ra thì
    tin vào cú kéo. `on_step(u, v)` gọi tại mỗi ô với (dX, dY) của camera so với gốc; trả True thì dừng sớm. Trả số ô đã ghé."""
    origin = _camera(bot)
    pos = (0.0, 0.0)
    visited = 0
    for cell in sector_cells(start_deg, end_deg, radius):
        target = px_to_world(*cell)
        _drag(bot, (cell[0] - pos[0], cell[1] - pos[1]))
        pos = cell
        for _ in range(FIX_TRIES + 1):
            now = _camera(bot) if origin else None
            if now is None:
                break
            actual = (now[0] - origin[0], now[1] - origin[1])
            pos = world_to_px(*actual)
            bot.log(f"arc: X:{now[0]:04d} Y:{now[1]:04d} (ô cần tới {origin[0] + target[0]:.0f}, {origin[1] + target[1]:.0f})")
            error = (target[0] - actual[0], target[1] - actual[1])
            if math.hypot(*error) <= TOLERANCE:
                break
            bot.log(f"arc: camera lệch ({-error[0]:.0f}, {-error[1]:.0f}) so với ô, kéo bù")
            fix = world_to_px(*error)
            _drag(bot, fix)
            pos = (pos[0] + fix[0], pos[1] + fix[1])
        visited += 1
        if on_step is not None and on_step(*target):
            break
    return visited
