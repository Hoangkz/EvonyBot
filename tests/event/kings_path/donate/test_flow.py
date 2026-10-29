"""
Flow test Event / King's Path / Donate (bot/activities/event/kings_path/donate/): tách từ test_flow.py.
Ảnh dùng chung ở ../screens/ (không chép sang thư mục nhiệm vụ).
"""
import sys
import unittest
from unittest import mock
from bot.activities.event.kings_path import donate, patrol
from bot.activities.event.kings_path.donate.constants import DONATE_BUTTON, GEMS_BUTTON, OKAY
from bot.activities.event.kings_path.donate.alliance import alliance_key as donate_alliance_key
from tests.flow import Step, back, end, swipe, tap, tap_at
from tests.event.kings_path.common import _run
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)


class DonateFlow(unittest.TestCase):
    def test_donate(self):
        """Tab Teamwork: dòng "Donate to the Alliance" (0 / 10) -> Go -> Alliance Science:
        Donate 2 lần -> hết lượt (nút kim cương) -> Okay -> Donate lần 3 (đủ mục tiêu 3) -> vẫn bấm tới khi ra
        nút kim cương rồi mới xong."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 567)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_gems.png", tap(GEMS_BUTTON)),
            Step("donate_confirm_gems.png", tap(OKAY)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_gems.png", end()),   # đủ mục tiêu nhưng vẫn bấm tới khi ra nút kim cương (không mua thêm)
        ]
        device = _run(self, flow, {donate.KEY: {"value": 3, "day": 2}})
        self.assertIn("Donate: done 0, target 3", device.logs)
        self.assertIn(donate.KEY, device.daily_done)

    def test_donate_via_alliance_when_patrol_off(self):
        """Ô Patrol = 0: Donate không vào King's Path mà qua Liên minh -> Alliance Science (ở sẵn
        màn đó), donate 2 lần (lưu từng lần vào daily_done) -> đủ, Back, xong."""
        settings = {patrol.KEY: {"value": 0, "day": 2}, donate.KEY: {"value": 2, "day": 2}}
        flow = [
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_gems.png", back(), end()),   # đủ 2 lần, ra nút kim cương -> Back
        ]
        device = _run(self, flow, settings, ctx_settings={"Event": settings})
        self.assertIn(donate_alliance_key(1), device.daily_done)
        self.assertIn(donate_alliance_key(2), device.daily_done)
        self.assertIn(donate.KEY, device.daily_done)
        self.assertNotIn("King's Path", " ".join(device.logs))

    def test_donate_via_alliance_full_path(self):
        """Ô Patrol = 0, đi đủ đường (ảnh thật): màn chính -> nút Liên minh -> màn Liên minh (Alliance
        Science bị che) -> cuộn 2 lần -> Alliance Science -> donate thẻ đầu (Alliance Capacity) -> xong."""
        settings = {patrol.KEY: {"value": 0, "day": 2}, donate.KEY: {"value": 1, "day": 2}}
        flow = [
            Step("alliance_main.png", tap("JoinBoss/lienminh.png")),
            Step("alliance_screen.png", swipe(50, 87, 50, 54), swipe(50, 87, 50, 54)),
            Step("alliance_scrolled.png", tap("Science/scienceclick.png")),
            Step("alliance_science.png", tap(DONATE_BUTTON)),
            Step("donate_gems.png", back(), end()),   # hết lượt miễn phí (nút kim cương) -> Back
        ]
        device = _run(self, flow, settings, ctx_settings={"Event": settings})
        self.assertIn(donate.KEY, device.daily_done)

    def test_donate_via_alliance_resumes(self):
        """Đường Liên minh, hôm nay đã donate 2 / 3 (bị ngắt): chỉ donate thêm 1 lần."""
        settings = {patrol.KEY: {"value": 0, "day": 2}, donate.KEY: {"value": 3, "day": 2}}
        flow = [
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_gems.png", back(), end()),
        ]
        done = {donate_alliance_key(n): "2026-10-02T08:00:00" for n in (1, 2)}
        device = _run(self, flow, settings, ctx_settings={"Event": settings}, daily_done=done)
        self.assertIn(donate_alliance_key(3), device.daily_done)
        self.assertIn(donate.KEY, device.daily_done)

    def test_donate_gem_limit(self):
        """Đã mua lại lượt đủ MAX_GEM_BUYS lần mà vẫn hết lượt: dừng, không đánh dấu xong."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 567)),
            Step("donate_gems.png", end()),
        ]
        with mock.patch.object(sys.modules["bot.activities.event.kings_path.donate.donating"],
                               "MAX_GEM_BUYS", 0):
            device = _run(self, flow, {donate.KEY: {"value": 60, "day": 2}})
        self.assertNotIn(donate.KEY, device.daily_done)

    def test_donate_out_of_gems(self):
        """Hết lượt miễn phí, bấm nút kim cương -> popup "insufficient Gems ... Buy" -> Back (không Buy), xong hôm
        nay (mai làm tiếp); không bấm kim cương thêm lần nào."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 567)),
            Step("donate_gems.png", tap(GEMS_BUTTON)),
            Step("donate_no_gems.png", back(), end()),
        ]
        device = _run(self, flow, {donate.KEY: {"value": 60, "day": 2}})
        self.assertIn(donate.KEY, device.daily_done)
        self.assertTrue(any("out of gems" in line for line in device.logs))

    def test_donate_via_alliance_out_of_gems(self):
        """Ô Patrol = 0, hết lượt miễn phí: bấm nút kim cương -> popup không đủ kim cương -> Back, xong hôm nay."""
        settings = {patrol.KEY: {"value": 0, "day": 2}, donate.KEY: {"value": 60, "day": 2}}
        flow = [
            Step("donate_gems.png", tap(GEMS_BUTTON)),
            Step("donate_no_gems.png", back(), end()),
        ]
        device = _run(self, flow, settings, ctx_settings={"Event": settings})
        self.assertIn(donate.KEY, device.daily_done)


if __name__ == "__main__":
    unittest.main()
