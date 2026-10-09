"""
Flow test event 3 ngày Event Center (bot/activities/event_center/three_day), ảnh "Precious Vegetation".

Ảnh chung: màn chính của Crazy Eggs (tests/event_center/crazy_eggs/screens/01_main.png).
Ảnh tổng hợp (chưa có ảnh chụp thật):
- `food_grey`: 06_redeem.png với nút Redeem của quà 500k Food thay bằng nút xám lấy từ
  06_redeem_grey.png — trạng thái hết vé sau khi đổi.
"""
import importlib
import unittest
from pathlib import Path
from unittest import mock

import cv2

from bot.activities.event_center.three_day import constants as c
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at

SCREENS = Path(__file__).resolve().parents[1]   # tests/event_center
MAIN = "crazy_eggs/screens/01_main.png"
TD = "three_day/screens/"
run_module = importlib.import_module("bot.activities.event_center.three_day.run")
ICON = "EventCenter/ThreeDay/Icons/precious_vegetation.png"


def _food_grey(screen):
    grey = cv2.imread(str(SCREENS / TD / "06_redeem_grey.png"))
    screen[334:366, 296:372] = grey[545:577, 296:372]
    return screen


VARIANTS = {"food_grey": _food_grey}
OFF = {"three_day_alliance": {"value": 0}, "three_day_heal": {"value": 0}}


def _to_event():
    """Màn chính -> Event Center (chính nút cúp) -> tab Limited -> cuộn -> icon event."""
    return [
        Step(MAIN, tap_at(359, 216)),
        Step(TD + "02_limited.png", tap("EventCenter/limitedTabOn.png")),
        Step(TD + "02_limited.png", swipe()),
        Step(TD + "03_limited_scrolled.png", tap(ICON)),
    ]


