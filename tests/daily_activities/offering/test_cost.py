"""
OCR ô "Cost" của popup Offer Gems (bot/ocr/read_offer_cost.py) và bảng giá theo lượt
(offering/run.py offer_total): mỗi ảnh screens/14_offer_gems_popup_<số lượng>.png (hôm nay chưa offer)
phải đọc ra đúng tổng kim cương của <số lượng> lượt đầu.
"""
import re
import unittest
from pathlib import Path

import cv2

from bot.activities.daily_activities.offering.run import offer_total
from bot.ocr import read_offer_cost
from bot.ocr.read_offer_cost import CROP

SCREENS = Path(__file__).parent / "screens"
# Cost thấy trên ảnh (đọc bằng mắt) theo số lượng.
COSTS = {1: 25, 6: 675, 7: 1075, 8: 1475, 9: 2075, 10: 2675, 11: 3675, 20: 15175,
         30: 30175, 42: 48175, 43: 49675, 94: 126175}


def _quantity(path: Path) -> int:
    match = re.search(r"_(\d+)\.png$", path.name)
    return int(match.group(1)) if match else 1   # 08_offer_gems_popup.png: số lượng 1


class OfferCostTests(unittest.TestCase):
    def test_ocr_reads_every_popup(self):
        files = sorted(SCREENS.glob("*offer_gems_popup*.png"))
        self.assertGreaterEqual(len(files), 12)
        x, y, w, h = CROP
        for path in files:
            with self.subTest(screen=path.name):
                quantity = _quantity(path)
                self.assertEqual(read_offer_cost(cv2.imread(str(path))[y:y + h, x:x + w]),
                                 COSTS[quantity])

    def test_ocr_reads_touching_one(self):
        # Hôm nay đã offer 1 lượt, số lượng 2: "150" — chân đế chữ "1" dính liền "5", "0" thành một khối.
        x, y, w, h = CROP
        screen = cv2.imread(str(SCREENS / "16_offer_cost_150.png"))
        self.assertEqual(read_offer_cost(screen[y:y + h, x:x + w]), 150)
        self.assertEqual(offer_total(1, 2), 150)

    def test_price_formula_matches_seen_costs(self):
        for quantity, cost in COSTS.items():
            with self.subTest(quantity=quantity):
                self.assertEqual(offer_total(0, quantity), cost)


if __name__ == "__main__":
    unittest.main()
