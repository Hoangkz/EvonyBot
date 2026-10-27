import unittest
from importlib import import_module
from pathlib import Path
from unittest import mock

from bot.activities import refine_equipment
from bot.activities.refine_equipment.constants import (
    ALL_TAB_X,
    CANCEL,
    CONFIRM,
    CRAFT_REFINE,
    WARN_CONFIRM,
    ENHANCE,
    EQUIPMENT_REFINE,
    FEATURES_ICON,
    FIRST_GENERAL,
    MENU_GENERALS,
    REFINE_BUTTON,
    SLOTS,
    TYPE_TAB_Y,
    VIEW,
)
from tests.flow import Step, back, end, run_flow, tap, tap_at, tap_pct

SCREENS = Path(__file__).parent / "screens"
WEAPON = SLOTS[0][2]

# Chụp trên máy 21913 (396x704): màn thành -> ••• -> Generals -> tướng đầu -> ô vũ khí -> View -> Refine -> Refine -> màn Refine Equipment.
# Chưa đọc được dòng New (READY = False) nên bot chỉ Back về thành, không bấm Refine.
FLOW = [
    Step("01_home.png", tap(FEATURES_ICON)),
    Step("02_menu.png", tap(MENU_GENERALS)),
    Step("03_generals.png", tap_pct(ALL_TAB_X, TYPE_TAB_Y), tap_pct(*FIRST_GENERAL)),
    Step("04_general.png", tap_pct(*WEAPON)),
    Step("05_popup.png", tap(VIEW, 0.85)),
    Step("06_equipment.png", tap(EQUIPMENT_REFINE)),
    Step("07_craft.png", tap(CRAFT_REFINE)),
    Step("08_refine_equipment.png", back()),                    # màn Refine Equipment (vòng Refine tách ra test riêng) -> Back
    Step("07_craft.png", back()),
    Step("06_equipment.png", back()),
    Step("04_general.png", back(4)),
    Step("01_home.png", end()),
]
SETTINGS = {"slots": {"weapon": {"lines": [{"attribute": "Ground Troop Attack", "color": "gold", "lock": True}]}}}


