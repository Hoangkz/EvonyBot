"""
Flow test Event / King's Path / Refine (bot/activities/event/kings_path/refine/): tách từ test_flow.py.
Ảnh dùng chung ở ../screens/ (không chép sang thư mục nhiệm vụ).
"""
import unittest

import cv2

from bot.activities.event.kings_path import refine
from bot.activities.event.kings_path.refine.constants import MENU_CRAFT, REFINE_BUTTON, TAB_REFINE
from bot.activities.event.kings_path.refine.constants import (
    CANCEL as REFINE_CANCEL,
    EQUIPMENT_REFINE as REFINE_EQUIPMENT_BUTTON)
from bot.activities.event.kings_path.refine.run import _last_done as refine_last_done, blue_items
from tests.flow import Step, back, end, swipe, tap, tap_at, tap_pct
from tests.event.kings_path.common import SCREENS, _run
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)


class RefineFlow(unittest.TestCase):
    def test_refine(self):
        """Refine: Day 4 -> Sharp Weapons (9 / 10) -> Go -> bấm giữa (Lò rèn) -> Craft -> tab Refine
        -> chọn món viền xanh trái nhất (94, 579) -> nút Refine -> màn Refine Equipment (2 ô trống,
        không bỏ tích) -> Refine 10 - 9 = 1 lần -> Cancel -> Back 2 lần -> làm lại từ đầu (harness
        dừng bot)."""
        refine_last_done.clear()
        flow = [
            Step("day4_sharp_weapons.png", tap_at(335, 344)),
            Step("refine_city.png", tap_pct(50, 50)),
            Step("refine_menu.png", tap(MENU_CRAFT)),
            Step("refine_craft.png", tap(TAB_REFINE)),
            Step("refine_items.png", tap_at(94, 579), tap(REFINE_BUTTON)),
            Step("refine_equipment.png", tap(REFINE_EQUIPMENT_BUTTON)),
            Step("refine_equipment_new.png", tap(REFINE_CANCEL)),
            Step("refine_equipment.png", back(), back()),   # đủ 1 lần -> Back 2 lần -> AGAIN
        ]
        device = _run(self, flow, {refine.KEY: {"value": 10, "day": 4}})
        self.assertIn("Refine: refine 1 time(s) (done 9, target 10)", device.logs)
        refine_last_done.clear()

    def test_refine_purple_when_no_blue(self):
        """Thanh trang bị không có món xanh: vuốt thanh sang trái tìm tiếp; thanh không đổi (hết
        thanh) -> món tím trái nhất (145, 578) -> Refine -> Back -> làm lại từ đầu."""
        refine_last_done.clear()
        flow = [
            Step("day4_sharp_weapons.png", tap_at(335, 344)),
            Step("refine_city.png", tap_pct(50, 50)),
            Step("refine_menu.png", tap(MENU_CRAFT)),
            Step("refine_items.png?no_blue", swipe(75, 82, 15, 82), tap_at(145, 578),
                 tap(REFINE_BUTTON)),
            Step("refine_equipment.png", tap(REFINE_EQUIPMENT_BUTTON)),
            Step("refine_equipment_new.png", tap(REFINE_CANCEL)),
            Step("refine_equipment.png", back(), back()),   # đủ 1 lần -> Back 2 lần -> AGAIN
        ]
        device = _run(self, flow, {refine.KEY: {"value": 10, "day": 4}})
        self.assertTrue(any(line.startswith("Refine: purple equipment") for line in device.logs))
        refine_last_done.clear()

    def test_refine_no_items(self):
        """Không có món xanh lẫn tím: vuốt thanh tìm, hết thanh -> bấm loại bên trái (121, 645); ảnh
        tĩnh nên vòng giữa không đổi sau 10 lần kiểm tra -> Back, không lưu done (lượt sau làm lại)."""
        refine_last_done.clear()
        flow = [
            Step("day4_sharp_weapons.png", tap_at(335, 344)),
            Step("refine_city.png", tap_pct(50, 50)),
            Step("refine_menu.png", tap(MENU_CRAFT)),
            Step("refine_items.png?no_items", swipe(75, 82, 15, 82), tap_at(121, 645), back(), end()),
        ]
        device = _run(self, flow, {refine.KEY: {"value": 10, "day": 4}})
        self.assertTrue(any(line.startswith("Refine: equipment type still") for line in device.logs))
        self.assertNotIn(refine.KEY, device.daily_done)

    def test_refine_helmet_no_items(self):
        """Tới mũ (loại cuối bên trái) mà không có món xanh / tím (ảnh thật ở loại mũ, xoá trắng thanh
        trang bị): không bấm sang trái nữa -> lỗi không tìm thấy, Back, xong hôm nay (không complete)."""
        refine_last_done.clear()
        flow = [
            Step("day4_sharp_weapons.png", tap_at(335, 344)),
            Step("refine_city.png", tap_pct(50, 50)),
            Step("refine_menu.png", tap(MENU_CRAFT)),
            Step("refine_helmet_items.png?no_items", swipe(75, 82, 15, 82), back(), end()),
        ]
        device = _run(self, flow, {refine.KEY: {"value": 10, "day": 4}})
        self.assertIn("Refine: helmet: no blue / purple, last type", device.logs)
        self.assertIn("Refine: ERROR no blue / purple equipment found (ring -> helmet), "
                      "done for today, retry tomorrow", device.logs)
        self.assertIn(refine.KEY, device.daily_done)
        self.assertNotIn(refine.KEY + "_complete", device.daily_done)

    def test_refine_target_reached(self):
        """Dòng Go đã 9 / 10, mục tiêu 9: không bấm Go, xong hẳn."""
        flow = [Step("day4_sharp_weapons.png", end())]
        device = _run(self, flow, {refine.KEY: {"value": 9, "day": 4}})
        self.assertIn(refine.KEY, device.daily_done)

    def test_refine_blue_items(self):
        """Món viền xanh nhận theo màu: màn Refine x 94 / 249 (vàng, tím bỏ qua); màn Craft x 42."""
        items = blue_items(cv2.imread(str(SCREENS / "refine_items.png")))
        self.assertEqual([x for x, _ in items], [94, 249])
        items = blue_items(cv2.imread(str(SCREENS / "refine_craft.png")))
        self.assertEqual([x for x, _ in items], [42])


if __name__ == "__main__":
    unittest.main()
