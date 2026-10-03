"""
tier.py — chọn lính cấp I trên màn Train cho nhiệm vụ Train Troop của King's Path.

Sau Go game mở ngẫu nhiên công trình train của 1 trong 4 loại lính (bộ / kỵ / cung / xe), ở cấp
bất kỳ (VD trường bắn cấp IV — tests/event/kings_path/screens/train_ranged_t04.png). Cấp I nằm
sát mép trái hàng cấp: mỗi lần chụp tìm vòng cấp I của cả 4 loại (loại nào cũng được); thấy thì
bấm, kiểm tra nút "+" rồi dừng; chưa thấy thì vuốt hàng sang trái rồi kiểm tra lại.
Dùng lại ảnh / hằng số của gather_troops/troop_tier.py (không sửa file đó).
"""
from ...gather_troops.troop_tier import (
    TAP_DELAY,
    TIER_ROW_REGION,
    TIER_THRESHOLD,
    TRAIN_PLUS,
    TRAIN_PLUS_REGION,
)
from .constants import FIRST_TIER_SWIPE, FIRST_TIER_SWIPE_WAIT, FIRST_TIER_SWIPES, TIERS


def choose_first_tier(bot, tiers=TIERS) -> int | None:
    """Chọn cấp thấp nhất (cấp I) trong `tiers` = {1: [ảnh cấp I của từng loại]}: tìm trong hàng
    cấp, thấy thì bấm + kiểm tra nút "+"; chưa thấy thì vuốt FIRST_TIER_SWIPE, tối đa
    FIRST_TIER_SWIPES lần. Trả cấp đã chọn, hoặc None nếu không thấy / không train được."""
    first = min(tiers)
    images = tiers[first] if isinstance(tiers[first], list) else [tiers[first]]
    for swipes in range(FIRST_TIER_SWIPES + 1):
        screen = bot.screenshot()
        score, pos = max(bot.best_match(path, screen=screen, region=TIER_ROW_REGION)
                         for path in images)
        if pos is not None and score >= TIER_THRESHOLD:
            bot.log(f"Train: tier {first} at {pos} (score {score:.2f}) after {swipes} swipe(s)")
            bot.tap(*pos, delay=TAP_DELAY)
            if bot.find(TRAIN_PLUS, region=TRAIN_PLUS_REGION) is None:
                bot.log(f"Train: tier {first} cannot be trained")
                return None
            return first
        if swipes < FIRST_TIER_SWIPES:
            bot.swipe_percent(*FIRST_TIER_SWIPE, duration=0.5, delay=FIRST_TIER_SWIPE_WAIT)
    bot.record(f"Train: tier {first} not found after {FIRST_TIER_SWIPES} swipes")
    return None
