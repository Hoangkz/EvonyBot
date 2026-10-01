"""
Flow test Event / King's Path (bot/activities/event/kings_path/): phần trên màn King's Path
— kiểm Day khoá -> tab Day -> tab phụ -> dòng Go của nhiệm vụ -> đọc tiến độ -> bấm Go.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (Day 5 đang khoá).

TODO: chưa có ảnh icon King's Path trong danh sách event (KINGS_PATH_ICON) nên các test bắt
đầu ngay ở màn King's Path, và tạm trỏ KINGS_PATH_ICON sang icon Gather Troops để nhiệm vụ
không bị bỏ qua. Có ảnh thì thêm bước 03_main -> 04_event_list như Gather Troops.
"""
import unittest
from pathlib import Path
from unittest import mock

from bot.activities import event
from bot.activities.event.constants import CLAIM_ALL, GATHER_TROOPS_ICON
from bot.activities.event.kings_path import donate, heal, patrol, path_task, wheel
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
KP = "Event/KingsPath"


def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng."""
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


VARIANTS = {
    # Đã bấm Claim All: xoá nút Claim All ở đáy màn.
    "claimed": _blank(655, 695, 140, 256),
    # Màn event cùng khung nhưng không phải King's Path (VD Gather Troops): xoá tiêu đề.
    "not_kp": _blank(5, 40, 120, 280),
}


def _run(testcase, flow, settings, **kw):
    with mock.patch.object(path_task, "KINGS_PATH_ICON", GATHER_TROOPS_ICON):
        return run_flow(testcase, event.run, SCREENS, flow, settings, variants=VARIANTS, **kw)


class KingsPathFlow(unittest.TestCase):
    def test_patrol(self):
        """Day 2 (tab Unstoppable) -> tab Teamwork -> dòng "Patrol for" trên cùng (140 / 150) -> Go."""
        flow = [
            Step("day2_unstoppable.png", tap(CLAIM_ALL)),
            Step("day2_unstoppable.png?claimed", tap(f"{KP}/Tab/teamwork.png")),
            Step("day2_teamwork.png", tap_at(335, 344), end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertIn("Patrol: done 140, target 200", device.logs)

    def test_donate(self):
        """Tab Teamwork: dòng "Donate to the Alliance" (dưới các dòng Patrol) -> Go."""
        flow = [Step("day2_teamwork.png", tap_at(335, 567), end())]
        device = _run(self, flow, {donate.KEY: {"value": 60, "day": 2}})
        self.assertIn("Donate: done 0, target 60", device.logs)

    def test_target_reached(self):
        """Đã đạt mục tiêu người dùng chọn (140 >= 100): đánh dấu xong, không bấm Go."""
        flow = [Step("day2_teamwork.png", end())]
        device = _run(self, flow, {patrol.KEY: {"value": 100, "day": 2}})
        self.assertIn(patrol.KEY, device.daily_done)

    def test_open_day(self):
        """Đang ở Day 4 -> bấm Day 3 -> tab Healing Heart đang chọn -> Go trên cùng."""
        flow = [
            Step("day4_accumulation.png", tap(f"{KP}/Day/day3.png")),
            Step("day3_healing_heart.png", tap_at(335, 344), end()),
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: done 0, target 50000", device.logs)

    def test_open_tab(self):
        """Day 4 tab Accumulation -> tab Fortune Wheel -> Go trên cùng."""
        flow = [
            Step("day4_accumulation.png", tap(f"{KP}/Tab/fortuneWheel.png")),
            Step("day4_fortune_wheel.png", tap_at(335, 344), end()),
        ]
        _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})

    def test_day_locked(self):
        """Ngày của nhiệm vụ còn khoá (Day 5): lưu "chưa thể thực hiện", không bấm gì."""
        flow = [Step("day4_fortune_wheel.png", end())]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 5}})
        self.assertIn(f"{wheel.KEY}_locked", device.daily_done)
        self.assertNotIn(wheel.KEY, device.daily_done)

    def test_not_kings_path_backs(self):
        """Hàng tab Day giống Gather Troops: không thấy tiêu đề King's Path -> Back."""
        flow = [
            Step("day4_fortune_wheel.png?not_kp", back()),
            Step("day4_fortune_wheel.png", tap_at(335, 344), end()),
        ]
        _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})

    def test_no_icon_skips(self):
        """Chưa có ảnh icon King's Path: bỏ qua nhiệm vụ, không bấm gì."""
        flow = [Step("day4_fortune_wheel.png", end())]
        run_flow(self, event.run, SCREENS, flow, {wheel.KEY: {"value": 100, "day": 4}})


if __name__ == "__main__":
    unittest.main()
