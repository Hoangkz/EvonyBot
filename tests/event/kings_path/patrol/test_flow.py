"""
Flow test Event / King's Path / Patrol (bot/activities/event/kings_path/patrol/): tách từ test_flow.py.
Ảnh dùng chung ở ../screens/ (không chép sang thư mục nhiệm vụ).
"""
import sys
import unittest

import cv2

from bot.activities.event.constants import CLAIM_ALL
from bot.activities.event.kings_path import patrol
from bot.activities.event.kings_path.patrol.constants import (
    MENU_PATROL,
    PATROL_BUTTON,
    REFRESH_BUTTON as PATROL_REFRESH,
    SELECT_ALL_OFF as PATROL_SELECT_ALL_OFF)
from bot.activities.event.kings_path.patrol.run import round_key as patrol_round_key
from tests.flow import Step, back, end, tap, tap_at
from tests.event.kings_path.common import SCREENS, KP, _run, WALLS_POS
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)


class PatrolFlow(unittest.TestCase):
    def test_patrol(self):
        """Day 2 (tab Unstoppable) -> tab Teamwork -> dòng "Patrol for" trên cùng (140 / 150) -> Go."""
        flow = [
            Step("day2_unstoppable.png", tap(CLAIM_ALL)),
            Step("day2_unstoppable.png?claimed", tap(f"{KP}/Tab/teamwork.png")),
            Step("day2_teamwork.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertIn("Patrol: done 140, target 200", device.logs)

    def test_patrol_rounds(self):
        """Patrol (đã làm 140, mục tiêu 160): Go -> bấm giữa thành -> icon Patrol -> Select All ->
        Patrol (+10) -> đã patrol -> Refresh -> Select All -> Patrol (+10 = 160) -> đủ, Back, xong."""
        rounds = [
            Step("patrol_screen.png", tap(PATROL_SELECT_ALL_OFF)),
            Step("patrol_selected.png", tap(PATROL_BUTTON)),
        ]
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_at(*WALLS_POS)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            *rounds,
            Step("patrol_done.png", tap(PATROL_REFRESH)),
            *rounds,
            Step("patrol_done.png", back(), end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 160, "day": 2}})
        self.assertIn("Patrol: progress 160 / 160, done", device.logs)
        self.assertIn(patrol.KEY, device.daily_done)
        self.assertIn(patrol_round_key(2), device.daily_done)

    def test_patrol_daily_limit(self):
        """Hôm nay đã patrol 9 lượt (lưu daily_done): patrol thêm 1 lượt -> đủ 10 -> Back, xong hôm
        nay (mục tiêu 200 chưa đủ, mai làm tiếp)."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_at(*WALLS_POS)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            Step("patrol_screen.png", tap(PATROL_SELECT_ALL_OFF)),
            Step("patrol_selected.png", tap(PATROL_BUTTON)),
            Step("patrol_done.png", back(), end()),
        ]
        done = {patrol_round_key(n): "2026-10-02T08:00:00" for n in range(1, 10)}
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}}, daily_done=done)
        self.assertIn("Patrol: 10 rounds today, done for today", device.logs)
        self.assertIn(patrol.KEY, device.daily_done)

    def test_patrol_out_of_refreshes(self):
        """Refresh mà phần thưởng vẫn là bộ đã patrol (hết lượt Refresh): Back, xong hôm nay."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_at(*WALLS_POS)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            Step("patrol_done.png", tap(PATROL_REFRESH)),
            Step("patrol_done.png", back(), end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertIn(patrol.KEY, device.daily_done)

    def test_patrol_not_confirmed(self):
        """Bấm Patrol mà màn không chuyển sang "đã patrol" (game chậm / popup): không tính lượt,
        không cộng tiến độ, dừng (không đánh dấu xong)."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_at(*WALLS_POS)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            Step("patrol_selected.png", tap(PATROL_BUTTON)),
            Step("patrol_selected.png", end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertNotIn(patrol_round_key(1), device.daily_done)
        self.assertNotIn(patrol.KEY, device.daily_done)

    def test_patrol_claimed_detection(self):
        """Đếm dấu tích lớn: chưa tích / chỉ tích ô nhỏ -> chưa patrol; sau patrol / hết lượt -> đã."""
        claimed = sys.modules["bot.activities.event.kings_path.patrol.run"]._claimed
        for name, expected in (("patrol_screen.png", False), ("patrol_selected.png", False),
                               ("patrol_done.png", True), ("patrol_no_refresh.png", True)):
            self.assertEqual(claimed(cv2.imread(str(SCREENS / name))), expected, name)

    def test_patrol_refresh_disabled(self):
        """Đã patrol lượt hiện tại, nút Refresh xám (Refreshes Today 10/10, ảnh thật): Back, xong
        hôm nay — không bấm Refresh."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_at(*WALLS_POS)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            Step("patrol_no_refresh.png", back(), end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertIn("Patrol: Refresh disabled (out of refreshes), done for today", device.logs)
        self.assertIn(patrol.KEY, device.daily_done)


if __name__ == "__main__":
    unittest.main()
