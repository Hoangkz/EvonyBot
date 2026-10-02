"""
Flow test Event / Gather Troops / Siege Machine
(bot/activities/event/gather_troops/siege_machine/, flow chung ở ../train_troop/): giống hệt
Mounted Troop, nhưng Day 4, tab phụ bên trái "Siege Machine" (mặc định; bên phải "Defense
Force"), xưởng (Workshop) và ảnh cấp xe công thành.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704. 01..04, 06, 07_gather_day1 và
speedup* chép từ tests/event/gather_troops/mounted_troop/screens/. train_t<c>.png: tài khoản
mở tới cấp XIII (XIV khoá), cấp c đang ở giữa. 06_day_locked_tmp.png (King's Path, Day 4 +
Day 5 khoá) là ảnh thật đúng trường hợp Day 4 khoá (2 ổ khoá).

locked_*.png: tài khoản chỉ mở tới cấp IV.

10_after_go.png / 11_train_menu.png: xưởng (Workshop) trước / sau khi bấm giữa màn hình.
11_speed_up_menu.png: menu xưởng khi đang có mẻ train (Speed Up, không có Train; icon "View"
khớp nhầm ảnh Train 0,92). speedup_workshop.png: màn Training Speedup mở từ menu đó.
12_after_finish_all.png: về lại thành sau Finish All (thông báo "finished training").
"""
import unittest
from pathlib import Path

import cv2

from bot.activities import event
from bot.activities.event.gather_troops import siege_machine
from bot.activities.event.gather_troops.siege_machine.constants import LOCKED_KEY
from tests.flow import Step, back, end, run_flow, tap, tap_at
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)

SCREENS = Path(__file__).parent / "screens"
KEY = siege_machine.KEY
SETTINGS = {KEY: {"value": 20000, "level": 13, "day": 4}}

LOGIN_GIFT_ICON = (361, 148)   # icon Login Gifts ở cột phải
LOGIN_REWARD = (37, 197)       # hộp quà dưới chữ "Login Gifts" (56, 141) + (-19, 56)
EVENT_BUTTON = (361, 280)   # nút event: đuôi ruy băng cột phải (331, 308) + (30, -28)

FIRST_GO = (335, 344)          # nút Go gần tab Siege Machine nhất (dòng "0 / 500")
CENTER = (198, 352)            # giữa màn hình: xưởng sau khi bấm Go
SM = "Event/GatherTroops/SiegeMachine"
TRAIN_DIR = "Event/GatherTroops/Train"
TRAIN_BUTTON = f"{TRAIN_DIR}/trainButton.png"
TRAINING_SPEEDUP = (295, 668)

TO_EVENT = [
    Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
    Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
]
# Gather Troops (Day 1) -> Day 4 (mở ở tab Siege Machine) -> Go đầu tiên -> xưởng -> menu
# Train -> màn Train (XIII ở giữa) -> bấm Train (hết kịch bản: Stop).
TO_FIRST_GO = [
    Step("07_gather_day1.png", tap(f"{SM}/day4.png")),
    Step("08_day4_siege_machine.png", tap_at(*FIRST_GO)),
    Step("10_after_go.png", tap_at(*CENTER)),
    Step("11_train_menu.png", tap(f"{TRAIN_DIR}/train.png")),
    Step("train_t13.png", tap(TRAIN_BUTTON)),
]

# Tâm vòng tròn cấp lính (x) trên train_t<c>.png: cấp c-2..c+2.
TIER_Y = 452
TIER_X = {6: [18, 106, 192, 281, 363], 7: [20, 106, 195, 278, 367], 8: [20, 110, 192, 281, 369],
          9: [24, 106, 195, 283, 371], 10: [21, 110, 198, 285, 369], 11: [24, 112, 199, 283, 373],
          12: [27, 114, 198, 288, 371], 13: [28, 112, 202, 285, 372]}


def tier_at(center: int, tier: int):
    """tap_at vòng tròn cấp `tier` trên màn Train đang chọn cấp `center`."""
    return tap_at(TIER_X[center][tier - center + 2], TIER_Y)


