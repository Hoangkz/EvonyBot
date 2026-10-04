"""
Flow test Daily Activities / Troop Healing (bot/activities/daily_activities/troop_healing/), phiên bản
giao diện CŨ: màn chính (không có nút Quests góc dưới trái) -> nút "•••" -> bảng chức năng -> Activity
-> lưới thẻ nhiệm vụ -> bấm nhận thẻ "100%" -> thẻ Troop Healing (trái tim) -> popup -> Go. Phần sau Go (Bệnh viện -> Heal,
giống phiên bản mới): TODO khi có ảnh.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (11..14 chép từ
tests/daily_activities/screens/).
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
from tests.daily_activities import open_task_of
from tests.flow import Step, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"


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


if __name__ == "__main__":
    unittest.main()
