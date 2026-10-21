"""Danh mục và bố cục lựa chọn vật phẩm Black Market."""
import unittest
from pathlib import Path

import cv2

from bot.activities.black_market.items import DATA
from bot.activities.black_market.run import wanted_items


class BlackMarketCatalogTest(unittest.TestCase):
    def test_general_group_combines_resource_stamina_chips_and_tribute(self):
        members = [item["id"] for item in DATA["items"]
                   if item["group"] == "general"]
        self.assertEqual(
            ["chips_100", "stamina_50", "tribute"],
            members,
        )
        self.assertEqual("General", DATA["groups"]["general"])
        self.assertNotIn("stamina_chips", DATA["groups"])

    def test_tribute_checkbox_selects_named_template(self):
        selected = wanted_items({
            "resources": False,
            "items": {"tribute": True},
        })

        self.assertEqual(1, len(selected))
        self.assertEqual("tribute", selected[0].id)
        self.assertEqual(["Black Market/Items/Tribute.png"], selected[0].icons)
        self.assertTrue(selected[0].gems_ok)

    def test_tribute_is_opt_in(self):
        tribute = next(item for item in DATA["items"]
                       if item["id"] == "tribute")
        self.assertFalse(tribute["default"])

    def test_tribute_template_is_readable_black_market_icon_crop(self):
        path = (Path(__file__).parents[2] / "Images" / "Black Market" /
                "Items" / "Tribute.png")
        image = cv2.imread(str(path))

        self.assertIsNotNone(image)
        self.assertEqual((26, 54), image.shape[:2])


if __name__ == "__main__":
    unittest.main()
