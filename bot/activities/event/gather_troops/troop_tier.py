"""
troop_tier.py — chọn cấp lính trên màn Train (doanh trại / chuồng ngựa / xưởng bẫy ...),
dùng chung cho các nhiệm vụ train của Gather Troops (và King's Path Train Troop).

Màn Train có hàng vòng tròn (y ~452). Bấm vào vòng nào thì vòng đó được chọn và nhảy ra giữa
hàng (x ~198), mỗi lần thấy ~5 vòng: giữa ±2 (cách nhau ~87 px). Lúc mở màn, vòng đang chọn là
vòng train lần trước (không phải cao nhất, có khi chưa nằm giữa).

Hình lính trên vòng tròn khác nhau theo nền văn minh nên KHÔNG dùng ảnh lính:
- Cấp của vòng đang chọn: đọc huy hiệu số La Mã cạnh tên lính ("VII Man-at-Arms", y ~364) —
  huy hiệu nền tối, số giống nhau ở mọi loại lính / nền văn minh: ảnh BADGE_DIR/<cấp>.png (I ..
  XVI). Đo trên 46 màn Train (4 loại lính + bẫy, cả hàng đang cuộn): đọc đúng 46/46; kiểm tra
  chéo (mẫu dựng không có ảnh đang đọc) 39/39, cấp đúng hơn cấp gần nhất >= 0,12.
- Vị trí các vòng: khung đồng của vòng tròn (RING, chỉ so phần vành RING_MASK, bỏ hình lính
  bên trong): 0,63 .. 0,90 trên mọi màn Train; vòng sát mép có khi không thấy.
- Train được hay khoá: nút "+" (TRAIN_PLUS) của vòng đang chọn.

- Lính (Ground / Mounted / Ranged / Siege): mỗi cấp một vòng. Cấp khoá luôn là các cấp cao nhất.
- Bẫy (Defense Force): mỗi cấp 4 vòng liền nhau (4 loại bẫy), loại nào cũng được. Khoá theo
  từng loại (VD Fire Arrow III khoá mà Trap IV mở) -> một cấp chỉ coi là khoá khi cả 4 loại đều
  khoá.

choose_tier(): tìm vòng đang chọn (viền cam — không phải lúc nào cũng nằm giữa: cấp đầu / cuối hàng
không cuộn ra giữa được), đọc huy hiệu, rồi bấm vòng cách nó 1 .. 2 ô về phía cấp muốn train, đọc
lại, tới khi vòng đang chọn đúng cấp và train được; cấp muốn train khoá thì lấy cấp mở cao nhất
dưới nó. Không cần tìm cấp cao nhất của tài khoản.

`tiers` (ảnh lính cũ, {cấp: ảnh} hoặc {cấp: [ảnh từng loại]}) chỉ còn dùng để biết số loại mỗi cấp.
"""
import cv2
import numpy as np

from ....common import images_in
from ..constants import EV

# Ổ khoá trên vòng tròn cấp lính (khác ổ khoá tab Day). Khớp 0,95-1,00 trên vòng thường; vòng
# đang chọn 0,70-0,82; vòng không khoá <= 0,5.
TIER_LOCK = f"{EV}/GatherTroops/Train/tierLock.png"
TIER_LOCK_THRESHOLD = 0.6
# Nút "+" cạnh thanh kéo số lượng, tâm (256, 581): chỉ có khi cấp đang chọn train được; cấp khoá
# thay bằng chữ đỏ "Upgrade to Level ..." -> cách chắc nhất để biết cấp đang chọn có khoá không.
# Khớp 1,00 trên mọi màn Train cấp mở (cả lính kỵ, bẫy...); cấp khoá <= 0,32; màn khác <= 0,51.
TRAIN_PLUS = f"{EV}/GatherTroops/Train/trainPlus.png"
TRAIN_PLUS_REGION = (50, 75, 75, 90)
# Hàng vòng tròn cấp lính (% màn hình).
TIER_ROW_REGION = (0, 59, 100, 70)
# Ảnh vòng lính cũ (hình lính + số): ngưỡng khi còn dùng để nhận màn Train ở nơi khác.
TIER_THRESHOLD = 0.65

