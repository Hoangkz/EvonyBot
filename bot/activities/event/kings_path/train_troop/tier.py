"""
tier.py — chọn lính cấp I trên màn Train cho nhiệm vụ Train Troop của King's Path.

Sau Go game mở ngẫu nhiên công trình train của 1 trong 4 loại lính (bộ / kỵ / cung / xe), ở cấp
bất kỳ (VD trường bắn cấp IV — tests/event/kings_path/screens/train_ranged_t04.png). Chọn cấp I
bằng gather_troops/troop_tier.choose_tier: đọc cấp ở huy hiệu số La Mã (không dùng hình lính —
khác nhau theo nền văn minh), bấm vòng bên trái tới khi vòng đang chọn là cấp I, kiểm tra nút "+".
"""
from ...gather_troops.troop_tier import choose_tier
from .constants import LOWEST


def choose_first_tier(bot, tiers=None) -> int | None:
    """Chọn cấp thấp nhất (cấp I). Trả cấp đã chọn, hoặc None nếu không đọc được hàng cấp /
    cấp I không train được. `tiers` (ảnh lính cũ) không còn dùng, giữ cho chỗ gọi cũ."""
    first = LOWEST if not tiers else min(tiers)
    tier = choose_tier(bot, {first: None}, first, first)
    if tier is None:
        bot.log(f"Train: tier {first} cannot be trained")
    return tier
