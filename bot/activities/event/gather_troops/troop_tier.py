"""
troop_tier.py — chọn cấp lính trên màn Train (doanh trại / chuồng ngựa / ...), dùng chung
cho các nhiệm vụ train lính của Gather Troops (Ground Troop, Mounted Troop, ...).

Màn Train có hàng vòng tròn cấp lính I..XVII (y ~452). Bấm vào cấp nào thì cấp đó nhảy
ra giữa hàng (x ~198), mỗi lần thấy ~5 cấp: giữa ±2 (cách nhau ~87 px). Cấp chưa mở có
ổ khoá ở góc trên phải vòng tròn; cấp khoá luôn là các cấp cao nhất. Lúc mở màn, cấp
đang chọn là cấp train lần trước (không phải cấp cao nhất).

choose_tier(): đi lên từ cấp đang thấy (bấm cấp phải nhất, nó nhảy ra giữa) tới khi thấy
cấp muốn train hoặc gặp cấp khoá (kiểm tra cấp vừa bấm bằng nút "+"); cấp muốn train bị
khoá thì lấy cấp mở cao nhất dưới nó. Không cần tìm cấp cao nhất của tài khoản.
"""
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
# bấm có khoá không. Khớp 1,00 trên mọi màn Train cấp mở (cả lính kỵ...); cấp khoá <= 0,32;
# màn khác <= 0,51.
TRAIN_PLUS = f"{EV}/GatherTroops/Train/trainPlus.png"
TRAIN_PLUS_REGION = (50, 75, 75, 90)
# Hàng vòng tròn cấp lính (% màn hình) và tâm hàng (px trên màn 396x704).
TIER_ROW_REGION = (0, 59, 100, 70)
TIER_CENTER_X = 198
TIER_CENTER_TOLERANCE = 25          # px: vòng tròn cách TIER_CENTER_X <= mức này là đang ở giữa
# Mỗi cấp là một ảnh <cấp>.png (phần dưới vòng tròn: hình lính + số La Mã, tránh góc ổ
# khoá). Đo trên 9 ảnh (giữa V..XIII): cùng cấp >= 0,78 ở vị trí thường, 0,70 khi vòng
# tròn bị cắt ở mép; cấp khác <= 0,55 -> ngưỡng 0,65 không khớp nhầm cấp.
TIER_THRESHOLD = 0.65
TIER_SAME_CIRCLE = 40               # px: hai cấp khớp gần hơn mức này là cùng một vòng tròn
TAP_DELAY = 1.5                     # giây chờ vòng tròn vừa bấm trượt ra giữa
MAX_STEPS = 12                      # số lần bấm tối đa (đi hết 17 cấp, 2 cấp mỗi lần)


def tier_images(folder: str) -> dict[int, str]:
    """{cấp: đường dẫn ảnh} từ thư mục ảnh <cấp>.png (VD Event/GatherTroops/GroundTroop/Tier)."""
    return {int(path.rsplit("/", 1)[-1].split(".")[0]): path for path in images_in(folder)}


def visible_tiers(bot, screen, tiers: dict[int, str]) -> dict[int, tuple[int, int, bool]]:
    """{cấp: (x, y, có khoá)} của các vòng tròn đang thấy trên hàng cấp lính. Cấp khoá
    luôn là các cấp cao nhất: thấy một cấp khoá thì mọi cấp cao hơn cũng khoá (vòng tròn
    sát mép phải bị cắt mất ổ khoá)."""
    seen = {}
    for tier, path in sorted(tiers.items()):
        pos = bot.find(path, threshold=TIER_THRESHOLD, screen=screen, region=TIER_ROW_REGION)
        if pos is not None and all(abs(pos[0] - x) > TIER_SAME_CIRCLE for x, _, _ in seen.values()):
            seen[tier] = (*pos, _locked(bot, screen, *pos))
    locked = [t for t, v in seen.items() if v[2]]
    if locked:
        seen = {t: (x, y, lock or t > min(locked)) for t, (x, y, lock) in seen.items()}
    return seen


def choose_tier(bot, tiers: dict[int, str], want: int, lowest: int) -> int | None:
    """Chọn (bấm, để nằm giữa hàng) cấp mở cao nhất <= `want`. Trả cấp đã chọn, hoặc None
    nếu cấp `lowest` cũng khoá / không nhận ra hàng cấp lính.

    Cấp ở giữa (cấp đang chọn: lúc mới vào là cấp train lần trước, luôn mở; sau đó là cấp
    vừa bấm) được kiểm tra bằng nút "+" (có = train được, không = khoá). Ổ khoá trên các
    vòng tròn khác chỉ là gợi ý để bớt số lần bấm."""
    locked_from = None   # cấp khoá thấp nhất đã biết (mọi cấp từ đó trở lên khoá)
    for _ in range(MAX_STEPS):
        screen = bot.screenshot()
        seen = visible_tiers(bot, screen, tiers)
        if not seen:
            bot.log("Train: tier row not found")
            return None
        center = _center_tier(seen)
        trainable = bot.find(TRAIN_PLUS, screen=screen, region=TRAIN_PLUS_REGION) is not None
        locked = [t for t, v in seen.items() if v[2]]
        if center is not None and not trainable:
            locked.append(center)
        if locked:
            locked_from = min([*locked, locked_from or min(locked)])
        bot.log(f"Train: center {center} {'open' if trainable else 'locked'}, "
                f"tiers {sorted(seen)}, locked from {locked_from}")
        result = want if locked_from is None else min(want, locked_from - 1)
        if result < lowest:
            bot.log(f"Train: tier {lowest} locked")
            return None
        if center == result and trainable:
            return result
        if result in seen:
            tier = result                # đang thấy cấp kết quả: bấm cho nó ra giữa
        elif max(seen) < result:
            tier = max(seen)             # chưa tới: bấm cấp phải nhất (nhảy ra giữa) để đi lên
        else:
            tier = min(seen)             # đã vượt quá / khoá: bấm cấp trái nhất để đi xuống
        bot.tap(*seen[tier][:2], delay=TAP_DELAY)
    bot.log("Train: cannot choose tier")
    return None


def _center_tier(seen) -> int | None:
    """Cấp đang ở giữa hàng (cấp đang chọn), hoặc None."""
    for tier, (x, _, _) in seen.items():
        if abs(x - TIER_CENTER_X) <= TIER_CENTER_TOLERANCE:
            return tier
    return None


def _locked(bot, screen, x: int, y: int) -> bool:
    dx, dy = TIER_LOCK_OFFSET
    lock = bot.crop(screen, x + dx - 18, y + dy - 18, 36, 36)
    return bot.find(TIER_LOCK, threshold=TIER_LOCK_THRESHOLD, screen=lock) is not None