# Huy hiệu số La Mã cạnh tên lính: ảnh <cấp>.png (30x20, phần trong vòng huy hiệu); vị trí ngang
# đổi theo độ dài tên lính -> tìm cả dải. Cấp đúng 0,76 .. 1,00; cấp khác <= 0,86 khi cấp đúng cao.
BADGE_DIR = f"{EV}/GatherTroops/Train/Badge"
BADGE_REGION = (10, 48, 90, 56)     # % màn hình: y 338 .. 394
BADGE_THRESHOLD = 0.7
# Khung vòng tròn (60x60, vành bán kính 21 .. 28 px).
RING = f"{EV}/GatherTroops/Train/tierRing.png"
RING_RADII = (21, 28)
RING_THRESHOLD = 0.6
RING_ROW_Y = 452                    # px: tâm hàng vòng tròn (màn 396x704)
RING_SEARCH = 25                    # px: tìm lệch lên / xuống quanh RING_ROW_Y
TIER_CENTER_X = 198
TIER_STEP = 87                      # px: khoảng cách hai vòng liền nhau
TIER_CENTER_TOLERANCE = 25          # px: vòng cách TIER_CENTER_X <= mức này là đang ở giữa
TIER_SAME_CIRCLE = 40               # px: hai chỗ khớp gần hơn mức này là cùng một vòng tròn
TAP_DELAY = 1.5                     # giây chờ vòng tròn vừa bấm trượt ra giữa
MAX_STEPS = 60                      # số lần bấm tối đa (bẫy: 4 vòng mỗi cấp; lùi qua nhiều cấp khoá ~25)
END_OF_ROW = 1000                   # cấp giả của "vòng" sau đầu / cuối hàng (choose_tier)
# Vòng đang chọn: viền cam sáng trên vành bán kính GLOW_R (px). Tỉ lệ pixel cam: vòng đang chọn
# 0,06 .. 0,11; vòng khác <= 0,03.
GLOW_R = (26, 33)
SELECTED_GLOW = 0.045


def tier_images(folder: str) -> dict[int, str]:
    """{cấp: đường dẫn ảnh} từ thư mục ảnh <cấp>.png (VD Event/GatherTroops/GroundTroop/Tier)."""
    return {int(path.rsplit("/", 1)[-1].split(".")[0]): path for path in images_in(folder)}


def kind_images(folder: str, kinds: list[str]) -> dict[int, list[str]]:
    """{cấp: [ảnh loại 1, ...]} từ thư mục ảnh <cấp>_<loại>.png, loại theo thứ tự `kinds`
    (thứ tự trên hàng vòng tròn). VD Event/GatherTroops/DefenseForce/Tier/3_trap.png."""
    found = {}
    for path in images_in(folder):
        level, kind = path.rsplit("/", 1)[-1].rsplit(".", 1)[0].split("_")
        found[(int(level), kind)] = path
    levels = sorted({level for level, _ in found})
    return {level: [found[(level, kind)] for kind in kinds if (level, kind) in found]
            for level in levels}


BADGES = tier_images(BADGE_DIR)


def read_tier(bot, screen) -> int | None:
    """Cấp của vòng đang chọn (huy hiệu số La Mã cạnh tên lính), hoặc None."""
    score, tier = max((bot.best_match(path, screen=screen, region=BADGE_REGION)[0], tier)
                      for tier, path in BADGES.items())
    return tier if score >= BADGE_THRESHOLD else None


