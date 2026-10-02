"""
Flow test Event / King's Path (bot/activities/event/kings_path/): phần trên màn King's Path
— kiểm Day khoá -> tab Day -> tab phụ -> dòng Go của nhiệm vụ -> đọc tiến độ -> bấm Go.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (Day 5 đang khoá).

test_open_from_main đi đủ từ màn chính (03_main chép từ test Ground Troop); các test khác bắt
đầu ngay ở màn King's Path.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

import cv2

from bot.activities import event
from bot.activities.event.constants import CLAIM_ALL, KINGS_PATH_ICON
from bot.activities.event.kings_path import city_tax, donate, heal, patrol, path_task, train_troop, wheel
from bot.activities.event.kings_path.city_tax.constants import POPUP_TAX, TAX_MENU
from bot.activities.event.kings_path.city_tax.run import split_counts
from bot.activities.event.kings_path.donate.constants import DONATE_BUTTON, GEMS_BUTTON, OKAY
from bot.activities.event.kings_path.wheel.constants import SPINS_10, SPINS_100
from tests.flow import Step, back, end, run_flow, tap, tap_at, tap_pct

SCREENS = Path(__file__).parent / "screens"
KP = "Event/KingsPath"
EVENT_BUTTON = (369, 281)   # chữ "Event Center" (359, 241) + (10, 40), xem test Gather Troops


def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng."""
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


def _paste_go_row(bgr):
    """Dán dòng "0 / 1,000" + nút Go (dòng đầu, y 290..375) của ảnh Day 3 vào ảnh City Tax
    (dòng nào cũng đang Claim) và xoá Claim All -> tab còn dòng Go, đã làm 0."""
    src = cv2.imread(str(SCREENS / "day3_healing_heart.png"))
    bgr[290:375, 260:385] = src[290:375, 260:385]
    return _blank(655, 695, 140, 256)(bgr)


VARIANTS = {
    # Màn chính đã nhận quà: không còn icon Login Gifts (cột phải + góc dưới trái).
    "main_claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    # Dòng đầu có nút Go "0 / ..." (ảnh tổng hợp, xem _paste_go_row): City Tax, Strong Troops.
    "go": _paste_go_row,
    # Đã bấm Claim All: xoá nút Claim All ở đáy màn.
    "claimed": _blank(655, 695, 140, 256),
    # Màn event cùng khung nhưng không phải King's Path (VD Gather Troops): xoá tiêu đề.
    "not_kp": _blank(5, 40, 120, 280),
}


def _run(testcase, flow, settings, **kw):
    return run_flow(testcase, event.run, SCREENS, flow, settings, variants=VARIANTS, **kw)


