"""
Flow test nhiệm vụ Event Center "Viking Summon" (bot/activities/event_center/viking_summon).

Ảnh thật chụp trên giả lập (độ khó Easy đã xác nhận thật; các độ khó khác chỉ chọn rồi Cancel ở hộp thoại).
Chưa có ảnh đường đi tới icon "Viking Challenge" trong tab Activities (run_task dùng chung, đã test ở crazy_eggs): flow bắt đầu từ màn Viking.
Chia sẻ boss (_share_boss) được giả: đã chạy thật 1 lần, ra 407:686 (xem FLOW.md).
"""
import importlib
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from bot.activities.event_center.viking_summon import constants as c
from tests.flow import Step, run_flow, tap, tap_at

# `from .run import run` ở __init__ che tên module `run` bằng hàm: lấy module qua importlib.
viking = importlib.import_module("bot.activities.event_center.viking_summon.run")

SCREENS = Path(__file__).parent / "screens"
F = c.FOLDER
BADGE = {"Easy": (65, 385), "Hard": (243, 385)}


def _run(bot, settings):
    bot.server = "1835"
    return viking.run(bot, settings)


def _flow(testcase, flow, settings, **kwargs):
    with mock.patch.object(viking, "_share_boss", return_value="shared") as share:
        device = run_flow(testcase, _run, SCREENS, flow, settings, **kwargs)
    device.share = share
    return device


class VikingSummonFlow(unittest.TestCase):
    def test_select_easy_then_summon_and_share(self):
        """Màn chọn độ khó: bấm huy hiệu Easy -> Confirm -> hộp thoại "Select Easy level?" -> Confirm -> "Congratulations!" ->
        màn Summon -> Summon -> bản đồ, boss Viking ở giữa -> chia sẻ."""
        flow = [
            Step("02_difficulty_easy.png", tap_at(*BADGE["Easy"]), tap(c.CONFIRM)),
            Step("03_confirm_popup_easy.png", tap(c.POPUP_CONFIRM)),
            Step("05_congratulations.png", tap(c.CONGRATULATIONS)),
            Step("06_summon_screen.png", tap(c.SUMMON)),
            Step("09_viking_map_0.png", end_()),
        ]
        device = _flow(self, flow, {"viking_level": "Easy"})
        pos = device.share.call_args.args[1]
        self.assertTrue(abs(pos[0] - 190) < 20 and abs(pos[1] - 333) < 20, pos)

    def test_wrong_level_in_dialog_is_cancelled(self):
        """Muốn Hard mà hộp thoại hỏi Easy: Cancel (không xác nhận nhầm độ khó không đổi lại được), chọn lại Hard rồi mới Confirm."""
        flow = [
            Step("03_confirm_popup_easy.png", tap(c.POPUP_CANCEL)),
            Step("02_difficulty_hard.png", tap_at(*BADGE["Hard"]), tap(c.CONFIRM)),
            Step("03_confirm_popup_hard.png", tap(c.POPUP_CONFIRM)),
            Step("05_congratulations.png", tap(c.CONGRATULATIONS)),
        ]
        _flow(self, flow, {"viking_level": "Hard"})

    def test_level_dialog_not_shown_retries(self):
        """Bấm Confirm mà hộp thoại không hiện sau 5 lần chờ 1 giây: chọn lại từ đầu."""
        flow = [
            Step("02_difficulty_easy.png", tap_at(*BADGE["Easy"]), tap(c.CONFIRM)),
            Step("02_difficulty_easy.png", tap_at(*BADGE["Easy"]), tap(c.CONFIRM)),
            Step("03_confirm_popup_easy.png", tap(c.POPUP_CONFIRM)),
            Step("05_congratulations.png", tap(c.CONGRATULATIONS)),
        ]
        _flow(self, flow, {"viking_level": "Easy"})

    def test_level_already_chosen_goes_straight_to_summon(self):
        """Đã chọn độ khó ở lần trước: vào thẳng màn Summon, không chọn lại; độ khó khác yêu cầu (Easy, muốn Hell) chỉ ghi log."""
        flow = [
            Step("06_summon_screen.png", tap(c.SUMMON)),
            Step("09_viking_map_0.png", end_()),
        ]
        device = _flow(self, flow, {"viking_level": "Hell"})
        self.assertTrue(any("already uses level Easy" in line for line in device.logs))
        device.share.assert_called_once()

    def test_boss_still_alive_go_to_boss_and_share_again(self):
        """Boss chưa bị hạ: màn Viking có nút Go thay cho Summon -> bấm Go (về vị trí boss) -> chia sẻ lại ."""
        flow = [
            Step("10_live_end.png", tap(c.GO)),
            Step("09_viking_map_0.png", end_()),
        ]
        device = _flow(self, flow, {"viking_level": "Easy"})
        device.share.assert_called_once()
        self.assertTrue(any("still alive" in line for line in device.logs))

    def test_viking_nearest_to_center_is_shared(self):
        """Hai nhãn Viking trên bản đồ: chia sẻ cái gần giữa màn hình."""
        import cv2
        shot = cv2.imread(str(SCREENS / "09_viking_map_0.png"))
        far = shot.copy()
        far[480:530, 20:130] = shot[318:368, 170:280]   # nhãn Viking thứ hai ở góc dưới trái
        names = [(95, 495), (190, 333)]
        bot = mock.Mock()
        bot.screenshot.return_value = far
        bot.find_all.side_effect = lambda template, **kw: names if template == c.BOSS_NAME else []
        self.assertEqual(viking._find_viking(bot), (190, 333))


    def test_no_viking_label_taps_screen_center(self):
        """Không thấy nhãn Viking sau BOSS_NAME_TRIES lần kiểm tra (mỗi lần chờ 1 giây): bấm giữa màn hình, không bấm sớm hơn."""
        import numpy as np
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), np.uint8)
        bot.find_all.return_value = []
        self.assertEqual(viking._find_viking(bot), (198, 352))
        self.assertEqual(bot.sleep.call_count, c.BOSS_NAME_TRIES)


