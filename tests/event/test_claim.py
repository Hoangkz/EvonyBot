"""
Test nhận thưởng theo chấm đỏ + rương mốc (bot/activities/event/claim.py), chạy sau khi xong
các nhiệm vụ của một event. Ảnh King's Path dùng chung tests/event/kings_path/screens/; ảnh
Gather Troops / rương mốc ở tests/event/claim_screens/ (396x704).
"""
import unittest
from pathlib import Path
from unittest import mock

import cv2

from bot.activities import event
from bot.activities.event import claim
from bot.activities.event.claim import claim_key, red_dots
from bot.activities.event.constants import CLAIM_ALL, DOT_DAY_Y, DOT_TAB_Y, GATHER_CHESTS, KINGS_PATH_ICON
from bot.activities.event.gather_troops import cultivate_generals
from bot.activities.event.kings_path import wheel
from bot.ocr import read_milestone
from tests.event import MAYBE_CLAIM
from tests.flow import Step, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "kings_path" / "screens"
GATHER = Path(__file__).parent / "gather_troops" / "ground_troop" / "screens"
CLAIM_SCREENS = Path(__file__).parent / "claim_screens"
EVENT_BUTTON = (369, 281)   # chữ "Event Center" (359, 241) + (10, 40)
SETTINGS = {wheel.KEY: {"value": 100, "day": 4}}
DONE = {wheel.KEY: "2026-10-02T08:00:00"}   # Wheel đã xong hôm nay -> King's Path có 1 nhiệm vụ xong


def _blank(y0, y1, x0, x1):
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


_NO_CLAIM_ALL = _blank(655, 695, 140, 256)
VARIANTS = {
    "main_claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    "claimed": _NO_CLAIM_ALL,
    # Đã nhận hết: không Claim All, không chấm đỏ trên hàng Day / tab phụ.
    "no_dots": lambda bgr: _blank(DOT_TAB_Y - 9, DOT_TAB_Y + 9, 0, 396)(
        _blank(DOT_DAY_Y - 9, DOT_DAY_Y + 9, 0, 396)(_NO_CLAIM_ALL(bgr))),
}


def _run(testcase, flow, daily_done):
    with mock.patch.object(claim, "maybe_claim", MAYBE_CLAIM):
        return run_flow(testcase, event.run, SCREENS, flow, SETTINGS, daily_done=daily_done,
                        variants=VARIANTS)


class RedDots(unittest.TestCase):
    def test_kings_path(self):
        screen = cv2.imread(str(SCREENS / "day2_teamwork.png"))
        self.assertEqual(red_dots(screen, DOT_DAY_Y), [77, 153, 228])
        self.assertEqual(red_dots(screen, DOT_TAB_Y), [128, 253])

    def test_gather_troops(self):
        screen = cv2.imread(str(GATHER / "07_gather_day1.png"))
        self.assertEqual(red_dots(screen, DOT_DAY_Y), [77])
        self.assertEqual(red_dots(screen, DOT_TAB_Y), [379])

    def test_no_dots(self):
        screen = cv2.imread(str(SCREENS / "day4_fortune_wheel.png"))
        self.assertEqual(red_dots(screen, DOT_TAB_Y), [])


class Milestone(unittest.TestCase):
    def test_read_progress(self):
        """OCR dòng "Progress:12 / 70" / "Progress:6 / 70" (MILESTONE_BOX)."""
        cases = [("gather_chest_10.png", 12), ("07_gather_day1.png", 6),
                 ("gather_chest_claimed.png", 12)]   # chữ tối hơn (băng Congratulations)
        cases += [(f"gather_progress_{n}.png", n) for n in range(13, 20)]   # đủ chữ số 0..9
        for name, done in cases:
            screen = cv2.imread(str(CLAIM_SCREENS / name))
            self.assertEqual(read_milestone(screen[121:135, 100:260], total=70), done, name)
            self.assertIsNone(read_milestone(screen[121:135, 100:260], total=99), name)


class Chests(unittest.TestCase):
    def test_claim_reached_chests(self):
        """Progress 15 / 70, rương 5 và 10 chưa nhận (chưa có dấu tích): bấm rương 5 rồi 10,
        không bấm rương 30."""
        flow = [
            Step("gather_progress_15.png", tap_at(70, 83)),
            Step("gather_progress_15.png", tap_at(122, 83), end()),
        ]
        device = run_flow(self, lambda bot, _: claim._claim_chests(bot, "Gather Troops", GATHER_CHESTS),
                          CLAIM_SCREENS, flow, {})
        self.assertIn("Gather Troops: claim chest 10 (progress 15)", device.logs)


class ClaimFlow(unittest.TestCase):
    def test_claim_red_dots(self):
        """King's Path có 1 nhiệm vụ xong: mở King's Path -> tab phụ có chấm (Unstoppable) ->
        Claim All -> tab phụ có chấm kế (Try Your Best) -> hết chấm tab phụ -> Day có chấm (Day 1)
        -> tab City Tax có chấm -> Claim All -> hết chấm -> xong, lưu đã nhận."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day2_teamwork.png?claimed", tap_at(103, 249)),
            Step("day2_unstoppable.png", tap(CLAIM_ALL)),
            Step("day2_unstoppable.png?claimed", tap_at(228, 249)),
            Step("day2_teamwork.png?claimed", tap_at(52, 205)),
            Step("day1_city_tax.png?claimed", tap_at(103, 249)),
            Step("day1_city_tax.png", tap(CLAIM_ALL)),
            Step("day1_city_tax.png?no_dots", end()),
        ]
        device = _run(self, flow, DONE)
        self.assertIn(claim_key("kings_path", 1), device.daily_done)

    def test_gather_chests(self):
        """Gather Troops có 1 nhiệm vụ xong: mở Gather Troops -> không còn chấm đỏ -> Progress 12:
        rương 5 đã tích (bỏ qua), bấm rương 10, rương 30 chưa tới mốc -> xong."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
            Step("gather_chest_10.png", tap_at(122, 83)),
            # Băng "Congratulations!" (rương 10 đã tích) -> chờ mất rồi mới xét tiếp.
            Step("gather_chest_claimed.png", end()),
        ]
        with mock.patch.object(claim, "maybe_claim", MAYBE_CLAIM):
            device = run_flow(self, event.run, CLAIM_SCREENS, flow,
                              {cultivate_generals.KEY: {"enabled": True, "day": 1}},
                              daily_done={cultivate_generals.KEY: "2026-10-02T08:00:00"},
                              variants=VARIANTS)
        self.assertIn("Gather Troops: claim chest 10 (progress 12)", device.logs)
        self.assertIn(claim_key("gather_troops", 1), device.daily_done)

    def test_already_claimed(self):
        """Đã nhận ứng với 1 nhiệm vụ xong: không mở lại event."""
        flow = [Step("03_main.png", end())]
        _run(self, flow, {**DONE, claim_key("kings_path", 1): "2026-10-02T08:05:00"})

    def test_no_task_done(self):
        """Không nhiệm vụ nào bật / xong: không mở event để nhận."""
        flow = [Step("03_main.png", end())]
        with mock.patch.object(claim, "maybe_claim", MAYBE_CLAIM):
            device = run_flow(self, event.run, SCREENS, flow, {})
        self.assertFalse(device.daily_done)


if __name__ == "__main__":
    unittest.main()
