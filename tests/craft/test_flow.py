"""Flow tests cho Craft (bot/activities/craft/): nhận nút theo màu, nhận loại đang mở, đi tới loại, kiểm tra tên trang bị, bấm Quick Compose / Begin,
menu Lò rèn đang chế tạo (Speed Up), nhận trang bị sau khi tăng tốc.

Ảnh thật chụp từ giả lập 21943 ở screens/ (396x704): cat_<loại>.png là màn Craft khi vừa mở loại đó (loại hiện ở vòng giữa đáy màn),
quick_compose.png (Fearless King's Ring, nút xanh lá), begin_gold.png (Fighter's Bow, nút Begin vàng); cat_ring.png có nút Begin xám;
forge_menu_busy.png (menu Lò rèn đang chế tạo), speedup.png (Crafting Speedup), city.png (về thành), city_bubble.png (bóng trang bị trên Lò rèn),
congrats.png ("Congratulations on getting").
Chưa có ảnh chụp màn Lò rèn rảnh -> Craft trong test này (dùng lại flow của Refine) và hộp Finish All / Speedup Settings (tài khoản thử đã đặt sẵn).
"""
import importlib
import unittest
from pathlib import Path

import cv2

craft = importlib.import_module("bot.activities.craft.run")     # `bot.activities.craft.run` là hàm run (package re-export), cần module
from bot.activities.craft.constants import (
    BEGIN, BUTTON_POS, COLLECT_POS, CONFIRM, DISABLED, LEFT_TYPE_POS, MENU_SPEED_UP, QUICK_COMPOSE, RIGHT_TYPE_POS, SPEEDUP_TITLE,
)
from tests.flow import Step, end, run_flow, swipe, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
RING_KING = "ring/03_Fearless_King's_Ring"
BOW_FIGHTER = "bow/01_Fighter's_Bow"


def screen(name: str):
    return cv2.imread(str(SCREENS / name))


def score(template: str, image: str) -> float:
    from bot.context import TEMPLATE_DIR
    result = cv2.matchTemplate(screen(image), cv2.imread(str(TEMPLATE_DIR / template)), cv2.TM_CCOEFF_NORMED)
    return float(result.max())


class ButtonState(unittest.TestCase):
    def test_colours(self):
        self.assertEqual(craft.button_state(screen("quick_compose.png")), QUICK_COMPOSE)
        self.assertEqual(craft.button_state(screen("begin_gold.png")), BEGIN)
        self.assertEqual(craft.button_state(screen("cat_ring.png")), DISABLED)   # Begin xám (thiếu nguyên liệu)


class Templates(unittest.TestCase):
    def test_speed_up_menu_icon_only_on_busy_forge(self):
        self.assertGreater(score(MENU_SPEED_UP, "forge_menu_busy.png"), 0.95)
        for other in ("city.png", "speedup.png", "congrats.png", "cat_ring.png"):
            self.assertLess(score(MENU_SPEED_UP, other), 0.6, other)

    def test_speedup_title_and_congrats(self):
        self.assertGreater(score(SPEEDUP_TITLE, "speedup.png"), 0.95)
        self.assertLess(score(SPEEDUP_TITLE, "city.png"), 0.6)
        self.assertGreater(score(CONFIRM, "congrats.png"), 0.95)
        self.assertLess(score(CONFIRM, "city.png"), 0.6)


def check_image(testcase, image: str, fn):
    """Chạy `fn(bot)` trên một ảnh (không có thao tác nào)."""
    run_flow(testcase, lambda bot, settings: fn(bot), SCREENS, [Step(image, end())], {})


class Helpers(unittest.TestCase):
    def check(self, image: str, fn):
        check_image(self, image, fn)

    def test_active_category(self):
        for kind in ("helmet", "armor", "legs", "boots", "ring", "bow"):
            def fn(bot, kind=kind):
                self.assertEqual(craft.active_category(bot, bot.screenshot()), kind)
            self.check(f"cat_{kind}.png", fn)

    def test_title_matches_only_the_selected_item(self):
        def fn(bot):
            self.assertTrue(craft.title_matches(bot, RING_KING))
            self.assertFalse(craft.title_matches(bot, "ring/01_Fighter's_Ring"))
            self.assertFalse(craft.title_matches(bot, BOW_FIGHTER))
        self.check("quick_compose.png", fn)

    def test_title_of_bow(self):
        self.check("begin_gold.png", lambda bot: self.assertTrue(craft.title_matches(bot, BOW_FIGHTER)))

    def test_icon_found_on_the_row(self):
        """Hàng trang bị của quick_compose.png đang cuộn: món đầu hàng là Courageous Dragon Ring (x ~ 40), Fearless King's Ring không có trên hàng."""
        def fn(bot):
            screen_now = bot.screenshot()
            found = craft.candidates(bot, screen_now, "ring/06_Courageous_Dragon_Ring")
            self.assertEqual(len(found), 1)
            self.assertLess(found[0][0], 60)
            self.assertEqual(craft.candidates(bot, screen_now, RING_KING), [])
        self.check("quick_compose.png", fn)

    def test_icon_found_even_when_saved_crop_is_a_little_off(self):
        """Consul's / Hospital Officer's / Academy Officer's Ring: icon lưu cắt lệch vài px nên khớp chỉ ~0,77 .. 0,81, vẫn phải thấy."""
        def fn(bot):
            for item in ("ring/09_Consul's_Ring", "ring/10_Hospital_Officer's_Ring", "ring/11_Academy_Officer's_Ring"):
                self.assertEqual(len(craft.candidates(bot, bot.screenshot(), item)), 1, item)
        self.check("quick_compose.png", fn)