def tier_circles(bot, screen) -> list[int]:
    """Tâm x các vòng tròn đang thấy trên hàng (khung đồng, không xét hình lính), trái sang phải."""
    ring = bot._template(RING)
    size = ring.shape[0] // 2
    yy, xx = np.mgrid[-size:size, -size:size]
    radius = np.hypot(xx + 0.5, yy + 0.5)
    mask = ((radius >= RING_RADII[0]) & (radius <= RING_RADII[1])).astype(np.uint8)
    top = RING_ROW_Y - size - RING_SEARCH
    band = screen[max(0, top):RING_ROW_Y + size + RING_SEARCH]
    result = cv2.matchTemplate(band, ring, cv2.TM_CCOEFF_NORMED, mask=np.dstack([mask] * 3))
    column = np.nan_to_num(result, nan=-1, posinf=-1, neginf=-1).max(0)
    found = []
    for x in np.argsort(-column):
        if column[x] < RING_THRESHOLD:
            break
        if all(abs(int(x) - other) > TIER_SAME_CIRCLE for other in found):
            found.append(int(x))
    return sorted(x + size for x in found)


def selected_circle(screen, circles) -> int | None:
    """Tâm x vòng đang chọn (viền cam sáng: tỉ lệ pixel cam trên vành >= SELECTED_GLOW; vòng khác
    <= 0,03), hoặc None nếu vòng đang chọn không có trên màn (hàng đã cuộn). Xét cả các vị trí
    cách vòng thấy được k ô (vòng đang chọn có viền sáng nên có khi không khớp khung RING).
    Đo trên 50 màn Train: vòng đang chọn 0,06 .. 0,11 — ở giữa, sát đầu hàng (x 37, 124) hay lệch
    (x 233)."""
    spots = []
    for x in sorted({x + k * TIER_STEP for x in circles for k in range(-2, 3)}):
        if GLOW_R[1] <= x <= screen.shape[1] - GLOW_R[1] and all(abs(x - s) > 20 for s in spots):
            spots.append(x)
    best, best_x = 0.0, None
    for x in spots:
        glow = _glow(screen, x)
        if glow > best:
            best, best_x = glow, x
    if best_x is None or best < SELECTED_GLOW:
        return None
    # Vị trí ước lượng (vòng thấy được + k ô) có thể lệch vài px: lấy vòng thấy được gần nhất.
    near = [c for c in circles if abs(c - best_x) <= TIER_CENTER_TOLERANCE]
    return near[0] if near else best_x


def _glow(screen, x: int) -> float:
    """Tỉ lệ pixel cam sáng trên vành (bán kính GLOW_R) quanh tâm (x, RING_ROW_Y)."""
    r = GLOW_R[1]
    hsv = cv2.cvtColor(screen[RING_ROW_Y - r:RING_ROW_Y + r, x - r:x + r], cv2.COLOR_BGR2HSV)
    yy, xx = np.mgrid[-r:r, -r:r]
    radius = np.hypot(xx + 0.5, yy + 0.5)
    ring = (radius >= GLOW_R[0]) & (radius <= GLOW_R[1])
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    orange = (h >= 8) & (h <= 30) & (s >= 120) & (v >= 150)
    return float(orange[ring].mean())


