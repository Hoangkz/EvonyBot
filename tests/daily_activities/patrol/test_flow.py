"""
Flow test Daily Activities / Patrol (bot/activities/daily_activities/patrol/), luồng mới `after_go` (giống hệt
King's Path Patrol sau Go): về thành -> Tường thành (ảnh mẫu civ) -> menu "Patrol" -> màn Patrol -> mỗi lượt
Select All -> Patrol -> Refresh, làm hết 10 lượt trong ngày (đếm riêng daily_patrol_round_<n>) hoặc tới khi hết
Refresh -> Back, xong hôm nay.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704, chép từ tests/event/kings_path/screens/ (màn
Patrol dùng chung với King's Path).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities.patrol.constants import KEY, LABEL
from bot.activities.daily_activities.patrol.run import after_go
from bot.activities.event.kings_path.patrol.constants import (
    MENU_PATROL,
    PATROL_BUTTON,
    REFRESH_BUTTON,
    SELECT_ALL_OFF,
)
from bot.activities.event.kings_path.patrol.constants import KEY as KP_KEY
from bot.activities.event.kings_path.patrol.run import round_key
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
WALLS_POS = (246, 345)   # Tường thành trên patrol_city khớp ảnh mẫu civ (Images/Event/Building/civ*/walls)
TO_PATROL = [
    Step("patrol_city.png", tap_at(*WALLS_POS)),
    Step("patrol_menu.png", tap(MENU_PATROL)),
]
ROUND = [
    Step("patrol_screen.png", tap(SELECT_ALL_OFF)),
    Step("patrol_selected.png", tap(PATROL_BUTTON)),
]


def _after_go(bot, _settings):
    return after_go(bot)


def _rounds_done(*numbers, key=KEY):
    return {round_key(n, key): "2026-10-04T08:00:00" for n in numbers}


class PatrolFlow(unittest.TestCase):
    def test_after_go_until_ten_rounds(self):
        """Hôm nay Daily đã patrol 8 lượt: patrol lượt 9 -> Refresh -> lượt 10 -> đủ 10 lượt -> Back, xong hôm nay
        (không dừng sau 1 lượt dù nhiệm vụ chỉ cần 3)."""
        flow = [
            *TO_PATROL,
            *ROUND,
            Step("patrol_done.png", tap(REFRESH_BUTTON)),
            *ROUND,
            Step("patrol_done.png", back()),
            Step("patrol_city.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {}, daily_done=_rounds_done(*range(1, 9)))
        self.assertIn(round_key(9, KEY), device.daily_done)
        self.assertIn(round_key(10, KEY), device.daily_done)
        self.assertIn(LABEL, device.daily_done)
        self.assertIn(f"{LABEL}: 10 rounds today, done for today", device.logs)

    def test_rounds_counted_separately_from_kings_path(self):
        """King's Path đã patrol đủ 10 lượt hôm nay: Daily vẫn đếm riêng (0 lượt) nên vẫn patrol; game hết lượt thật
        thì nút Refresh xám -> Back, xong hôm nay."""
        flow = [
            *TO_PATROL,
            Step("patrol_no_refresh.png", back()),
            Step("patrol_city.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {},
                          daily_done=_rounds_done(*range(1, 11), key=KP_KEY))
        self.assertIn(f"{LABEL}: Refresh disabled (out of refreshes), done for today", device.logs)
        self.assertIn(LABEL, device.daily_done)
        self.assertNotIn(round_key(1, KEY), device.daily_done)

    def test_after_go_not_confirmed(self):
        """Bấm Patrol mà màn không chuyển sang "đã patrol" (thiếu kim cương / game chậm): không tính lượt, dừng,
        không đánh dấu xong."""
        flow = [
            *TO_PATROL,
            Step("patrol_selected.png", tap(PATROL_BUTTON)),
            Step("patrol_selected.png", end(result=False)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {})
        self.assertNotIn(round_key(1, KEY), device.daily_done)
        self.assertNotIn(LABEL, device.daily_done)


if __name__ == "__main__":
    unittest.main()
