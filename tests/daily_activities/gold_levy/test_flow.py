"""
Flow test Daily Activities / Gold Levy (bot/activities/daily_activities/gold_levy/), phiên bản giao diện mới:
màn chính -> Quests -> tab Activity -> Claim All -> cuộn -> dòng "Levy Gold 5 time(s)" -> Go -> về thành,
Thành chính ở giữa -> menu tròn, icon "Levy" -> popup Levy -> "Free Levy All" (after_go) -> Back.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704: 01..04 chép từ tests/daily_activities/screens/
(dòng Levy ở 04 sát đáy -> cuộn thêm); 04b..08 chụp trên máy 21913 (2026-10-04): 04b dòng Levy, 05 sau Go,
06 menu Thành chính, 07 popup Levy còn free (Free Levy All vàng), 08 sau khi bấm (Free Levy All xám).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities import gold_levy
from bot.activities.daily_activities.common import open_task, task_cards, task_titles
from bot.activities.daily_activities.constants import GO_BUTTON, TASK_OPENED
from bot.activities.daily_activities.gold_levy.run import FREE_LEVY_ALL, MENU_LEVY, after_go
from tests.daily_activities import CLAIM_ALL_ONCE, SCROLL, TO_ACTIVITY, open_task_of
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
LEVY_GO_Y = 461   # Go dưới tiêu đề "Levy Gold 5 time(s)" (y 418) trên 04b_activity_levy_row
KEEP_POS = (222, 345)   # Thành chính khớp ảnh mẫu có sẵn (Images/Event/Building/civ*/keep) trên 05_after_go
TO_GO = [
    *TO_ACTIVITY, *CLAIM_ALL_ONCE,
    Step("03_activity_top.png", SCROLL),
    Step("04_activity_scrolled.png", SCROLL),     # dòng Levy sát đáy (y > ROW_TITLE_MAX_Y): cuộn tiếp
    Step("04b_activity_levy_row.png", tap(GO_BUTTON)),
]
# Sau Go: nhận ra Thành chính theo ảnh mẫu -> bấm vào nó -> menu tròn -> icon Levy -> popup Levy.
TO_POPUP = [
    Step("05_after_go.png", tap_at(*KEEP_POS)),
    Step("06_keep_menu.png", tap(MENU_LEVY)),
]


def _open_and_after_go(bot, _settings):
    """open_task (bấm Go) rồi phần sau Go của Gold Levy."""
    if open_task(bot, task_titles(gold_levy.TASK), task_cards(gold_levy.TASK)) != TASK_OPENED:
        return False
    return after_go(bot)


class GoldLevyFlow(unittest.TestCase):
    def test_open_task(self):
        flow = [*TO_GO, Step("01_main.png", end(result=TASK_OPENED))]
        device = run_flow(self, open_task_of(gold_levy.TASK), SCREENS, flow, {})
        go = [e for _, e in device.events if e[0] == "tap"][-1]
        self.assertEqual(go[2], LEVY_GO_Y)

    def test_after_go_free_levy_all(self):
        """Còn lượt free: bấm Free Levy All -> nút xám -> Back đóng popup -> về thành, xong hôm nay."""
        flow = [
            *TO_GO, *TO_POPUP,
            Step("07_levy_popup.png", tap(FREE_LEVY_ALL)),
            Step("08_levy_done.png", back()),
            Step("05_after_go.png", end(result=True)),
        ]
        device = run_flow(self, _open_and_after_go, SCREENS, flow, {})
        self.assertIn("Gold Levy", device.daily_done)

    def test_after_go_already_used(self):
        """Free Levy All đã xám ngay khi mở popup (hết lượt free): không bấm, Back đóng popup, vẫn xong."""
        flow = [
            *TO_GO, *TO_POPUP,
            Step("08_levy_done.png", back()),
            Step("05_after_go.png", end(result=True)),
        ]
        device = run_flow(self, _open_and_after_go, SCREENS, flow, {})
        self.assertIn("Gold Levy", device.daily_done)


if __name__ == "__main__":
    unittest.main()
