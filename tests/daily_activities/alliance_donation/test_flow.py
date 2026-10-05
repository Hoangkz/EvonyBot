"""
Flow test Daily Activities / Alliance Donation (bot/activities/daily_activities/alliance_donation/), luồng mới
`donate_free` (giao diện CŨ — lưới thẻ Activity):
1. Kiểm tra trước: màn chính -> "•••" -> Activity -> lưới -> thẻ Alliance Donation: "Completed" -> xong, thôi.
2. Chưa xong (thẻ còn Go, không bấm) -> Liên minh -> cuộn -> Alliance Science -> Donate tới khi hết lượt
   miễn phí (nút kim cương) -> Back -> kiểm tra lại -> "Completed" -> xong.
3. Không còn lượt miễn phí -> dừng, không kiểm tra lại, không đánh dấu xong.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704: 11..31 chép từ tests/daily_activities/screens/
(18: thẻ Alliance Donation chưa xong; 31: thẻ "Completed", máy 21943); alliance_*, donate_* chép từ
tests/event/kings_path/screens/ (donate_science_21943: 13/13 lượt free). Không bấm
Go nên không cần ảnh popup thẻ.
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities.alliance_donation.constants import LABEL, TRIED_KEY
from bot.activities.daily_activities.alliance_donation.run import donate_free
from bot.activities.daily_activities.constants import MAIN_MORE, OLD_MENU_ACTIVITY
from bot.activities.event.kings_path.donate.constants import DONATE_BUTTON_2
from tests.daily_activities import SCROLL
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
# Màn chính -> "•••" -> Activity -> lưới: thẻ "100%" đầu lưới bấm nhận (ảnh tĩnh nên vẫn "100%" -> coi là kẹt,
# bỏ qua) -> cuộn.
TO_GRID = [
    Step("11_old_main.png", tap(MAIN_MORE)),
    Step("12_old_more_menu.png", tap(OLD_MENU_ACTIVITY)),
    Step("13_old_activity_grid.png", tap_at(75, 325)),
    Step("13_old_activity_grid.png", SCROLL),
]
# Thẻ đã "Completed" -> TASK_DONE -> Back đóng bảng Activity.
CHECK_DONE = [*TO_GRID, Step("31_old_grid_end_donation_completed.png", back())]
# Thẻ chưa nhận = chưa xong: không bấm thẻ / Go, Back đóng bảng Activity.
CHECK_NOT_DONE = [
    *TO_GRID,
    Step("18_old_grid_3.png", back()),   # thẻ chưa nhận = chưa xong: không bấm thẻ, Back đóng bảng
]
# Màn chính -> Liên minh -> cuộn 2 lần -> Alliance Science.
TO_SCIENCE = [
    Step("alliance_main.png", tap("JoinBoss/lienminh.png")),
    Step("alliance_screen.png", swipe(50, 87, 50, 54), swipe(50, 87, 50, 54)),
    Step("alliance_scrolled.png", tap("Science/scienceclick.png")),
]


def _donate_free(bot, _settings):
    return donate_free(bot)


class AllianceDonationFlow(unittest.TestCase):
    def test_already_done_skips_donating(self):
        """Kiểm tra trước thấy thẻ Completed: đánh dấu xong, không đi Liên minh."""
        flow = [*CHECK_DONE, Step("11_old_main.png", end(result=True))]
        device = run_flow(self, _donate_free, SCREENS, flow, {})
        self.assertIn(LABEL, device.daily_done)
        self.assertIn(TRIED_KEY, device.daily_done)

    def test_donate_free_then_done(self):
        """Chưa xong: donate 1 lượt free -> hết lượt (nút kim cương, không mua) -> Back -> kiểm tra lại ->
        Completed -> xong."""
        flow = [
            *CHECK_NOT_DONE, *TO_SCIENCE,
            Step("donate_science_21943.png", tap(DONATE_BUTTON_2)),
            Step("donate_gems.png", back()),
            *CHECK_DONE,
            Step("11_old_main.png", end(result=True)),
        ]
        device = run_flow(self, _donate_free, SCREENS, flow, {})
        self.assertIn(LABEL, device.daily_done)

    def test_no_free_donation_stops(self):
        """Chưa xong và hết lượt free ngay khi vào Alliance Science: Back, dừng — không mua, không kiểm tra
        lại, không đánh dấu xong (chỉ lưu giờ thử)."""
        flow = [
            *CHECK_NOT_DONE, *TO_SCIENCE,
            Step("donate_gems.png", back()),
            Step("alliance_main.png", end(result=False)),
        ]
        device = run_flow(self, _donate_free, SCREENS, flow, {})
        self.assertNotIn(LABEL, device.daily_done)
        self.assertIn(TRIED_KEY, device.daily_done)


if __name__ == "__main__":
    unittest.main()
