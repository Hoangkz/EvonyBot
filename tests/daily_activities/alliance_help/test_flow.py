"""
Flow test Daily Activities / Alliance Help (bot/activities/daily_activities/alliance_help/), `help_all` (theo giờ):
1. Màn chính -> Liên minh -> dòng "Alliance Help" -> màn Alliance Help.
2. "No records" trước khi bấm -> Back, dừng: không kiểm tra Activity, không lưu gì.
3. "Help All" -> bấm -> danh sách trống ("No records") -> Back -> lưu giờ thử -> kiểm tra lưới Activity (giao diện
   cũ): thẻ "Completed" -> xong hôm nay; thẻ còn Go -> chưa xong.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704: alliance_screen / help_list / help_no_records do người
dùng chụp; alliance_main chép từ tests/event/kings_path/screens/; 11..32 chép từ tests/daily_activities/screens/ (18:
thẻ Alliance Help chưa xong; 32: thẻ Alliance Help "Completed", máy 21943). Không bấm Go
nên không cần ảnh popup thẻ.
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities.alliance_help.constants import HELP_ALL, HELP_ROW, LABEL, TRIED_KEY
from bot.activities.daily_activities.alliance_help.run import help_all
from bot.activities.daily_activities.constants import MAIN_MORE, OLD_MENU_ACTIVITY
from tests.daily_activities import SCROLL
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
# Màn chính -> Liên minh -> dòng Alliance Help.
TO_HELP = [
    Step("alliance_main.png", tap("JoinBoss/lienminh.png")),
    Step("alliance_screen.png", tap(HELP_ROW)),
]
# Màn chính -> "•••" -> Activity -> lưới: thẻ "100%" đầu lưới bấm nhận (ảnh tĩnh -> kẹt, bỏ qua) -> cuộn.
TO_GRID = [
    Step("11_old_main.png", tap(MAIN_MORE)),
    Step("12_old_more_menu.png", tap(OLD_MENU_ACTIVITY)),
    Step("13_old_activity_grid.png", tap_at(75, 325)),
    Step("13_old_activity_grid.png", SCROLL),
]


def _help_all(bot, _settings):
    return help_all(bot)


class AllianceHelpFlow(unittest.TestCase):
    def test_help_all_then_done(self):
        """Help All -> danh sách trống ("No records" sau khi bấm: vẫn đi nhận quà) -> Back -> lưới Activity: thẻ
        Completed -> xong hôm nay."""
        flow = [
            *TO_HELP,
            Step("help_list.png", tap(HELP_ALL)),
            Step("help_no_records.png", back()),
            *TO_GRID,
            Step("32_old_grid_end_help_completed.png", back()),
            Step("11_old_main.png", end(result=True)),
        ]
        device = run_flow(self, _help_all, SCREENS, flow, {})
        self.assertIn(LABEL, device.daily_done)
        self.assertIn(TRIED_KEY, device.daily_done)

    def test_no_records_skips_without_saving(self):
        """Không ai cần giúp ("No records" trước khi bấm): Back, dừng — không kiểm tra Activity, không lưu gì."""
        flow = [
            *TO_HELP,
            Step("help_no_records.png", back()),
            Step("alliance_screen.png", end(result=False)),
        ]
        device = run_flow(self, _help_all, SCREENS, flow, {})
        self.assertEqual(device.daily_done, {})

    def test_help_all_not_done_yet(self):
        """Help All nhưng thẻ chưa nhận (chưa đủ 5 lần): không bấm thẻ / Go, Back đóng bảng Activity -> chưa xong (chỉ
        lưu giờ thử)."""
        flow = [
            *TO_HELP,
            Step("help_list.png", tap(HELP_ALL)),
            Step("help_no_records.png", back()),
            *TO_GRID,
            Step("18_old_grid_3.png", back()),   # thẻ chưa nhận = chưa xong: không bấm thẻ, Back đóng bảng
            Step("11_old_main.png", end(result=False)),
        ]
        device = run_flow(self, _help_all, SCREENS, flow, {})
        self.assertNotIn(LABEL, device.daily_done)
        self.assertIn(TRIED_KEY, device.daily_done)


if __name__ == "__main__":
    unittest.main()
