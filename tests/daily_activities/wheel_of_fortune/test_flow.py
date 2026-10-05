"""
Flow test Daily Activities / Wheel of Fortune (bot/activities/daily_activities/wheel_of_fortune/), luồng mới `after_go`
(event/kings_path/wheel spin_wheel, max_spins_10=1): Go -> màn Wheel of Fortune -> "100 Spins" nếu có (-> Back), không
thì "10 Spins" đúng 1 lần -> Back -> xong hôm nay (không quay tới hết chip, không vào Purchase Chips).

Ảnh dùng chung, không chép (ảnh chụp nguyên màn hình giả lập 396x704): wheel_* ở tests/event/kings_path/screens/.
"""
import unittest

from bot.activities.daily_activities.wheel_of_fortune.constants import LABEL
from bot.activities.daily_activities.wheel_of_fortune.run import after_go
from bot.activities.event.kings_path.wheel.constants import SPINS_10, SPINS_100
from tests.daily_activities import KP, TESTS_DIR
from tests.flow import Step, back, end, run_flow, tap

SCREENS = TESTS_DIR


def _after_go(bot, _settings):
    return after_go(bot)


class WheelOfFortuneFlow(unittest.TestCase):
    def test_spin_100(self):
        """Có "100 Spins": bấm -> Back -> xong hôm nay."""
        flow = [Step(f"{KP}wheel_of_fortune.png", tap(SPINS_100), back(), end(result=True))]
        device = run_flow(self, _after_go, SCREENS, flow, {})
        self.assertIn(LABEL, device.daily_done)

    def test_spin_10_once(self):
        """Chỉ có "10 Spins": bấm 1 lần -> Back -> xong hôm nay (không bấm tiếp tới hết chip)."""
        flow = [
            Step(f"{KP}wheel_10_only.png", tap(SPINS_10)),
            Step(f"{KP}wheel_result_10.png", back(), end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {})
        self.assertIn(f"{LABEL}: 1 x 10 Spins, back, done", device.logs)
        self.assertIn(LABEL, device.daily_done)

    def test_out_of_chips_first_spin(self):
        """Bấm 10 Spins mà không đủ chip: game mở Purchase Chips -> Back -> xong hôm nay."""
        flow = [
            Step(f"{KP}wheel_10_only.png", tap(SPINS_10)),
            Step(f"{KP}wheel_chips_empty.png", back(), end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {})
        self.assertIn(LABEL, device.daily_done)


if __name__ == "__main__":
    unittest.main()
