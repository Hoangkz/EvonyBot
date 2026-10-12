"""
Flow test Event / King's Path / Wheel (bot/activities/event/kings_path/wheel/): tách từ test_flow.py.
Ảnh dùng chung ở ../screens/ (không chép sang thư mục nhiệm vụ).
"""
import unittest
from bot.activities.event.kings_path import wheel
from bot.activities.event.kings_path.wheel.constants import SPINS_10, SPINS_100
from tests.flow import Step, back, end, tap, tap_at
from tests.event.kings_path.common import KP, _run
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)


class WheelFlow(unittest.TestCase):
    def test_wheel(self):
        """Day 4 tab Accumulation -> tab Fortune Wheel -> Go trên cùng -> màn Wheel of
        Fortune -> bấm "100 Spins" một lần -> xong."""
        flow = [
            Step("day4_accumulation.png", tap(f"{KP}/Tab/fortuneWheel.png")),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertIn(wheel.KEY, device.daily_done)

    def test_wheel_out_of_chips(self):
        """Chỉ có 10 Spins: bấm liên tục (kể cả khi bảng kết quả đang hiện) tới khi không đủ chip,
        game mở Purchase Chips -> Back, đánh dấu xong hôm nay (không dùng chip trong túi)."""
        flow = [
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_10_only.png", tap(SPINS_10)),
            Step("wheel_result_10.png", tap(SPINS_10)),
            Step("wheel_chips_empty.png", back(), end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertIn("Wheel: out of chips after 2 x 10 Spins, done for today", device.logs)
        self.assertIn(wheel.KEY, device.daily_done)

    def test_wheel_no_button(self):
        """Sau Go không thấy nút "100 Spins" (màn khác): không đánh dấu xong."""
        flow = [
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("day4_accumulation.png", end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertNotIn(wheel.KEY, device.daily_done)


if __name__ == "__main__":
    unittest.main()
