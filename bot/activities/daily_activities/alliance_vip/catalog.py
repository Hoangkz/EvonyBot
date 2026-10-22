"""Danh sách rút gọn các vật phẩm Alliance Shop được phép tự động mua."""
from dataclasses import dataclass


SETTINGS_KEY = "Alliance VIP Items"


@dataclass(frozen=True)
class ShopItem:
    key: str
    label: str
    maximum: int
    default: bool = False

    @property
    def template(self) -> str:
        return f"DailyActivites/ActivitiesAllianceVip/Items/{self.key}.png"


ITEMS = (
    # Hai vật phẩm này luôn đứng đầu, mặc định bật và được tìm trước.
    ShopItem("tribute", "Tribute", 5, default=True),
    ShopItem("vip_points", "100 VIP Points", 5, default=True),
    ShopItem("food_100k", "Food 100K", 200),
    ShopItem("lumber_100k", "Lumber 100K", 200),
    ShopItem("stone_100k", "Stone 100K", 200),
    ShopItem("ore_100k", "Ore 100K", 200),
    ShopItem("food_500k", "Food 500K", 50),
    ShopItem("lumber_500k", "Lumber 500K", 50),
    ShopItem("stone_500k", "Stone 500K", 50),
    ShopItem("ore_500k", "Ore 500K", 50),
    ShopItem("chip_100", "100 Chips", 5),
    ShopItem("chip_1000", "1K Chips", 1),
    ShopItem("truce_agreement_8h", "Truce 8h", 3),
    ShopItem("truce_agreement_24h", "Truce 24h", 1),
    ShopItem("truce_agreement_3d", "Truce 3d", 1),
)

BY_KEY = {item.key: item for item in ITEMS}


def normalized(raw: object, *, legacy_defaults: bool = True) -> dict[str, int]:
    """Đổi cấu hình checkbox sang 0/MAX; vẫn đọc được cấu hình số cũ."""
    values = raw if isinstance(raw, dict) else {}
    aliases = {
        "vip_points": "vip_points_100",
        "chip_100": "chips_100",
        "chip_1000": "chips_1k",
        "truce_agreement_8h": "truce_8h",
        "truce_agreement_24h": "truce_24h",
        "truce_agreement_3d": "truce_3d",
    }
    result = {}
    for item in ITEMS:
        fallback = item.default if legacy_defaults and not isinstance(raw, dict) else False
        value = values.get(item.key, values.get(aliases.get(item.key, ""), fallback))
        result[item.key] = item.maximum if bool(value) else 0
    return result