class WindowTests(unittest.TestCase):
    def test_window_monday_to_thursday_at_reset(self):
        """Từ 14:00 thứ 2 tới 14:00 thứ 5 (giờ reset)."""
        monday = datetime(2026, 10, 26)
        self.assertFalse(viking.in_window(monday.replace(hour=13, minute=59), "14:00"))
        self.assertTrue(viking.in_window(monday.replace(hour=14), "14:00"))
        self.assertTrue(viking.in_window(monday + timedelta(days=2, hours=23), "14:00"))   # thứ 4 23:00
        self.assertTrue(viking.in_window(monday + timedelta(days=3, hours=13, minutes=59), "14:00"))
        self.assertFalse(viking.in_window(monday + timedelta(days=3, hours=14), "14:00"))   # thứ 5 14:00
        self.assertFalse(viking.in_window(monday + timedelta(days=6, hours=20), "14:00"))   # chủ nhật

    def test_window_follows_reset_time(self):
        monday = datetime(2026, 10, 26)
        self.assertTrue(viking.in_window(monday.replace(hour=9), "08:30"))
        self.assertFalse(viking.in_window(monday.replace(hour=9), "14:00"))

    def test_due_needs_enabled_window_and_interval(self):
        ctx = mock.Mock(server_time=lambda: "14:00", done_at=lambda key: None)
        on, off = {"viking_summon": True}, {"viking_summon": False}
        with mock.patch.object(viking, "datetime", wraps=datetime) as clock:
            clock.now.return_value = datetime(2026, 10, 27, 10)   # thứ 3
            self.assertTrue(viking._due(ctx, on))
            self.assertFalse(viking._due(ctx, off))
            ctx.done_at = lambda key: (datetime(2026, 10, 27, 9, 55)).isoformat()
            self.assertFalse(viking._due(ctx, on))                # mới thử 5 phút trước
            ctx.done_at = lambda key: (datetime(2026, 10, 27, 9, 45)).isoformat()
            self.assertTrue(viking._due(ctx, on))
            clock.now.return_value = datetime(2026, 10, 31, 10)   # thứ 7: ngoài cửa sổ
            self.assertFalse(viking._due(ctx, on))


def end_():
    from tests.flow import end
    return end()


if __name__ == "__main__":
    unittest.main()
