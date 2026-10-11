"""
Flow test Daily Activities / Alliance Donation (bot/activities/daily_activities/alliance_donation/), `donate_free`:
Liên minh -> kéo xuống Alliance Science -> Donate tới khi hết lượt miễn phí (nút kim cương, không mua) -> Back -> LƯU giờ vừa
donate vào DB (TRIED_KEY) -> ra danh sách nhiệm vụ nhận thưởng (collect_activity_rewards, được thay bằng mock ở đây: phần
nhận thưởng có test riêng). Không tìm dòng nhiệm vụ rồi bấm Go, không mở bảng Activity để kiểm tra dòng đã xong chưa.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704: alliance_*, donate_* chép từ tests/event/kings_path/screens/
(donate_science_21943: 13/13 lượt free).
"""
import importlib
import unittest
from pathlib import Path
from unittest import mock

from bot.activities.daily_activities.alliance_donation.constants import LABEL, TRIED_KEY
from bot.activities.event.kings_path.donate.constants import DONATE_BUTTON_2
from tests.flow import Step, back, end, run_flow, swipe, tap

run_module = importlib.import_module("bot.activities.daily_activities.alliance_donation.run")

SCREENS = Path(__file__).parent / "screens"
# Màn chính -> Liên minh -> cuộn 2 lần -> Alliance Science.
TO_SCIENCE = [
    Step("alliance_main.png", tap("JoinBoss/lienminh.png")),
    Step("alliance_screen.png", swipe(50, 87, 50, 54), swipe(50, 87, 50, 54)),
    Step("alliance_scrolled.png", tap("Science/scienceclick.png")),
]


def _donate_free(bot, _settings):
    return bool(run_module.donate_free(bot))


class AllianceDonationFlow(unittest.TestCase):
    def run_with_rewards_mocked(self, flow):
        with mock.patch.object(run_module, "collect_activity_rewards") as collect:
            device = run_flow(self, _donate_free, SCREENS, flow, {})
        return device, collect

    def test_donate_free_saves_the_time_then_claims_rewards(self):
        """Donate 1 lượt free -> hết lượt (nút kim cương, không mua) -> Back -> lưu giờ vào DB -> nhận thưởng. Việc theo giờ
        không có "xong hôm nay": chỉ lưu giờ, không lưu nhãn."""
        flow = [
            *TO_SCIENCE,
            Step("donate_science_21943.png", tap(DONATE_BUTTON_2)),
            Step("donate_gems.png", back()),
            Step("alliance_main.png", end(result=False)),
        ]
        device, collect = self.run_with_rewards_mocked(flow)
        self.assertIn(TRIED_KEY, device.daily_done)       # đã donate lúc mấy giờ
        self.assertNotIn(LABEL, device.daily_done)        # không "xong hôm nay": mỗi N giờ lại donate
        collect.assert_called_once()                      # ra danh sách nhiệm vụ nhận thưởng

    def test_no_free_donation_stops_without_claiming(self):
        """Hết lượt free ngay khi vào Alliance Science: Back, dừng — không mua, không nhận thưởng, chưa lưu giờ (giờ chờ
        lượt sau do common.hourly_job lưu)."""
        flow = [
            *TO_SCIENCE,
            Step("donate_gems.png", back()),
            Step("alliance_main.png", end(result=False)),
        ]
        device, collect = self.run_with_rewards_mocked(flow)
        self.assertNotIn(TRIED_KEY, device.daily_done)
        self.assertNotIn(LABEL, device.daily_done)
        collect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
