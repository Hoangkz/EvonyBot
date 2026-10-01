"""Flow giữ bubble trên ảnh chụp thật (skill flow-test)."""
import unittest
from pathlib import Path

from bot.common.bubble import BUFF_ICON, CONFIRM, TRUCE, keep_bubble
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
CITY_BUFF_TIME = 6 * 3600 + 55 * 60 + 22    # city_buff_time.png: 06:55:22
AFTER_USE = 7 * 3600 + 57 * 60 + 10         # use_item_after.png: 07:57:10
CITY_BUFF_DAYS = 2 * 86400 + 23 * 3600 + 38 * 60   # city_buff_days.png: 2d 23:38


def run(ctx, settings):
    return keep_bubble(ctx, settings["type"], settings["renew"])


class KeepBubbleFlowTests(unittest.TestCase):
    def test_enough_time_reads_and_leaves(self):
        flow = [
            Step("home.png", tap(BUFF_ICON)),
            Step("city_buff_time.png", back(), end(CITY_BUFF_TIME)),
        ]
        run_flow(self, run, SCREENS, flow, {"type": "24h", "renew": 3600})

    def test_days_format(self):
        # Từ 1 ngày trở lên game hiện "2d 23:38" (không có giây).
        flow = [
            Step("home.png", tap(BUFF_ICON)),
            Step("city_buff_days.png", back(), end(CITY_BUFF_DAYS)),
        ]
        run_flow(self, run, SCREENS, flow, {"type": "3d", "renew": 3600})

    def test_renew_8h_replaces_active_bubble(self):
        # renew lớn hơn 06:55:22 -> phải dùng bubble mới.
        flow = [
            Step("home.png", tap(BUFF_ICON)),
            Step("city_buff_time.png", tap(TRUCE)),
            Step("use_item_time.png", tap_at(333, 213)),     # nút Use dòng 8h
            Step("confirm_replace.png", tap(CONFIRM)),
            Step("confirm_use_8h.png", tap(CONFIRM)),
            Step("use_item_after.png", back(2), end(AFTER_USE)),
        ]
        run_flow(self, run, SCREENS, flow, {"type": "8h", "renew": 25000})

    def test_buy_3d_with_gems(self):
        flow = [
            Step("home.png", tap(BUFF_ICON)),
            Step("city_buff_time.png", tap(TRUCE)),
            Step("use_item_time.png", tap_at(333, 453)),     # nút kim cương dòng 3d
            Step("confirm_replace.png", tap(CONFIRM)),
            Step("confirm_buy_3d.png", tap(CONFIRM)),
            Step("use_item_after.png", back(2), end(AFTER_USE)),
        ]
        run_flow(self, run, SCREENS, flow, {"type": "3d", "renew": 25000})

    def test_new_time_unreadable_falls_back_to_duration(self):
        # Sau khi dùng vẫn thấy thời gian cũ (<= renew) -> đọc lại 3 lần rồi tính theo loại.
        flow = [
            Step("home.png", tap(BUFF_ICON)),
            Step("city_buff_time.png", tap(TRUCE)),
            Step("use_item_time.png", tap_at(333, 337)),     # nút Use dòng 24h
            Step("confirm_use_24h.png", tap(CONFIRM)),
            Step("use_item_time.png", back(2), end(24 * 3600)),
        ]
        run_flow(self, run, SCREENS, flow, {"type": "24h", "renew": 25000})

    def test_no_bubble_goes_to_use_item(self):
        flow = [
            Step("home.png", tap(BUFF_ICON)),
            Step("city_buff.png", tap(TRUCE)),
            Step("use_item_time.png", tap_at(333, 213)),
            Step("confirm_use_8h.png", tap(CONFIRM)),
            Step("use_item_after.png", back(2), end(AFTER_USE)),
        ]
        run_flow(self, run, SCREENS, flow, {"type": "8h", "renew": 3600})


if __name__ == "__main__":
    unittest.main()