class Locks(unittest.TestCase):
    """locked_row.png: hàng Nhẫn của 21913 có 2 ô khoá (tâm x ~ 291, 343); General's .. Courageous Dragon Ring (x 30 .. 238) đã mở."""

    def test_first_lock_x(self):
        def fn(bot):
            x = craft.first_lock_x(bot, bot.screenshot())
            self.assertIsNotNone(x)
            self.assertAlmostEqual(x, 291, delta=8)
        check_image(self, "locked_row.png", fn)

    def test_no_lock_on_an_unlocked_row(self):
        check_image(self, "quick_compose.png", lambda bot: self.assertIsNone(craft.first_lock_x(bot, bot.screenshot())))

    def test_items_not_found_before_the_lock_are_skipped_without_scrolling_on(self):
        """Thấy ô khoá mà trang bị cần làm chưa thấy -> các ô từ khoá tới hết danh sách chưa mở: bỏ qua hết, không vuốt tiếp."""
        wanted = {"ring/07_Courageous_Achaemenidae_Ring": 1}
        flow = [Step("locked_row.png", swipe()), Step("locked_row.png", end(None))]
        device = run_flow(self, lambda bot, settings: craft.craft_category(bot, "ring", wanted), SCREENS, flow, {})
        self.assertEqual(wanted, {})
        self.assertIn("Craft: ring/07_Courageous_Achaemenidae_Ring: behind a locked item, skip", device.logs)


class Flow(unittest.TestCase):
    def test_goto_category_taps_left_circle_to_a_lower_type(self):
        """Đang ở Nhẫn, cần Giày (bên trái trong vòng chọn): bấm vòng bên trái một lần."""
        flow = [Step("cat_ring.png", tap_at(*LEFT_TYPE_POS)), Step("cat_boots.png", end(True))]
        run_flow(self, lambda bot, settings: craft.goto_category(bot, "boots"), SCREENS, flow, {})

    def test_goto_category_taps_right_circle_to_a_higher_type(self):
        flow = [Step("cat_ring.png", tap_at(*RIGHT_TYPE_POS)), Step("cat_bow.png", end(True))]
        run_flow(self, lambda bot, settings: craft.goto_category(bot, "bow"), SCREENS, flow, {})

    def test_goto_category_already_there_does_not_tap(self):
        run_flow(self, lambda bot, settings: craft.goto_category(bot, "ring"), SCREENS, [Step("cat_ring.png", end(True))], {})

    def test_begin_is_tapped_and_craft_screen_closes(self):
        """Nút Begin vàng -> bấm một lần; game về thành (không còn tiêu đề Craft) = đã bắt đầu chế tạo."""
        flow = [Step("begin_gold.png", tap_at(*BUTTON_POS)), Step("city.png", end(True))]
        device = run_flow(self, lambda bot, settings: craft.start_craft(bot, BOW_FIGHTER), SCREENS, flow, {})
        self.assertIn("Craft: bow/01_Fighter's_Bow: Begin", device.logs)

    def test_quick_compose_is_tapped_and_item_skipped_when_it_stays_unavailable(self):
        """Nút xanh lá (Quick Compose) -> bấm; nút không đổi thành Begin -> bỏ qua trang bị, không bấm Begin."""
        flow = [Step("quick_compose.png", tap_at(*BUTTON_POS)), Step("quick_compose.png", end(False))]
        device = run_flow(self, lambda bot, settings: craft.start_craft(bot, RING_KING), SCREENS, flow, {})
        self.assertIn("Craft: ring/03_Fearless_King's_Ring: Quick Compose", device.logs)

    def test_disabled_begin_is_skipped_without_tapping(self):
        device = run_flow(self, lambda bot, settings: craft.start_craft(bot, "ring/01_Fighter's_Ring"), SCREENS,
                          [Step("cat_ring.png", end(False))], {})
        self.assertIn("Craft: ring/01_Fighter's_Ring: Begin disabled, skip", device.logs)

    def test_collect_taps_the_bubble_then_confirm(self):
        """Sau Finish All: bấm bóng trang bị trên Lò rèn -> hộp "Congratulations on getting" -> Confirm."""
        flow = [Step("city_bubble.png", tap_at(*COLLECT_POS)), Step("congrats.png", tap(CONFIRM)), Step("city.png", end(True))]
        run_flow(self, lambda bot, settings: craft.collect(bot), SCREENS, flow, {})

    def test_finish_all_on_crafting_speedup_screen(self):
        """Màn Crafting Speedup: lần đầu bấm Speedup Settings (hộp Finish All do tài khoản đã đặt sẵn nên ảnh thử không có)."""
        from bot.activities.event.gather_troops.train_troop.constants import SPEEDUP_SETTINGS
        flow = [Step("speedup.png", tap(SPEEDUP_SETTINGS)), Step("city.png", end())]
        run_flow(self, lambda bot, settings: craft.finish_all(bot), SCREENS, flow, {})


if __name__ == "__main__":
    unittest.main()