class KingsPathFlow(unittest.TestCase):
    def test_open_from_main(self):
        """Màn chính -> nút dưới Event Center -> danh sách event (đã cuộn, King's Path ở dưới)
        -> icon King's Path -> màn King's Path Day 4 -> tab Fortune Wheel đang chọn -> Go."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertIn(wheel.KEY, device.daily_done)

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
        """Tab Teamwork: dòng "Donate to the Alliance" (0 / 10) -> Go -> Alliance Science:
        Donate 2 lần -> hết lượt (nút kim cương) -> Okay -> Donate lần 3 -> xong (mục tiêu 3)."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 567)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_gems.png", tap(GEMS_BUTTON)),
            Step("donate_confirm_gems.png", tap(OKAY)),
            Step("donate_science.png", tap(DONATE_BUTTON), end()),
        ]
        device = _run(self, flow, {donate.KEY: {"value": 3, "day": 2}})
        self.assertIn("Donate: done 0, target 3", device.logs)
        self.assertIn(donate.KEY, device.daily_done)

    def test_donate_gem_limit(self):
        """Đã mua lại lượt đủ MAX_GEM_BUYS lần mà vẫn hết lượt: dừng, không đánh dấu xong."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 567)),
            Step("donate_gems.png", end()),
        ]
        with mock.patch.object(sys.modules["bot.activities.event.kings_path.donate.run"],
                               "MAX_GEM_BUYS", 0):
            device = _run(self, flow, {donate.KEY: {"value": 60, "day": 2}})
        self.assertNotIn(donate.KEY, device.daily_done)

    def test_city_tax(self):
        """Day 1 City Tax: đọc 0 / ... -> Go -> bấm giữa thành -> icon Tax -> màn Tax: chia
        110 thành 28, 28, 27, 27 -> mỗi dòng Tax -> popup gõ số -> Tax -> xong."""
        rows = [284, 383, 482, 581]
        flow = [
            Step("day1_city_tax.png?go", tap_at(335, 344)),
            Step("tax_city.png", tap_pct(50, 50)),
            Step("tax_menu.png", tap(TAX_MENU)),
        ]
        for y in rows:
            flow += [
                Step("tax_screen.png", tap_at(308, y)),
                Step("tax_popup.png", tap_at(198, 300), tap(POPUP_TAX)),
            ]
        flow.append(Step("tax_screen.png", end()))
        device = _run(self, flow, {city_tax.KEY: {"value": 110, "day": 1}})
        texts = [c for c in device.shells if c.startswith("input text")]
        self.assertEqual(texts, ["input text 28", "input text 28", "input text 27", "input text 27"])
        self.assertIn(city_tax.KEY, device.daily_done)

    def test_train_troop(self):
        """Day 3 -> tab Strong Troops -> Go (0 / ...) -> doanh trại -> menu Train -> màn Train:
        bấm vòng cấp I (sát mép trái) -> 2000 lính / 1580 mỗi mẻ = 2 mẻ -> Train."""
        flow = [
            Step("day3_healing_heart.png", tap(f"{KP}/Tab/strongTroops.png")),
            Step("day3_strong_troops.png?go", tap_at(335, 344)),
            Step("train_after_go.png", tap_at(198, 352)),
            Step("train_menu.png", tap("Event/GatherTroops/Train/train.png")),
            Step("train_t01.png", tap("Event/GatherTroops/GroundTroop/Tier/1.png")),
            Step("train_t01.png", tap("Event/GatherTroops/Train/trainButton.png")),
        ]
        device = _run(self, flow, {train_troop.KEY: {"value": 2000, "day": 3}})
        self.assertIn("Train Troop: 1580 per batch -> 2 batch(es)", device.logs)

    def test_split_counts(self):
        self.assertEqual(split_counts(110), [28, 28, 27, 27])
        self.assertEqual(split_counts(3), [1, 1, 1, 0])
        self.assertEqual(split_counts(0), [0, 0, 0, 0])

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

    def test_day_locked(self):
        """Ngày của nhiệm vụ còn khoá (Day 5): lưu "chưa thể thực hiện", không bấm gì."""
        flow = [Step("day4_fortune_wheel.png", end())]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 5}})
        self.assertIn(f"{wheel.KEY}_locked", device.daily_done)
        self.assertNotIn(wheel.KEY, device.daily_done)

    def test_not_kings_path_backs(self):
        """Hàng tab Day giống Gather Troops: không thấy tiêu đề King's Path -> Back."""
        flow = [
            Step("day3_healing_heart.png?not_kp", back()),
            Step("day3_healing_heart.png", tap_at(335, 344), end()),
        ]
        _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})

    def test_no_icon_skips(self):
        """Chưa có ảnh icon King's Path: bỏ qua nhiệm vụ, không bấm gì."""
        flow = [Step("day4_fortune_wheel.png", end())]
        with mock.patch.object(path_task, "KINGS_PATH_ICON", f"{KP}/missing.png"):
            run_flow(self, event.run, SCREENS, flow, {wheel.KEY: {"value": 100, "day": 4}})


if __name__ == "__main__":
    unittest.main()