class ThreeDayFlow(unittest.TestCase):
    def _run(self, flow, settings, **kwargs):
        return run_flow(self, run_module.run, SCREENS, flow, settings,
                        ctx_settings={"Event": settings}, variants=VARIANTS, **kwargs)

    def test_claim_and_redeem(self):
        """Không bật nhiệm vụ nào: sang tab Redeem luôn, đổi quà ưu tiên
        (Food, hàng 0: tìm ảnh quà theo ưu tiên thấy Food ở hàng 0 nên không cuộn): popup số lượng -> bấm cạnh "+" -> nút xanh -> Congratulations -> Back -> nút xám ->
        sang quà kế (hết danh sách ưu tiên), lưu đã xong hôm nay."""
        flow = _to_event() + [
            # Cả 2 nhiệm vụ đã xong: sang tab Redeem luôn, không cuộn lại danh sách nhiệm vụ.
            Step(TD + "04_tasks.png", tap_at(*c.REDEEM_TAB_TAP)),
            Step(TD + "06_redeem.png", tap_at(334, 350)),
            Step(TD + "07_qty_popup.png", tap_at(*c.QTY_MAX_TAP), tap_at(*c.QTY_CONFIRM_TAP)),
            Step(TD + "08_congratulations.png", back()),
            Step(TD + "06_redeem.png?food_grey", end()),
        ]
        settings = {**OFF, "three_day_redeem": {"order": ["food"]}}
        with mock.patch.object(run_module, "_order", return_value=["food"]):
            device = self._run(flow, settings)
        self.assertIn(c.DONE_KEY, device.daily_done)

    def test_alliance_row_go(self):
        """Alliance 60: cuộn xuống, thấy chữ chung "Donate to the Alliance" + nút Go, đọc tiến độ 0 < 60, bấm Go,
        gọi after_go (donate) với done 0, mục tiêu 60; không đạt mục tiêu vẫn lưu xong hôm nay."""
        calls = []

        def after_go(bot, path, done, target):
            calls.append((path.key, done, target))

        flow = _to_event() + [
            # Vào là ở đầu danh sách (không cuộn lên): chưa thấy nút Go (dòng Donate sát mép) -> cuộn xuống.
            Step(TD + "04_tasks.png", swipe()),
            # Thấy Go của dòng Donate đầu (3 mốc dùng chung bộ đếm): OCR 0 < 60 -> bấm Go dòng đó.
            # Sau mỗi lần Go bot quét lại từ đầu, OCR lại (vẫn 0 < 60) và bấm Go lại, tối đa GO_TRIES lần;
            # lần thứ GO_TRIES + 1 thì coi là không đạt, xong hôm nay.
            *[Step(TD + "05_donate_rows.png", tap_at(336, 390, tol=6)) for _ in range(c.GO_TRIES)],
            Step(TD + "05_donate_rows.png", end()),
        ]
        settings = {"three_day_alliance": {"value": 60}, "three_day_heal": {"value": 0}}
        # after_go không đạt mục tiêu: vẫn lưu xong hôm nay (mai làm lại), rồi mới sang nhận quà
        # (nhánh nhận quà có test riêng nên ở đây bỏ qua).
        with mock.patch.object(run_module, "TASKS", [(c.ALLIANCE_KEY, "Alliance", after_go)]),                 mock.patch.object(run_module, "_claim_and_redeem", return_value=None):
            device = self._run(flow, settings)
        self.assertEqual(calls, [(c.ALLIANCE_KEY, 0, 60)] * c.GO_TRIES)
        self.assertIn(c.ALLIANCE_KEY, device.daily_done)

    def test_heal_row_go(self):
        """Heal 5000: cuộn xuống thấy chữ chung "Heal" + nút Go (dòng Heal đầu thấy được), đọc tiến độ 0 < 5000, bấm
        Go của dòng, gọi after_go (heal) với done 0, mục tiêu 5000."""
        calls = []

        def after_go(bot, path, done, target):
            calls.append((path.key, done, target))

        flow = _to_event() + [
            Step(TD + "04_tasks.png", swipe()),
            *[Step(TD + "05_heal_rows.png", tap_at(336, 358, tol=6)) for _ in range(c.GO_TRIES)],
            Step(TD + "05_heal_rows.png", end()),
        ]
        settings = {"three_day_alliance": {"value": 0}, "three_day_heal": {"value": 5000}}
        with mock.patch.object(run_module, "TASKS", [(c.HEAL_KEY, "Heal", after_go)]),                 mock.patch.object(run_module, "_claim_and_redeem", return_value=None):
            device = self._run(flow, settings)
        self.assertEqual(calls, [(c.HEAL_KEY, 0, 5000)] * c.GO_TRIES)
        self.assertIn(c.HEAL_KEY, device.daily_done)

    def test_tasks_not_found_three_times_then_marked(self):
        """Không thấy nhiệm vụ nào: Back rồi làm lại, 3 lần; vẫn không thấy -> ghi lỗi, đánh dấu xong hôm nay
        (cả 2 nhiệm vụ) rồi sang nhận quà."""
        flow = [Step(MAIN, back()), Step(MAIN, back()), Step(MAIN, end())]
        settings = {"three_day_alliance": {"value": 60}, "three_day_heal": {"value": 30000}}
        with mock.patch.object(run_module, "_run_tasks", return_value=c.NOT_FOUND) as scan,                 mock.patch.object(run_module, "_claim_and_redeem", return_value=None):
            device = self._run(flow, settings)
        self.assertEqual(scan.call_count, c.TASK_SEARCH_TRIES)
        self.assertIn(c.ALLIANCE_KEY, device.daily_done)
        self.assertIn(c.HEAL_KEY, device.daily_done)
        self.assertTrue(any("không tìm thấy nhiệm vụ" in log for log in device.logs))

    def test_redeem_grey_item_skipped(self):
        """Quà ưu tiên có nút Redeem xám (Refining Stone, màn 06_redeem_grey): không bấm, loại khỏi danh sách; hết
        danh sách đổi thì xong."""
        flow = _to_event() + [
            Step(TD + "04_tasks.png", tap_at(*c.REDEEM_TAB_TAP)),
            Step(TD + "06_redeem_grey.png", end()),
        ]
        with mock.patch.object(run_module, "_order", return_value=["refining_stone"]):
            device = self._run(flow, OFF)
        self.assertTrue(any("greyed, skip" in log for log in device.logs))
        self.assertIn(c.DONE_KEY, device.daily_done)

    def test_done_marks_do_not_skip_scan(self):
        """Nhiệm vụ đã có dấu "xong" trong daily_done (donate tự lưu) vẫn phải được kiểm tra khi vào danh sách: thấy Go,
        OCR lại thấy chưa đủ 60 thì vẫn bấm Go."""
        calls = []

        def after_go(bot, path, done, target):
            calls.append(done)

        flow = _to_event() + [
            Step(TD + "04_tasks.png", swipe()),
            *[Step(TD + "05_donate_rows.png", tap_at(336, 390, tol=6)) for _ in range(c.GO_TRIES)],
            Step(TD + "05_donate_rows.png", end()),
        ]
        marks = {c.ALLIANCE_KEY: "2026-10-06T09:00:00", f"{c.ALLIANCE_KEY}_complete_60": "2026-10-06T09:00:00",
                 f"{c.ALLIANCE_KEY}_reached_60": "2026-10-06T09:00:00"}
        settings = {"three_day_alliance": {"value": 60}, "three_day_heal": {"value": 0}}
        with mock.patch.object(run_module, "TASKS", [(c.ALLIANCE_KEY, "Alliance", after_go)]),                 mock.patch.object(run_module, "_claim_and_redeem", return_value=None):
            self._run(flow, settings, daily_done=marks)
        self.assertEqual(calls, [0] * c.GO_TRIES)

    def test_done_when_requirement_reached(self):
        """Trường hợp 1: có Go, OCR lại số đã làm >= mục tiêu -> xong, không bấm Go (VD đã làm 60 / mục tiêu 10)."""
        flow = _to_event() + [
            Step(TD + "04_tasks.png", swipe()),
            Step(TD + "05_donate_rows.png", end()),
        ]
        settings = {"three_day_alliance": {"value": 10}, "three_day_heal": {"value": 0}}
        with mock.patch.object(run_module, "_progress", return_value=60),                 mock.patch.object(run_module, "_claim_and_redeem", return_value=None):
            device = self._run(flow, settings)
        self.assertTrue(any("target reached (60 >= 10)" in log for log in device.logs))
        self.assertIn(c.ALLIANCE_KEY, device.daily_done)

    def test_done_when_three_rows_claimed(self):
        """Trường hợp 2: chưa kết luận được ở màn đầu (dòng sát mép) -> cuộn xuống thấy cả 3 dòng Donate đều Claimed
        -> xong, không bấm gì."""
        flow = _to_event() + [
            Step(TD + "04_tasks.png", swipe()),
            Step(TD + "05_donate_claimed.png", end()),
        ]
        settings = {"three_day_alliance": {"value": 60}, "three_day_heal": {"value": 0}}
        with mock.patch.object(run_module, "_claim_and_redeem", return_value=None):
            device = self._run(flow, settings)
        self.assertTrue(any("3 rows all Claimed" in log for log in device.logs))
        self.assertIn(c.ALLIANCE_KEY, device.daily_done)

    def test_claim_tapped_then_all_claimed(self):
        """Trường hợp 3: dòng có Claim (nổi lên đầu danh sách lúc vào) -> bấm nhận quà; sau khi nhận cả 3 dòng
        thành Claimed -> xong."""
        flow = _to_event() + [
            Step(TD + "04_tasks_claim.png", tap("EventCenter/ThreeDay/claim.png")),
            Step(TD + "05_donate_claimed.png", end()),
        ]
        settings = {"three_day_alliance": {"value": 60}, "three_day_heal": {"value": 0}}
        with mock.patch.object(run_module, "_claim_and_redeem", return_value=None):
            device = self._run(flow, settings)
        self.assertIn(c.ALLIANCE_KEY, device.daily_done)

    def test_claim_tapped_on_device_21943(self):
        """Máy 21943: nút Claim lệch 4 px (tâm x 330, khớp 0,86): vẫn nhận ra và bấm nhận quà ở dòng Donate đầu
        (ảnh thật lúc vào event, có 2 nút Claim ở dòng Donate 10 và 30)."""
        flow = _to_event() + [
            Step(TD + "04_tasks_claim_21943.png", tap_at(330, 350, tol=6)),
            Step(TD + "05_donate_claimed.png", end()),
        ]
        settings = {"three_day_alliance": {"value": 60}, "three_day_heal": {"value": 0}}
        with mock.patch.object(run_module, "_claim_and_redeem", return_value=None):
            self._run(flow, settings)

    def test_group_not_active(self):
        """Bỏ tích group: không làm gì, return ngay."""
        run_flow(self, run_module.run, SCREENS, [Step(MAIN, end())],
                 {"three_day_active": {"enabled": False}})

    def test_done_today(self):
        """Đã xong hôm nay (daily_done): return ngay, không vào game."""
        run_flow(self, run_module.run, SCREENS, [Step(MAIN, end())], OFF,
                 daily_done={c.DONE_KEY: "2026-10-06T09:00:00"})


if __name__ == "__main__":
    unittest.main()