def choose_tier(bot, tiers, want: int, lowest: int) -> int | None:
    """Chọn (bấm) một vòng của cấp mở cao nhất <= `want`. Trả cấp đã chọn, hoặc None nếu mọi cấp
    từ `lowest` tới `want` đều khoá / không đọc được hàng.

    Mỗi bước tìm vòng đang chọn (viền cam, selected_circle — KHÔNG giả định nằm giữa: cấp thấp
    nhất / cao nhất ở đầu hàng không cuộn ra giữa được), đọc cấp, rồi bấm vòng cách nó 1 .. 2 ô."""
    kinds = max((len(paths) if isinstance(paths, (list, tuple)) else 1)
                for paths in tiers.values()) if tiers else 1
    seen: dict[int, tuple[int, bool]] = {}   # thứ tự vòng (tính từ vòng chọn đầu tiên) -> (cấp, khoá)
    index = 0
    for _ in range(MAX_STEPS):
        screen = bot.screenshot()
        circles = tier_circles(bot, screen)
        if not circles:
            bot.record("Train: tier row not found")
            return None
        selected = selected_circle(screen, circles)
        if selected is None:
            # Vòng đang chọn đã cuộn khỏi màn: chọn vòng gần giữa nhất, đếm lại từ đầu.
            nearest = min(circles, key=lambda x: abs(x - TIER_CENTER_X))
            bot.log("Train: selected tier not visible, tapping the circle nearest to center")
            bot.tap(nearest, RING_ROW_Y, delay=TAP_DELAY)
            seen, index = {}, 0
            continue
        tier = read_tier(bot, screen)
        if tier is None:
            bot.record("Train: tier badge not readable")
            return None
        trainable = bot.find(TRAIN_PLUS, screen=screen, region=TRAIN_PLUS_REGION) is not None
        seen[index] = (tier, not trainable)
        goal = _goal(seen, want, lowest, kinds)
        bot.log(f"Train: selected tier {tier} {'open' if trainable else 'locked'}, goal {goal}")
        if goal is None:
            bot.log(f"Train: tier {lowest} locked")
            return None
        if tier == goal and trainable:
            return goal
        move = _move(seen, index, tier, goal, kinds)
        target = _circle_at(circles, selected, move)
        if target is None and tier == goal:
            # Đang thử các loại cùng cấp mà hết hàng phía đó (cấp cao / thấp nhất của game):
            # ghi một "vòng" giả khác cấp ở đầu hàng rồi xét lại (sang phía còn lại).
            side = 1 if move > 0 else -1
            seen[index + side] = (tier + side * END_OF_ROW, True)
            continue
        if target is None:
            bot.record("Train: next tier circle not found")
            return None
        x, step = target
        bot.tap(x, RING_ROW_Y, delay=TAP_DELAY)
        index += step
    bot.record("Train: cannot choose tier")
    return None


def _goal(seen, want, lowest, kinds) -> int | None:
    """Cấp cao nhất trong [lowest, want] chưa biết là khoá. Lính: cấp khoá thấp nhất trở lên đều
    khoá. Bẫy: một cấp khoá khi mọi vòng của nó đã thấy đều khoá và đã thấy đủ `kinds` vòng,
    hoặc đã thấy hết các vòng của nó (hai đầu là vòng cấp khác)."""
    if kinds == 1:
        locked = [tier for tier, is_locked in seen.values() if is_locked]
        goal = min([want] + [tier - 1 for tier in locked])
        return goal if goal >= lowest else None
    for tier in range(want, lowest - 1, -1):
        indices = [i for i, (t, _) in seen.items() if t == tier]
        if not indices or any(not seen[i][1] for i in indices):
            return tier
        if len(indices) < kinds and _open_side(seen, indices[0], tier) is not None:
            return tier
    return None


def _move(seen, index, tier, goal, kinds) -> int:
    """Số ô cần đi từ vòng giữa (âm: sang trái). Khác cấp: đi về phía `goal` (tối đa 2 ô, vì
    mỗi lần thấy giữa ±2). Đúng cấp mà khoá (bẫy): sang vòng chưa thử của cùng cấp."""
    if tier != goal:
        return max(-2, min(2, (goal - tier) * kinds))
    side = _open_side(seen, index, goal)
    return 1 if side is None else max(-2, min(2, side - index))


def _open_side(seen, index, tier) -> int | None:
    """Thứ tự vòng chưa thấy gần nhất nằm trong dãy vòng cùng `tier` quanh `index` (bên phải
    trước), hoặc None nếu dãy đã thấy hết (hai đầu là vòng cấp khác)."""
    right = index + 1
    while right in seen and seen[right][0] == tier:
        right += 1
    if right not in seen:
        return right
    left = index - 1
    while left in seen and seen[left][0] == tier:
        left -= 1
    return left if left not in seen else None


def _circle_at(circles, selected, move):
    """(x, số ô thật) của vòng cách vòng đang chọn `move` ô; không thấy (sát mép / hết hàng) thì
    thử ô gần hơn."""
    step = move
    while step != 0:
        x = selected + step * TIER_STEP
        near = [c for c in circles if abs(c - x) <= TIER_CENTER_TOLERANCE]
        if near:
            return near[0], step
        step -= 1 if step > 0 else -1
    return None