def _blank(y0, y1, x0, x1):
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


def _training(bgr):
    """Biến thể ảnh: dán đáy màn Train đang train (ảnh thật train_training.png: dòng "Training
    Troops" thay thanh kéo / nút "+", nút "Training Speedup" thay nút Train)."""
    real = cv2.imread(str(SCREENS / "train_training.png"))
    bgr[560:] = real[560:]
    return bgr


VARIANTS = {
    "claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    "no_go": _blank(320, 704, 290, 380),
    "training": _training,
}


class SiegeMachineFlow(unittest.TestCase):
    def test_main_flow(self):
        """Nhận quà đăng nhập, Event Center -> Gather Troops -> Day 4 -> Siege Machine (tab
        mặc định) -> OCR "0 / 500" -> Go -> xưởng -> Train -> cấp XIII -> Train."""
        flow = [
            Step("01_main_login_gift.png", tap_at(*LOGIN_GIFT_ICON)),
            Step("02_login_gifts.png", tap_at(*LOGIN_REWARD), back()),
            Step("03_main.png", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
            *TO_FIRST_GO,
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertNotIn(LOCKED_KEY, device.daily_done)
        self.assertIn("Siege Machine: done 0, remaining 20000", device.logs)
        self.assertIn("Siege Machine: train tier 13 (chosen 13), goal 20000, count 20000",
                      device.logs)

    def test_from_day3_opens_day4(self):
        """Gather Troops đang ở Day 3: bấm tab Day 4 (Day 3 đang chọn không làm nhầm)."""
        flow = [
            *TO_EVENT,
            Step("07_gather_day3.png", tap(f"{SM}/day4.png")),
            *TO_FIRST_GO[1:3],
        ]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_defense_tab_selected_opens_siege(self):
        """Day 4 đang ở tab phụ Defense Force: bấm tab Siege Machine rồi mới Go."""
        flow = [
            *TO_EVENT,
            Step("09_day4_defense_force.png", tap(f"{SM}/siegeMachine.png")),
            *TO_FIRST_GO[1:3],
        ]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_day4_locked_saved(self):
        """2 ổ khoá trên hàng tab Day (Day 4, 5 khoá): lưu LOCKED_KEY rồi dừng."""
        flow = [*TO_EVENT, Step("06_day_locked_tmp.png", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(LOCKED_KEY, device.daily_done)

    def _train_flow(self, settings, *train_steps):
        """Tới màn Train rồi các bước chọn cấp `train_steps`."""
        flow = [*TO_EVENT, *TO_FIRST_GO[:-1], *train_steps]
        device = run_flow(self, event.run, SCREENS, flow, settings, variants=VARIANTS)
        # Không bao giờ bấm "Instant Train" (tốn gems), nút trái đáy màn Train.
        instant = [(i, e) for i, e in device.events
                   if e[0] == "tap" and flow[i].screen.startswith(("train_t", "locked_"))
                   and e[1] < 190 and e[2] > 640]
        self.assertEqual(instant, [], "bấm vào Instant Train")
        return device

    def test_tier_walk_up_to_chosen(self):
        """Màn Train mở ở cấp 6, chọn 13: bấm cấp phải nhất (8, 10, 12 ra giữa) rồi XIII."""
        device = self._train_flow(
            SETTINGS,
            Step("train_t06.png", tier_at(6, 8)),
            Step("train_t08.png", tier_at(8, 10)),
            Step("train_t10.png", tier_at(10, 12)),
            Step("train_t12.png", tier_at(12, 13)),
            Step("train_t13.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Siege Machine: train tier 13 (chosen 13), goal 20000, count 20000",
                      device.logs)

    def test_tier_walk_down_from_higher(self):
        """Màn Train mở ở cấp 13 (XIV khoá), chọn 7: đi xuống (bấm cấp trái nhất)."""
        settings = {KEY: {"value": 500, "level": 7, "day": 4}}
        device = self._train_flow(
            settings,
            Step("train_t13.png", tier_at(13, 11)),
            Step("train_t11.png", tier_at(11, 9)),
            Step("train_t09.png", tier_at(9, 7)),
            Step("train_t07.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Siege Machine: train tier 7 (chosen 7), goal 500, count 500", device.logs)

    def test_train_speedup_finish_all(self):
        """Cấp 13, mỗi lần train tối đa 20812 (OCR) -> 20000 lính cần 1 lần: Train ->
        Training Speedup -> Speedup Settings, tích ô, Confirm -> Finish All -> xong."""
        device = self._train_flow(
            SETTINGS,
            Step("train_t13.png", tap(TRAIN_BUTTON)),
            Step("train_t13.png?training", tap_at(*TRAINING_SPEEDUP)),
            Step("speedup.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings.png", tap(f"{TRAIN_DIR}/checkboxOff.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("train_t13.png", end()),
        )
        self.assertIn("Siege Machine: 20812 per batch -> 1 batch(es)", device.logs)
        self.assertIn(KEY, device.daily_done)

    def test_existing_training_finished_first(self):
        """Ảnh thật: vừa vào màn Train đã có mẻ đang train (nút "Training Speedup", không có
        nút "+"). Phải Finish All mẻ đó trước (không tính), không được coi cấp ở giữa là khoá;
        về màn Train mới chọn cấp và bấm Train (lần 1/1)."""
        device = self._train_flow(
            SETTINGS,
            Step("train_training.png", tap(f"{TRAIN_DIR}/trainingSpeedup.png")),
            Step("speedup.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("train_t13.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Siege Machine: troops already training, finishing them first (not counted)",
                      device.logs)
        self.assertIn("Siege Machine: Train batch 1/1", device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_open_only_to_4_saved_locked(self):
        """Tài khoản chỉ mở tới cấp IV (ảnh thật): màn mở ở I..IV -> bấm IV (phải nhất) ->
        IV ra giữa, thấy V, VI khoá -> cấp 7 khoá -> lưu LOCKED_KEY."""
        device = self._train_flow(
            SETTINGS,
            Step("locked_201311.png", tap_at(300, TIER_Y)),   # IV
            Step("locked_201315.png", end()),
        )
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_all_locked_walks_down_to_7(self):
        """Mở ở XIV, mọi cấp đang thấy (XII..XVI) khoá: bấm cấp trái nhất để đi xuống (XII,
        X, VIII lần lượt ra giữa) tới khi thấy VI khoá -> lưu LOCKED_KEY."""
        device = self._train_flow(
            SETTINGS,
            Step("locked_201352.png", tap_at(27, TIER_Y)),    # XII
            Step("locked_201343.png", tap_at(27, TIER_Y)),    # X
            Step("locked_201333.png", tap_at(21, TIER_Y)),    # VIII
            Step("locked_201328.png", end()),                 # VI..X khoá
        )
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_building_busy_speed_up_from_menu(self):
        """Sau Go, xưởng đang có mẻ train: menu có "Speed Up" (không có Train; không bấm
        "View" dù nó khớp ảnh Train) -> màn Training Speedup -> Speedup Settings, Confirm ->
        Finish All -> về lại thành -> bấm giữa màn hình lần nữa -> menu có Train -> Train."""
        flow = [
            *TO_EVENT, *TO_FIRST_GO[:3],
            Step("11_speed_up_menu.png", tap(f"{TRAIN_DIR}/speedUp.png")),
            Step("speedup_workshop.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup_workshop.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("12_after_finish_all.png", tap_at(*CENTER)),
            *TO_FIRST_GO[3:],
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn("Siege Machine: building already training, Speed Up from menu (not counted)",
                      device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_no_go_marks_done(self):
        """Tab Siege Machine không còn Go: đánh dấu xong."""
        flow = [*TO_EVENT, Step("08_day4_siege_machine.png?no_go", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(KEY, device.daily_done)

    def test_already_done_skips(self):
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, daily_done={KEY: "2026-10-01T08:00:00"})

    def test_disabled_skips(self):
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, {KEY: {"value": 0, "level": None, "day": 4}})


if __name__ == "__main__":
    unittest.main()
