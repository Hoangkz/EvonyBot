"""
troop_tier.py — chọn cấp lính trên màn Train (doanh trại / chuồng ngựa / xưởng bẫy ...),
dùng chung cho các nhiệm vụ train của Gather Troops.

Màn Train có hàng vòng tròn (y ~452). Bấm vào vòng nào thì vòng đó nhảy ra giữa hàng
(x ~198), mỗi lần thấy ~5 vòng: giữa ±2 (cách nhau ~87 px). Vòng chưa mở có ổ khoá ở góc
trên phải. Lúc mở màn, vòng đang chọn là vòng train lần trước (không phải cao nhất).

- Lính (Ground / Mounted / Ranged / Siege): mỗi cấp một vòng (I, II, ...). Cấp khoá luôn
  là các cấp cao nhất.
- Bẫy (Defense Force): mỗi cấp 4 vòng liền nhau (4 loại bẫy), loại nào cũng được. Khoá
  theo từng loại (VD Fire Arrow III khoá mà Trap IV mở) -> một cấp chỉ coi là khoá khi cả
  4 loại đều khoá.

`tiers` = {cấp: ảnh} (mỗi cấp một vòng) hoặc {cấp: [ảnh loại 1, ảnh loại 2, ...]} theo thứ
tự trên hàng. Vòng tròn thứ tự trên hàng = (cấp, loại).

choose_tier(): đi lên từ vòng đang thấy (bấm vòng phải nhất, nó nhảy ra giữa) tới khi thấy
cấp muốn train hoặc gặp cấp khoá (kiểm tra vòng vừa bấm bằng nút "+"); cấp muốn train bị
khoá thì lấy cấp mở cao nhất dưới nó. Không cần tìm cấp cao nhất của tài khoản.
"""
from dataclasses import dataclass

from ....common import images_in
from ..constants import EV

# Ổ khoá trên vòng tròn cấp lính (khác ổ khoá tab Day): tâm (x+21, 431) với tâm vòng tròn
# (x, 452), tức lệch (+21, -32) so với điểm khớp ảnh cấp (tâm phần dưới vòng tròn, y 463).
# Khớp 0,95-1,00 trên vòng thường; vòng đang chọn (viền vàng sáng phía sau) 0,70-0,82;
# vòng tròn không khoá <= 0,5 -> ngưỡng 0,6.
TIER_LOCK = f"{EV}/GatherTroops/Train/tierLock.png"
TIER_LOCK_THRESHOLD = 0.6
TIER_LOCK_OFFSET = (21, -32)
# Nút "+" cạnh thanh kéo số lượng, tâm (256, 581): chỉ có khi cấp đang chọn (ở giữa) train
# được; cấp khoá thay bằng chữ đỏ "Upgrade to Level ..." -> cách chắc nhất để biết cấp vừa
# bấm có khoá không. Khớp 1,00 trên mọi màn Train cấp mở (cả lính kỵ, bẫy...); cấp khoá
# <= 0,32; màn khác <= 0,51.
TRAIN_PLUS = f"{EV}/GatherTroops/Train/trainPlus.png"
TRAIN_PLUS_REGION = (50, 75, 75, 90)
# Hàng vòng tròn cấp lính (% màn hình) và tâm hàng (px trên màn 396x704).
TIER_ROW_REGION = (0, 59, 100, 70)
TIER_CENTER_X = 198
TIER_CENTER_TOLERANCE = 25          # px: vòng tròn cách TIER_CENTER_X <= mức này là đang ở giữa
# Mỗi vòng là một ảnh (phần dưới vòng tròn: hình lính + số La Mã, tránh góc ổ khoá). Lính:
# đo trên 9 ảnh (giữa V..XIII): cùng cấp >= 0,78 ở vị trí thường, 0,70 khi vòng tròn bị cắt
# ở mép; cấp khác <= 0,55 -> ngưỡng 0,65 không khớp nhầm cấp. Bẫy: các loại cùng cấp khớp
# chéo tới 0,83 -> tại mỗi vòng lấy ảnh khớp CAO NHẤT (luôn đúng loại); cấp khác <= 0,65.
TIER_THRESHOLD = 0.65
TIER_SAME_CIRCLE = 40               # px: hai chỗ khớp gần hơn mức này là cùng một vòng tròn
TAP_DELAY = 1.5                     # giây chờ vòng tròn vừa bấm trượt ra giữa
MAX_STEPS = 30                      # số lần bấm tối đa (bẫy: 4 vòng mỗi cấp)


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


@dataclass(frozen=True)
class Circle:
    """Một vòng tròn đang thấy trên hàng: (cấp, loại) và vị trí."""
    tier: int
    kind: int        # thứ tự loại trong cấp (lính: luôn 0)
    x: int
    y: int
    locked: bool     # có ổ khoá


