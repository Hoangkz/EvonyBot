"""
Flow test Daily Activities / Troop Healing (bot/activities/daily_activities/troop_healing/), phiên bản
giao diện CŨ: màn chính (không có nút Quests góc dưới trái) -> nút "•••" -> bảng chức năng -> Activity
-> lưới thẻ nhiệm vụ -> bấm nhận thẻ "100%" -> thẻ Troop Healing (trái tim) -> popup -> Go. Thẻ đã "Completed" -> xong
hôm nay, không bấm Go.
Luồng mới `after_go` (giống King's Path Heal): Bệnh viện ở giữa -> menu "Heal" -> màn Hospital -> Reset -> chọn 150
lính từ dòng dưới cùng -> Heal -> Speed Up -> Healing Speedup -> Finish All -> xong hôm nay. Bệnh viện đang chữa
dở -> Speed Up -> Finish All trước; không có lính bị thương -> Back, cũng xong hôm nay.

Ảnh chụp nguyên màn hình giả lập 396x704: 11..14 trong screens/ (chép từ tests/daily_activities/screens/); ảnh sau
Go dùng chung, không chép: heal_* ở tests/event/kings_path/screens/, 29 ở tests/daily_activities/screens/.
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities import troop_healing
from bot.activities.daily_activities.common import task_cards
from bot.activities.daily_activities.constants import (
    MAIN_MORE,
    OLD_MENU_ACTIVITY,
    OLD_POPUP_GO,
    TASK_OPENED,
)
from bot.activities.daily_activities.common import open_task_or_finish
from bot.activities.daily_activities.troop_healing.constants import LABEL
from bot.activities.daily_activities.troop_healing.run import after_go
from bot.activities.event.gather_troops.train_troop.constants import CHECKBOX_OFF, CONFIRM, FINISH_ALL, SPEEDUP_SETTINGS
from bot.activities.event.kings_path.heal.constants import (
    HEAL_BUTTON,
    INPUT_OK,
    MENU_HEAL,
    MENU_SPEED_UP,
    RESET,
    SPEED_UP,
)
from tests.daily_activities import KP, OLD_GRID_VARIANTS, TESTS_DIR, old_grid_completed, open_task_of
from tests.flow import Step, back, end, run_flow, tap, tap_at, tap_pct

SCREENS = Path(__file__).parent / "screens"
# Healing Speedup: Speedup Settings -> tích ô -> Confirm -> Finish All.
FINISH_ALL_STEPS = [
    Step(f"{KP}heal_speedup.png", tap(SPEEDUP_SETTINGS)),
    Step(f"{KP}heal_finish_all.png", tap(CHECKBOX_OFF)),
    Step(f"{KP}heal_finish_all_ticked.png", tap(CONFIRM)),
    Step(f"{KP}heal_speedup.png", tap(FINISH_ALL)),
]
# Màn Hospital: Reset -> đã ở cuối danh sách -> ô số dòng cuối -> gõ 150 -> OK -> Heal -> Speed Up -> Finish All.
HEAL_STEPS = [
    Step(f"{KP}heal_screen.png", tap(RESET)),
    Step(f"{KP}heal_screen_reset.png", tap_at(285, 465)),
    Step(f"{KP}heal_input.png", tap(INPUT_OK)),
    Step(f"{KP}heal_screen_reset.png", tap(HEAL_BUTTON)),
    Step(f"{KP}heal_healing.png", tap(SPEED_UP)),
    *FINISH_ALL_STEPS,
]


def _after_go(bot, _settings):
    return after_go(bot)


class TroopHealingFlow(unittest.TestCase):
    def test_open_task_old_ui(self):
        card = task_cards(troop_healing.TASK)[0]
        flow = [
            Step("11_old_main.png", tap(MAIN_MORE)),
            Step("12_old_more_menu.png", tap(OLD_MENU_ACTIVITY)),
            # Thẻ Troop Training "100%": bấm giữa thẻ nhận trước (ảnh tĩnh nên vẫn "100%" -> coi là kẹt, bỏ
            # qua) rồi mới bấm thẻ Troop Healing.
            Step("13_old_activity_grid.png", tap_at(75, 325)),
            Step("13_old_activity_grid.png", tap(card)),
            Step("14_old_troop_healing_popup.png", tap(OLD_POPUP_GO)),
            Step("11_old_main.png", end(result=TASK_OPENED)),
        ]
        run_flow(self, open_task_of(troop_healing.TASK), SCREENS, flow, {})

    def test_open_task_completed_card(self):
        """Giao diện cũ: thẻ Troop Healing "Completed" -> xong hôm nay, không bấm Go."""
        device = run_flow(self, lambda bot, _s: open_task_or_finish(bot, troop_healing.TASK), TESTS_DIR,
                          old_grid_completed("29_old_grid_end_heal_completed.png", "no_heal"), {},
                          variants=OLD_GRID_VARIANTS)
        self.assertIn(LABEL, device.daily_done)

    def test_after_go_heal(self):
        """Bệnh viện rảnh: Heal -> chọn 150 lính dòng cuối -> Heal -> Speed Up -> Finish All -> xong hôm nay."""
        flow = [
            Step(f"{KP}heal_city.png", tap_pct(50, 50)),
            Step(f"{KP}heal_menu.png", tap(MENU_HEAL)),
            *HEAL_STEPS,
            Step(f"{KP}heal_city.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, TESTS_DIR, flow, {})
        self.assertIn("input text 150", device.shells)
        self.assertIn(LABEL, device.daily_done)

    def test_after_go_busy_hospital(self):
        """Bệnh viện đang chữa dở (menu có "Speed Up"): Finish All trước -> mở lại menu -> Heal 150 -> xong."""
        flow = [
            Step(f"{KP}heal_city.png", tap_pct(50, 50)),
            Step(f"{KP}heal_menu_healing.png", tap(MENU_SPEED_UP)),
            *FINISH_ALL_STEPS,
            Step(f"{KP}heal_city.png", tap_pct(50, 50)),
            Step(f"{KP}heal_menu.png", tap(MENU_HEAL)),
            *HEAL_STEPS,
            Step(f"{KP}heal_city.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, TESTS_DIR, flow, {})
        self.assertIn(f"{LABEL}: hospital busy, Speed Up first", device.logs)
        self.assertIn(LABEL, device.daily_done)

    def test_after_go_no_wounded(self):
        """Màn Hospital không có lính bị thương: Back, xong hôm nay."""
        flow = [
            Step(f"{KP}heal_city.png", tap_pct(50, 50)),
            Step(f"{KP}heal_menu.png", tap(MENU_HEAL)),
            Step(f"{KP}heal_empty.png", back()),
            Step(f"{KP}heal_city.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, TESTS_DIR, flow, {})
        self.assertIn(f"{LABEL}: no wounded troops, done for today", device.logs)
        self.assertIn(LABEL, device.daily_done)


if __name__ == "__main__":
    unittest.main()
