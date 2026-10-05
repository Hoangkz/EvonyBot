"""
Flow test Daily Activities / General Enhancing (bot/activities/daily_activities/general_enhancing/), luồng mới
`after_go` (giao diện cũ, máy 21943): danh sách Generals -> tích lọc yêu thích -> kéo xuống cuối -> tướng cuối ->
"Cultivate" -> màn Cultivate -> 5 lần "Gold Cultivate" -> kết quả -> Cancel -> Back 3 lần, xong hôm nay.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704, chụp trên máy 21943 (2026-10-04): 05 danh sách tim
chưa tích, 06 đã tích + cuộn cuối, 07 màn tướng, 08 màn Cultivate, 09 kết quả Gold Cultivate (Cancel / Confirm).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities.general_enhancing.constants import (
    CULTIVATE_CANCEL,
    CULTIVATE_GOAL,
    GOLD_CULTIVATE,
    LABEL,
)
from bot.activities.daily_activities.general_enhancing.run import after_go
from bot.activities.event.gather_troops.cultivate_generals.constants import CULTIVATE_BUTTONS, FAVORITE_OFF
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_pct

SCREENS = Path(__file__).parent / "screens"
# Tim lọc yêu thích chưa tích -> bấm; đã tích -> kéo nhanh 6 lần -> bấm tướng cuối (10 %, 90 %) -> màn tướng ->
# Cultivate (mẫu 3 nút).
TO_CULTIVATE = [
    Step("05_generals_heart_off.png", tap(FAVORITE_OFF)),
    Step("06_generals_favorite_end.png", *[swipe(50, 85, 50, 15) for _ in range(6)], tap_pct(10, 90)),
    Step("07_general_detail.png", tap(CULTIVATE_BUTTONS[0])),
]
ONE_CULTIVATE = [
    Step("08_cultivate.png", tap(GOLD_CULTIVATE)),
    Step("09_cultivate_result.png", tap(CULTIVATE_CANCEL)),
]


def _after_go(bot, _settings):
    return after_go(bot)


class GeneralEnhancingFlow(unittest.TestCase):
    def test_after_go_gold_cultivate_five_times(self):
        """5 lần Gold Cultivate (mỗi lần Cancel kết quả) -> Back 3 lần -> xong hôm nay."""
        flow = [
            *TO_CULTIVATE,
            *ONE_CULTIVATE * CULTIVATE_GOAL,
            Step("08_cultivate.png", back(), back(), back()),
            Step("05_generals_heart_off.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {})
        self.assertIn(LABEL, device.daily_done)
        self.assertIn(f"{LABEL}: Gold Cultivate x{CULTIVATE_GOAL}, done", device.logs)

    def test_gold_cultivate_no_result_stops(self):
        """Bấm Gold Cultivate mà không ra kết quả (thiếu vàng / game chậm): không tính, dừng, không đánh dấu."""
        flow = [
            *TO_CULTIVATE,
            Step("08_cultivate.png", tap(GOLD_CULTIVATE)),
            Step("08_cultivate.png", end(result=False)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {})
        self.assertNotIn(LABEL, device.daily_done)


if __name__ == "__main__":
    unittest.main()