def visible_circles(bot, screen, tiers) -> list[Circle]:
    """Các vòng tròn đang thấy trên hàng, trái sang phải. Mỗi vòng lấy ảnh khớp cao nhất.
    Lính (mỗi cấp một vòng): cấp khoá luôn là các cấp cao nhất, thấy một cấp khoá thì mọi
    cấp cao hơn cũng khoá (vòng tròn sát mép phải bị cắt mất ổ khoá)."""
    images = [(tier, kind, path) for tier, paths in sorted(_as_lists(tiers).items())
              for kind, path in enumerate(paths)]
    spots = []   # tâm các vòng tròn (từ mọi ảnh khớp >= ngưỡng)
    for _, _, path in images:
        for pos in bot.find_all(path, threshold=TIER_THRESHOLD, screen=screen,
                                region=TIER_ROW_REGION):
            if all(abs(pos[0] - x) > TIER_SAME_CIRCLE for x, _ in spots):
                spots.append(pos)
    circles = []
    for x, y in sorted(spots):
        area = bot.crop(screen, x - TIER_SAME_CIRCLE, y - 20, 2 * TIER_SAME_CIRCLE, 40)
        _, tier, kind = max((bot.best_match(path, screen=area)[0], tier, kind)
                            for tier, kind, path in images)
        circles.append(Circle(tier, kind, x, y, _locked(bot, screen, x, y)))
    if all(len(paths) == 1 for paths in _as_lists(tiers).values()):
        locked = [c.tier for c in circles if c.locked]
        if locked:
            circles = [Circle(c.tier, c.kind, c.x, c.y, c.locked or c.tier > min(locked))
                       for c in circles]
    return circles


def choose_tier(bot, tiers, want: int, lowest: int) -> int | None:
    """Chọn (bấm, để nằm giữa hàng) một vòng của cấp mở cao nhất <= `want`. Trả cấp đã
    chọn, hoặc None nếu mọi cấp từ `lowest` tới `want` đều khoá / không nhận ra hàng.

    Vòng ở giữa (lúc mới vào là vòng train lần trước, luôn mở; sau đó là vòng vừa bấm)
    được kiểm tra bằng nút "+" (có = train được, không = khoá). Ổ khoá trên các vòng khác
    giúp bớt số lần bấm."""
    tiers = _as_lists(tiers)
    kinds = max(len(paths) for paths in tiers.values())
    single = kinds == 1
    locked = set()   # (cấp, loại) đã biết là khoá
    for _ in range(MAX_STEPS):
        screen = bot.screenshot()
        circles = visible_circles(bot, screen, tiers)
        if not circles:
            bot.log("Train: tier row not found")
            return None
        center = next((c for c in circles if abs(c.x - TIER_CENTER_X) <= TIER_CENTER_TOLERANCE),
                      None)
        trainable = bot.find(TRAIN_PLUS, screen=screen, region=TRAIN_PLUS_REGION) is not None
        locked |= {(c.tier, c.kind) for c in circles if c.locked}
        if center is not None and not trainable:
            locked.add((center.tier, center.kind))
        goal = _goal(tiers, locked, want, lowest, single)
        bot.log(f"Train: center {_name(center)} {'open' if trainable else 'locked'}, "
                f"tiers {sorted({c.tier for c in circles})}, goal {goal}")
        if goal is None:
            bot.log(f"Train: tier {lowest} locked")
            return None
        if center is not None and center.tier == goal and trainable:
            return goal
        target = _next_tap(circles, locked, goal, kinds)
        bot.tap(target.x, target.y, delay=TAP_DELAY)
    bot.log("Train: cannot choose tier")
    return None


def _goal(tiers, locked, want, lowest, single) -> int | None:
    """Cấp cao nhất trong [lowest, want] chưa biết là khoá. Lính: khoá từ cấp khoá thấp
    nhất trở lên; bẫy: một cấp khoá khi cả mọi loại của nó đều khoá."""
    if single:
        locked_from = min((tier for tier, _ in locked), default=None)
        goal = want if locked_from is None else min(want, locked_from - 1)
        return goal if goal >= lowest else None
    for tier in range(want, lowest - 1, -1):
        kinds = len(tiers.get(tier, [None]))
        if any((tier, kind) not in locked for kind in range(kinds)):
            return tier
    return None


def _next_tap(circles, locked, goal, kinds) -> Circle:
    """Vòng cần bấm để tới cấp `goal`: đang thấy một vòng của nó chưa biết khoá thì bấm vòng
    đó (gần giữa nhất); chưa thấy thì bấm vòng phải nhất (đi lên) / trái nhất (đi xuống)
    về phía loại chưa biết khoá của cấp đó."""
    candidates = [c for c in circles if c.tier == goal and (c.tier, c.kind) not in locked]
    if candidates:
        return min(candidates, key=lambda c: abs(c.x - TIER_CENTER_X))
    order = [c.tier * kinds + c.kind for c in circles]
    wanted = max(goal * kinds + kind for kind in range(kinds) if (goal, kind) not in locked)
    return circles[-1] if wanted > max(order) else circles[0]


def _name(circle) -> str:
    return "None" if circle is None else f"{circle.tier}/{circle.kind}"


def _as_lists(tiers) -> dict[int, list[str]]:
    return {tier: [paths] if isinstance(paths, str) else list(paths)
            for tier, paths in tiers.items()}


def _locked(bot, screen, x: int, y: int) -> bool:
    dx, dy = TIER_LOCK_OFFSET
    lock = bot.crop(screen, x + dx - 18, y + dy - 18, 36, 36)
    return bot.find(TIER_LOCK, threshold=TIER_LOCK_THRESHOLD, screen=lock) is not None
