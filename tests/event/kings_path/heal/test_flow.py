"""
Flow test Event / King's Path / Heal (bot/activities/event/kings_path/heal/): tách từ test_flow.py.
Ảnh dùng chung ở ../screens/ (không chép sang thư mục nhiệm vụ).
"""
import unittest
from bot.activities.event.kings_path import heal
from bot.activities.event.kings_path.heal.constants import (
    MENU_HEAL as HEAL_MENU_HEAL,
    MENU_SPEED_UP as HEAL_MENU_SPEED_UP,
    RESET as HEAL_RESET,
    HEAL_BUTTON)
from bot.activities.event.kings_path.heal.constants import INPUT_OK as HEAL_INPUT_OK, SPEED_UP as HEAL_SPEED_UP
from bot.activities.event.gather_troops.train_troop.constants import (
    CHECKBOX_OFF as TRAIN_CHECKBOX_OFF,
    CONFIRM as TRAIN_CONFIRM,
    FINISH_ALL as TRAIN_FINISH_ALL,
    SPEEDUP_SETTINGS as TRAIN_SPEEDUP_SETTINGS)
from tests.flow import Step, back, end, tap, tap_at, tap_pct
from tests.event.kings_path.common import _run
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)


class HealFlow(unittest.TestCase):
    def test_heal_idle_hospital(self):
        """Heal: Go -> bấm giữa (Bệnh viện) -> menu có "Heal" -> màn Hospital (chọn hết) -> Reset ->
        đã ở cuối danh sách (không cuộn) -> ô số dòng cuối (285, 465) -> thanh nhập: gõ 50000 - 0 -> OK -> Heal
        -> Speed Up -> Healing Speedup: Speedup Settings -> tích ô -> Confirm -> Finish All -> làm lại
        từ đầu (harness dừng bot)."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu.png", tap(HEAL_MENU_HEAL)),
            Step("heal_screen.png", tap(HEAL_RESET)),
            # Đã ở cuối danh sách (khoảng trống trên khung tài nguyên): không cuộn.
            Step("heal_screen_reset.png", tap_at(285, 465)),
            Step("heal_input.png", tap(HEAL_INPUT_OK)),
            # Nút Heal phải SÁNG (cam, heal_screen.png) mới bấm; xám (heal_screen_reset.png) thì làm lại.
            Step("heal_screen.png", tap(HEAL_BUTTON)),
            Step("heal_healing.png", tap(HEAL_SPEED_UP)),
            Step("heal_speedup.png", tap(TRAIN_SPEEDUP_SETTINGS)),
            Step("heal_finish_all.png", tap(TRAIN_CHECKBOX_OFF)),
            Step("heal_finish_all_ticked.png", tap(TRAIN_CONFIRM)),
            Step("heal_speedup.png", tap(TRAIN_FINISH_ALL)),   # -> AGAIN; harness dừng bot
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: hospital idle, Heal (done 0, target 50000)", device.logs)
        self.assertIn("input text 50000", device.shells)

    def test_heal_button_not_lit_redo_from_hospital(self):
        """Nút Heal còn xám (không chọn được lính) -> không bấm, làm lại từ màn Hospital (ở sẵn màn, ô số dòng
        cuối) -> lần 2 nút sáng -> bấm Heal."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu.png", tap(HEAL_MENU_HEAL)),
            Step("heal_screen.png", tap(HEAL_RESET)),
            Step("heal_screen_reset.png", tap_at(285, 465)),
            Step("heal_input.png", tap(HEAL_INPUT_OK)),
            Step("heal_screen_reset.png", tap_at(285, 465)),   # nút Heal xám: làm lại bước chọn lính
            Step("heal_input.png", tap(HEAL_INPUT_OK)),
            Step("heal_screen.png", tap(HEAL_BUTTON)),
            Step("heal_healing.png", tap(HEAL_SPEED_UP)),
            Step("heal_speedup.png", tap(TRAIN_SPEEDUP_SETTINGS)),
            Step("heal_finish_all.png", tap(TRAIN_CHECKBOX_OFF)),
            Step("heal_finish_all_ticked.png", tap(TRAIN_CONFIRM)),
            Step("heal_speedup.png", tap(TRAIN_FINISH_ALL)),
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertTrue(any("Heal button not lit" in log for log in device.logs))

    def test_heal_already_started_goes_to_speed_up(self):
        """Sau khi nhập số đã thấy hộp "Healing ... Speed Up" (lần bấm OK trúng nút Heal): coi như đã bắt đầu hồi, đi
        tiếp tới Speed Up, không báo thiếu nút Heal."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu.png", tap(HEAL_MENU_HEAL)),
            Step("heal_screen.png", tap(HEAL_RESET)),
            Step("heal_screen_reset.png", tap_at(285, 465)),
            Step("heal_input.png", tap(HEAL_INPUT_OK)),
            Step("heal_healing.png", tap(HEAL_SPEED_UP)),
            Step("heal_speedup.png", tap(TRAIN_SPEEDUP_SETTINGS)),
            Step("heal_finish_all.png", tap(TRAIN_CHECKBOX_OFF)),
            Step("heal_finish_all_ticked.png", tap(TRAIN_CONFIRM)),
            Step("heal_speedup.png", tap(TRAIN_FINISH_ALL)),
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertTrue(any("heal already started" in log for log in device.logs))

    def test_heal_no_wounded(self):
        """Hospital không còn lính bị thương ("Wounded Troops 0/0", không có dòng lính): Back, xong
        hôm nay."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu.png", tap(HEAL_MENU_HEAL)),
            Step("heal_empty.png", back(), end()),
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: no wounded troops, done for today", device.logs)
        self.assertIn(heal.KEY, device.daily_done)

    def test_heal_menu_without_heal(self):
        """Menu Bệnh viện chỉ có Citizen / Detail / Upgrade (không có lính bị thương): Back, xong hôm
        nay."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu_empty.png", back(), end()),
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: no wounded troops, done for today", device.logs)
        self.assertIn(heal.KEY, device.daily_done)

    def test_heal_busy_hospital_speed_up(self):
        """Heal: bệnh viện đang chữa dở -> menu có "Speed Up" -> Healing Speedup -> Finish All (như
        train lính) -> làm lại từ đầu (harness dừng bot)."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu_healing.png", tap(HEAL_MENU_SPEED_UP)),
            Step("heal_speedup.png", tap(TRAIN_SPEEDUP_SETTINGS)),
            Step("heal_finish_all.png", tap(TRAIN_CHECKBOX_OFF)),
            Step("heal_finish_all_ticked.png", tap(TRAIN_CONFIRM)),
            Step("heal_speedup.png", tap(TRAIN_FINISH_ALL)),   # -> AGAIN; harness dừng bot
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: hospital busy, Speed Up", device.logs)


if __name__ == "__main__":
    unittest.main()