class RefineEquipmentFlow(unittest.TestCase):
    def test_main_flow(self):
        """Điều hướng tới màn Refine Equipment rồi Back về thành; vòng Refine tách ra test riêng nên ở đây bỏ qua."""
        with mock.patch.object(import_module("bot.activities.refine_equipment.run"), "_refine_until"):
            run_flow(self, refine_equipment.run, SCREENS, FLOW, SETTINGS)

    def test_refine_loop_cancel_then_confirm(self):
        """Nhẫn (21913), cần 1 dòng Siege Machine Load màu cam trở lên: Refine -> kết quả không đạt (ảnh 13) -> Cancel -> Refine -> kết quả đạt (ảnh 14) -> Confirm."""
        module = import_module("bot.activities.refine_equipment.run")
        ring_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "ring")
        settings = {"slots": {"ring": {"lines": [{"attribute": "Siege Machine Load", "color": "orange"}], "max_refines": 100, "stop": {"gold": 0, "orange": 1}}}}

        def refine_ring(bot, settings):
            module._refine_until(bot, "Ring", module.goals(settings)["ring"], ring_catalog)

        flow = [
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("13_result_no_match.png", tap(CANCEL)),
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("14_result_match.png", tap(CONFIRM, 0.9)),
            Step("12_ring_refine.png", end()),
        ]
        run_flow(self, refine_ring, SCREENS, flow, settings)

    def test_empty_slot_is_skipped(self):
        """Tướng chưa mặc đồ nào (ảnh 10): ô trống không bị bấm, bot chỉ Back về thành."""
        flow = [
            Step("01_home.png", tap(FEATURES_ICON)),
            Step("02_menu.png", tap(MENU_GENERALS)),
            Step("03_generals.png", tap_pct(ALL_TAB_X, TYPE_TAB_Y), tap_pct(*FIRST_GENERAL)),
            Step("10_general_empty.png", back(4)),
            Step("01_home.png", end()),
        ]
        run_flow(self, refine_equipment.run, SCREENS, flow, SETTINGS)

    def test_refine_warning_popup_then_result(self):
        """Refine mà còn dòng cao cấp chưa khoá: hiện hộp cảnh báo (ảnh 15) -> bot tích ô "Don't show this again for today" (158, 385) rồi Confirm -> sang màn kết quả
        (ảnh 13, có Cancel / Confirm) -> Cancel -> Refine -> kết quả đạt (ảnh 14) -> Confirm."""
        module = import_module("bot.activities.refine_equipment.run")
        ring_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "ring")
        settings = {"slots": {"ring": {"lines": [{"attribute": "Siege Machine Load", "color": "orange"}], "max_refines": 100, "stop": {"gold": 0, "orange": 1}}}}

        def refine_ring(bot, settings):
            module._refine_until(bot, "Ring", module.goals(settings)["ring"], ring_catalog)

        flow = [
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("15_warning_popup.png", tap_at(158, 385), tap(WARN_CONFIRM)),
            Step("13_result_no_match.png", tap(CANCEL)),
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("14_result_match.png", tap(CONFIRM, 0.9)),
            Step("12_ring_refine.png", end()),
        ]
        run_flow(self, refine_ring, SCREENS, flow, settings)

    def test_first_refine_of_unrefined_equipment(self):
        """Trang bị chưa tinh luyện (ảnh 16, chưa có khung Original, những khoảng đen lớn): Refine lần đầu áp thẳng dòng vào Original (ảnh 12) và KHÔNG có Confirm, bot thấy khung
        Original hiện ra thì Refine tiếp luôn (không chờ 10 s); lần sau ra kết quả đạt (ảnh 14) -> Confirm."""
        module = import_module("bot.activities.refine_equipment.run")
        ring_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "ring")
        settings = {"slots": {"ring": {"lines": [{"attribute": "Siege Machine Load", "color": "orange"}], "max_refines": 100, "stop": {"gold": 0, "orange": 1}}}}

        def refine_ring(bot, settings):
            opened, closed = module._lock_counts(bot)            # ảnh 16: không có ổ khoá nào -> chưa tinh luyện
            self.assertEqual((opened, closed), (0, 0))
            module._refine_until(bot, "Ring", module.goals(settings)["ring"], ring_catalog, unrefined=True)

        flow = [
            Step("16_unrefined.png", tap(REFINE_BUTTON)),
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("14_result_match.png", tap(CONFIRM, 0.9)),
            Step("12_ring_refine.png", end()),
        ]
        run_flow(self, refine_ring, SCREENS, flow, settings)

    def test_all_four_locked_is_detected(self):
        """Ảnh 17 (giày, cả 4 dòng đã khoá, nút Refine xám): không có ổ khoá mở, đếm được 4 ổ khoá đóng -> `_refine_slot` bỏ qua trang bị. Ảnh 12 (4 chưa khoá) và 16
        (chưa tinh luyện) thì không bỏ qua."""
        module = import_module("bot.activities.refine_equipment.run")
        seen = {}

        def count_locks(bot, settings):
            seen["counts"] = module._lock_counts(bot)

        for image, expected in (("17_all_locked.png", (0, 4)), ("12_ring_refine.png", (4, 0)), ("16_unrefined.png", (0, 0))):
            run_flow(self, count_locks, SCREENS, [Step(image, end())], {})
            self.assertEqual(seen["counts"], expected, image)

    def test_all_locked_in_the_loop_skips_without_refining(self):
        """Cả 4 dòng đã khoá (ảnh 17, nút Refine xám): `_refine_until` bỏ qua trang bị, không bấm gì (flow chỉ có end(): bấm bất kỳ thứ gì sẽ làm test hỏng)."""
        module = import_module("bot.activities.refine_equipment.run")
        boots_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "boots")
        settings = {"slots": {"boots": {"lines": [{"attribute": "March Speed", "color": "gold"}], "max_refines": 100, "stop": {"gold": 1, "orange": 0}}}}

        def refine_boots(bot, settings):
            module._refine_until(bot, "Boots", module.goals(settings)["boots"], boots_catalog)

        run_flow(self, refine_boots, SCREENS, [Step("17_all_locked.png", end())], settings)

    def test_cancel_with_higher_new_line_shows_keep_old_popup(self):
        """Bấm Cancel ở kết quả mà dòng mới cao hơn dòng cũ: game hỏi "The new attribute is higher than the old one. Are you sure you want to maintain it?" (ảnh 24, ô "Don't
        show this again" ở (158, 355), Confirm ở (278, 411)). Bot tích ô rồi Confirm (giữ dòng cũ), sau đó thấy nút Refine (ảnh 12) và Refine tiếp -> kết quả đạt (ảnh 14) -> Confirm."""
        module = import_module("bot.activities.refine_equipment.run")
        ring_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "ring")
        settings = {"slots": {"ring": {"lines": [{"attribute": "Siege Machine Load", "color": "orange"}], "max_refines": 100, "stop": {"gold": 0, "orange": 1}}}}

        def refine_ring(bot, settings):
            module._refine_until(bot, "Ring", module.goals(settings)["ring"], ring_catalog)

        flow = [
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("13_result_no_match.png", tap(CANCEL)),
            Step("24_keep_old_popup.png", tap_at(158, 355), tap(WARN_CONFIRM)),
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("14_result_match.png", tap(CONFIRM, 0.9)),
            Step("12_ring_refine.png", end()),
        ]
        run_flow(self, refine_ring, SCREENS, flow, settings)

    def test_confirm_new_wanted_line_then_lock_it(self):
        """Vũ khí (21913, ảnh thật ghi từ lượt chạy), mức dừng 4 Gold, các thuộc tính bật Lock: Refine (ảnh 25) -> kết quả New có thêm 1 dòng vàng cần khoá (ảnh 26) nhưng chưa đủ 4 Gold
        -> bot Confirm giữ kết quả (287, 669) -> khung Original (ảnh 27) -> bấm ổ khoá dòng vàng (32, 401) -> đã khoá (ảnh 28). Giới hạn 1 lần Refine nên vòng kết thúc ngay sau đó."""
        module = import_module("bot.activities.refine_equipment.run")
        weapon_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "weapon")
        lines = [{"attribute": name, "color": "gold", "kind": "all", "lock": True} for name in weapon_catalog]
        settings = {"slots": {"weapon": {"lines": lines, "max_refines": 100, "stop": {"gold": 4, "orange": 0}}}}

        def refine_weapon(bot, settings):
            goal = module.goals(settings)["weapon"]
            goal["max_refines"] = 1
            module._refine_until(bot, "Weapon", goal, weapon_catalog)

        flow = [
            Step("25_lockloop_1_refine_screen.png", tap_at(198, 668)),
            Step("26_lockloop_2_result_new_gold.png", tap_at(287, 669)),
            Step("27_lockloop_3_after_confirm.png", tap_at(32, 401)),
            Step("28_lockloop_4_locked.png", end()),
        ]
        run_flow(self, refine_weapon, SCREENS, flow, settings)

    def test_unknown_popup_is_closed_with_back(self):
        """Hộp thoại lạ chặn màn sau Cancel (ở đây dùng ảnh 13 đứng yên làm màn lạ: không có nút Refine, hình không đổi): bot kiểm tra 2 lần rồi bấm Back MỘT lần, thấy lại nút
        Refine (ảnh 12) và Refine tiếp -> kết quả đạt (ảnh 14) -> Confirm."""
        module = import_module("bot.activities.refine_equipment.run")
        ring_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "ring")
        settings = {"slots": {"ring": {"lines": [{"attribute": "Siege Machine Load", "color": "orange"}], "max_refines": 100, "stop": {"gold": 0, "orange": 1}}}}

        def refine_ring(bot, settings):
            module._refine_until(bot, "Ring", module.goals(settings)["ring"], ring_catalog)

        flow = [
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("13_result_no_match.png", tap(CANCEL)),
            Step("13_result_no_match.png", back()),
            Step("12_ring_refine.png", tap(REFINE_BUTTON)),
            Step("14_result_match.png", tap(CONFIRM, 0.9)),
            Step("12_ring_refine.png", end()),
        ]
        run_flow(self, refine_ring, SCREENS, flow, settings)

    def test_pending_result_is_handled_when_coming_back(self):
        """Quay lại trang bị mà kết quả New cũ còn treo (ảnh 31: Cancel / Confirm hiện sẵn, không có nút Refine, ảnh thật từ vũ khí): bot không coi là chưa tinh luyện, đọc kết quả đó
        và xử lý như vừa ra: chưa đủ 3 Orange -> Cancel."""
        module = import_module("bot.activities.refine_equipment.run")
        weapon_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "weapon")
        lines = [{"attribute": name, "color": "orange", "kind": "all", "lock": False} for name in weapon_catalog]
        settings = {"slots": {"weapon": {"lines": lines, "max_refines": 100, "stop": {"gold": 0, "orange": 3}}}}

        def refine_weapon(bot, settings):
            goal = module.goals(settings)["weapon"]
            goal["max_refines"] = 0              # chỉ xử lý kết quả treo, không Refine thêm
            module._refine_until(bot, "Weapon", goal, weapon_catalog)

        flow = [Step("31_pending_result.png", tap(CANCEL)), Step("25_lockloop_1_refine_screen.png", end())]
        run_flow(self, refine_weapon, SCREENS, flow, settings)

    def test_empty_general_list_stops(self):
        """Lọc tim yêu thích mà không có tướng nào (chữ "No favorite General", ảnh 11): bot không bấm tướng, Back về thành rồi dừng."""
        flow = [
            Step("01_home.png", tap(FEATURES_ICON)),
            Step("02_menu.png", tap(MENU_GENERALS)),
            Step("11_list_no_favorite.png", tap_pct(ALL_TAB_X, TYPE_TAB_Y), tap_pct(89.6, TYPE_TAB_Y)),
            Step("11_list_no_favorite.png", back()),
            Step("01_home.png", end()),
        ]
        settings = {**SETTINGS, "favorite": True, "general_type": "sub"}
        run_flow(self, refine_equipment.run, SCREENS, flow, settings)

    def test_empty_general_type_without_heart_stops(self):
        """Chưa tích tim mà loại tướng (Duty) không có ai: game hiện "No General!" (ảnh 30), khác chữ "No favorite General": bot cũng không bấm tướng, Back về thành rồi dừng."""
        flow = [
            Step("01_home.png", tap(FEATURES_ICON)),
            Step("02_menu.png", tap(MENU_GENERALS)),
            Step("30_list_no_general.png", tap_pct(ALL_TAB_X, TYPE_TAB_Y), tap_pct(73.7, TYPE_TAB_Y)),
            Step("30_list_no_general.png", back()),
            Step("01_home.png", end()),
        ]
        settings = {**SETTINGS, "favorite": False, "general_type": "duty"}
        run_flow(self, refine_equipment.run, SCREENS, flow, settings)

    def test_not_at_the_city_goes_back_first(self):
        """Máy đang ở màn Refine (ảnh 12) chứ không phải thành: bot Back (tối đa CITY_BACKS lần) tới khi thấy nút ••• (ảnh 01) rồi mới đi tiếp; ở đây thành sạch nên dừng lại
        vì không có gì để làm trước khi vào menu: bước tiếp theo là bấm •••."""
        flow = [
            Step("12_ring_refine.png", back()),
            Step("01_home.png", tap(FEATURES_ICON)),
            Step("02_menu.png", tap(MENU_GENERALS)),
            Step("30_list_no_general.png", tap_pct(ALL_TAB_X, TYPE_TAB_Y)),
            Step("30_list_no_general.png", back()),
            Step("01_home.png", end()),
        ]
        run_flow(self, refine_equipment.run, SCREENS, flow, {**SETTINGS, "favorite": False, "general_type": "all"})

    def test_cannot_reach_the_city_does_not_refine(self):
        """Back mấy lần mà vẫn không thấy nút ••• (ảnh 12 mãi): bot Back tối đa 6 lần rồi dừng, không đi tiếp và không bấm gì ngoài Back."""
        flow = [Step("12_ring_refine.png", back(6), end())]
        run_flow(self, refine_equipment.run, SCREENS, flow, SETTINGS)

    def test_unknown_gold_line_stops_this_equipment(self):
        """Kết quả New có một dòng VÀNG không nhận ra tên: bot dừng trang bị này (không bấm Cancel / Confirm, flow chỉ có bước Refine rồi end())."""
        module = import_module("bot.activities.refine_equipment.run")
        ring_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "ring")
        settings = {"slots": {"ring": {"lines": [{"attribute": "Siege Machine Load", "color": "orange"}], "max_refines": 100, "stop": {"gold": 0, "orange": 1}}}}
        rows = [{"name": "Ground Troop Load", "color": "normal", "kind": "percent", "locked": None, "y": 0, "score": 0.9},
                {"name": None, "color": "gold", "kind": "percent", "locked": None, "y": 0, "score": 0.4}] * 2

        def refine_ring(bot, settings):
            module._refine_until(bot, "Ring", module.goals(settings)["ring"], ring_catalog)

        flow = [Step("12_ring_refine.png", tap(REFINE_BUTTON)), Step("13_result_no_match.png", end())]
        with mock.patch.object(module, "read_new", return_value=rows):
            run_flow(self, refine_ring, SCREENS, flow, settings)

    def test_unknown_name_of_another_colour_still_cancels(self):
        """Dòng không nhận ra tên mà màu KHÁC vàng (ở đây tím): vẫn Cancel rồi tinh luyện bình thường (giới hạn 1 lần Refine nên kết thúc sau Cancel)."""
        module = import_module("bot.activities.refine_equipment.run")
        ring_catalog = next(catalog for slot_id, _label, _pos, catalog in SLOTS if slot_id == "ring")
        settings = {"slots": {"ring": {"lines": [{"attribute": "Siege Machine Load", "color": "orange"}], "max_refines": 100, "stop": {"gold": 0, "orange": 1}}}}
        rows = [{"name": None, "color": "purple", "kind": "percent", "locked": None, "y": 0, "score": 0.4}] * 4

        def refine_ring(bot, settings):
            goal = module.goals(settings)["ring"]
            goal["max_refines"] = 1
            module._refine_until(bot, "Ring", goal, ring_catalog)

        flow = [Step("12_ring_refine.png", tap(REFINE_BUTTON)), Step("13_result_no_match.png", tap(CANCEL)), Step("12_ring_refine.png", end())]
        with mock.patch.object(module, "read_new", return_value=rows):
            run_flow(self, refine_ring, SCREENS, flow, settings)

    def test_no_attribute_does_nothing(self):
        run_flow(self, refine_equipment.run, SCREENS, [Step("01_home.png", end())], {"slots": {}})


if __name__ == "__main__":
    unittest.main()
