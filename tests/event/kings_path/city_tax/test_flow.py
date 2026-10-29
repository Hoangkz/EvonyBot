"""
Flow test Event / King's Path / City Tax (bot/activities/event/kings_path/city_tax/): tách từ test_flow.py.
Ảnh dùng chung ở ../screens/ (không chép sang thư mục nhiệm vụ).
"""
import unittest
from bot.activities.event.kings_path import city_tax
from bot.activities.event.kings_path.city_tax.constants import POPUP_TAX, TAX_MENU
from bot.activities.event.kings_path.city_tax.run import split_counts
from tests.flow import Step, back, end, tap, tap_at, tap_pct
from tests.event.kings_path.common import KP, _run
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)


class CityTaxFlow(unittest.TestCase):
    def test_city_tax(self):
        """Day 1 City Tax (ảnh thật): dòng Go trên cùng 93 / 110, các dòng Claimed dồn xuống dưới
        -> Go -> bấm giữa thành -> icon Tax -> màn Tax: còn 17 / 4 = 4,25 -> mỗi dòng 5 -> mỗi
        dòng Tax -> popup: bấm "−" 3 lần (ảnh tĩnh: ô số đứng yên = nhỏ nhất) -> "+" 4 lần -> Tax
        -> xong."""
        rows = [284, 383, 482, 581]
        flow = [
            Step("day1_city_tax_go.png", tap_at(335, 344)),
            Step("tax_city.png", tap_pct(50, 50)),
            Step("tax_menu.png", tap(TAX_MENU)),
        ]
        for y in rows:
            flow += [
                Step("tax_screen.png", tap_at(308, y)),
                Step("tax_popup.png", *[tap_at(71, 345) for _ in range(3)],
                     *[tap_at(324, 345) for _ in range(4)], tap(POPUP_TAX)),
            ]
        flow.append(Step("tax_screen.png", end()))
        device = _run(self, flow, {city_tax.KEY: {"value": 110, "day": 1}})
        self.assertIn("City Tax: done 93, target 110, tax [5, 5, 5, 5]", device.logs)
        self.assertFalse([c for c in device.shells if c.startswith("input text")])
        self.assertIn(city_tax.KEY, device.daily_done)

    def test_city_tax_not_enough_gems_stops(self):
        """Dòng 1: chọn xong số lần mà nút Tax XÁM (Cost chữ đỏ, không đủ kim cương) -> Back đóng popup, không bấm Tax,
        dừng cả nhiệm vụ (không thu 3 dòng sau); KHÔNG lưu gì vào DB (lần chạy sau vẫn kiểm tra lại)."""
        flow = [
            Step("day1_city_tax_go.png", tap_at(335, 344)),
            Step("tax_city.png", tap_pct(50, 50)),
            Step("tax_menu.png", tap(TAX_MENU)),
            Step("tax_screen.png", tap_at(308, 284)),
            Step("tax_popup_no_gems.png", *[tap_at(71, 345) for _ in range(3)],
                 *[tap_at(324, 345) for _ in range(4)], back(), end()),
        ]
        device = _run(self, flow, {city_tax.KEY: {"value": 110, "day": 1}})
        self.assertIn("City Tax: out of gems, stop", device.logs)
        self.assertNotIn("City Tax: all rows taxed, done", device.logs)
        self.assertNotIn(city_tax.KEY, device.daily_done)

    def test_city_tax_open_tab(self):
        """Day 1 đang mở tab Hoarding: bấm tab City Tax (ảnh "chưa chọn") -> dòng Go 93 / 110 -> Go."""
        flow = [
            Step("day1_hoarding.png", tap(f"{KP}/Tab/cityTax.png")),
            Step("day1_city_tax_go.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        device = _run(self, flow, {city_tax.KEY: {"value": 110, "day": 1}})
        self.assertIn("City Tax: done 93, target 110", device.logs)

    def test_split_counts(self):
        self.assertEqual(split_counts(110), [28] * 4)
        self.assertEqual(split_counts(90), [23] * 4)   # đã làm 20 / 110
        self.assertEqual(split_counts(3), [1] * 4)
        self.assertEqual(split_counts(0), [0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
