"""
Test Alliance Capacity (bot/activities/alliance_capacity/): hết lượt donate free (Remaining Donations 0/13), bấm nút
kim cương ở Alliance Science -> popup "insufficient Gems ... Buy" -> bot đóng popup bằng Back (KHÔNG bấm Buy) rồi
dừng hoạt động (worker chuyển sang việc khác).
Ảnh: tests/alliance_capacity/screens/ (máy thật, tài khoản thiếu kim cương).
"""
import unittest
from pathlib import Path

from bot.activities.alliance_capacity.run import run
from tests.flow import Step, back, end, run_flow, tap

SCREENS = Path(__file__).parent / "screens"


class BuyGemsPopup(unittest.TestCase):
    def test_stops_on_buy_popup(self):
        """Màn Science: bấm nút kim cương; popup Buy hiện -> Back (không Buy) -> activity return."""
        flow = [
            Step("01_gem_button.png", tap("Science/1sciencekc.png")),
            Step("02_buy_gems_popup.png", back(), end()),
        ]
        run_flow(self, run, SCREENS, flow, {"times": "ALL"})


if __name__ == "__main__":
    unittest.main()
