"""
Flow test Event / Gather Troops / Ranged Troop
(bot/activities/event/gather_troops/ranged_troop/, flow chung ở ../train_troop/): giống hệt
Mounted Troop, cùng Day 3 nhưng tab phụ bên phải "Ranged Troop" (Day 3 mở mặc định ở tab
Mounted Troop nên phải bấm sang), trại cung (Archer Camp) và ảnh cấp lính cung.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704. 01..04, 06, 07 và speedup*
chép từ tests/event/gather_troops/mounted_troop/screens/. train_t<c>.png: tài khoản mở tới
cấp XIII (XIV khoá), cấp c đang ở giữa. locked_*.png: tài khoản chỉ mở tới cấp IV.
10_after_go.png / 11_train_menu.png: trại cung (Archer Camp) trước / sau khi bấm giữa màn hình.

TODO: 06_day_locked_tmp.png là ảnh tạm (King's Path) — thay bằng ảnh thật khi có.
"""
import unittest
from pathlib import Path

import cv2

from bot.activities import event
from bot.activities.event.constants import DAY_LOCK
from bot.activities.event.gather_troops import ranged_troop
from bot.activities.event.gather_troops.ranged_troop.constants import LOCKED_KEY
from bot.context import TEMPLATE_DIR
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
KEY = ranged_troop.KEY
SETTINGS = {KEY: {"value": 20000, "level": 13, "day": 3}}

LOGIN_GIFT_ICON = (361, 148)   # icon Login Gifts ở cột phải
LOGIN_REWARD = (37, 197)       # hộp quà dưới chữ "Login Gifts" (56, 141) + (-19, 56)
EVENT_BUTTON = (369, 281)      # chữ "Event Center" + (10, 40)
DAY_3_LOCK = (174, 209)        # tâm ổ khoá trên tab Day 3

FIRST_GO = (335, 344)          # nút Go gần tab Ranged Troop nhất (dòng "0 / 500")
CENTER = (198, 352)            # giữa màn hình: trại cung sau khi bấm Go
RT = "Event/GatherTroops/RangedTroop"
TRAIN_DIR = "Event/GatherTroops/Train"
TRAIN_BUTTON = f"{TRAIN_DIR}/trainButton.png"
TRAINING_SPEEDUP = (295, 668)

TO_EVENT = [
    Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
    Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
]
# Gather Troops (Day 1) -> Day 3 (mở ở tab Mounted Troop) -> tab Ranged Troop -> Go đầu tiên
# -> trại cung -> menu Train -> màn Train (XIII ở giữa) -> bấm Train (hết kịch bản: Stop).
TO_FIRST_GO = [
    Step("07_gather_day1.png", tap("Event/GatherTroops/MountedTroop/day3.png")),
    Step("08_day3_mounted_troop.png", tap(f"{RT}/rangedTroop.png")),
    Step("09_day3_ranged_troop.png", tap_at(*FIRST_GO)),
    Step("10_after_go.png", tap_at(*CENTER)),
    Step("11_train_menu.png", tap(f"{TRAIN_DIR}/train.png")),
    Step("train_t13.png", tap(TRAIN_BUTTON)),
]

# Tâm vòng tròn cấp lính (x) trên train_t<c>.png: cấp c-2..c+2.
TIER_Y = 452
TIER_X = {8: [21, 110, 198, 281, 368], 9: [24, 110, 199, 282, 368], 10: [25, 112, 199, 285, 371],
          11: [29, 113, 198, 284, 369], 12: [27, 114, 201, 287, 375], 13: [28, 116, 203, 289, 372]}


def tier_at(center: int, tier: int):
    """tap_at vòng tròn cấp `tier` trên màn Train đang chọn cấp `center`."""
    return tap_at(TIER_X[center][tier - center + 2], TIER_Y)


def _blank(y0, y1, x0, x1):
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


def _day3_locked(bgr):
    """Biến thể ảnh: dán thêm ổ khoá lên tab Day 3 -> 3 ổ khoá (Day 3..5 khoá)."""
    lock = cv2.imread(str(TEMPLATE_DIR / DAY_LOCK))
    h, w = lock.shape[:2]
    x, y = DAY_3_LOCK
    bgr[y - h // 2:y - h // 2 + h, x - w // 2:x - w // 2 + w] = lock
    return bgr


def _training(bgr):
    """Biến thể ảnh: dán đáy màn Train đang train (ảnh thật train_training.png: dòng "Training
    Troops" thay thanh kéo / nút "+", nút "Training Speedup" thay nút Train)."""
    real = cv2.imread(str(SCREENS / "train_training.png"))
    bgr[560:] = real[560:]
    return bgr


VARIANTS = {
    "claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    "day3_locked": _day3_locked,
    "no_go": _blank(320, 704, 290, 380),
    "training": _training,
}


class RangedTroopFlow(unittest.TestCase):
    def test_main_flow(self):
        """Nhận quà đăng nhập, Event Center -> Gather Troops -> Day 3 -> tab Ranged Troop ->
        OCR "0 / 500" -> Go -> trại cung -> Train -> cấp XIII -> Train."""
        flow = [
            Step("01_main_login_gift.png", tap_at(*LOGIN_GIFT_ICON)),
            Step("02_login_gifts.png", tap_at(*LOGIN_REWARD), back()),
            Step("03_main.png", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
            *TO_FIRST_GO,
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertNotIn(LOCKED_KEY, device.daily_done)
        self.assertIn("Ranged Troop: done 0, remaining 20000", device.logs)
        self.assertIn("Ranged Troop: train tier 13 (chosen 13), goal 20000, count 20000",
                      device.logs)

    def test_day3_locked_saved(self):
        """3 ổ khoá trên hàng tab Day (Day 3..5 khoá): lưu LOCKED_KEY rồi dừng."""
        flow = [*TO_EVENT, Step("06_day_locked_tmp.png?day3_locked", end())]
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
        """Màn Train mở ở cấp 8, chọn 13: bấm cấp phải nhất (10, 12 ra giữa) rồi XIII."""
        device = self._train_flow(
            SETTINGS,
            Step("train_t08.png", tier_at(8, 10)),
            Step("train_t10.png", tier_at(10, 12)),
            Step("train_t12.png", tier_at(12, 13)),
            Step("train_t13.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Ranged Troop: train tier 13 (chosen 13), goal 20000, count 20000",
                      device.logs)

    def test_tier_walk_down_from_higher(self):
        """Màn Train mở ở cấp 13 (XIV khoá), chọn 9: đi xuống (bấm cấp trái nhất) rồi IX."""
        settings = {KEY: {"value": 2000, "level": 9, "day": 3}}
        device = self._train_flow(
            settings,
            Step("train_t13.png", tier_at(13, 11)),
            Step("train_t11.png", tier_at(11, 9)),
            Step("train_t09.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Ranged Troop: train tier 9 (chosen 9), goal 2000, count 2000", device.logs)

    def test_train_speedup_finish_all(self):
        """Cấp 13, mỗi lần train tối đa 28266 (OCR) -> 20000 lính cần 1 lần: Train ->
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
        self.assertIn("Ranged Troop: 28266 per batch -> 1 batch(es)", device.logs)
        self.assertIn(KEY, device.daily_done)

    def test_open_only_to_4_saved_locked(self):
        """Tài khoản chỉ mở tới cấp IV (ảnh thật): màn mở ở I..IV -> bấm IV (phải nhất) ->
        IV ra giữa, thấy V, VI khoá -> cấp 7 khoá -> lưu LOCKED_KEY."""
        device = self._train_flow(
            SETTINGS,
            Step("locked_180037.png", tap_at(300, TIER_Y)),   # IV
            Step("locked_180045.png", end()),
        )
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_all_locked_walks_down_to_7(self):
        """Mở ở XIV, mọi cấp đang thấy (XII..XVI) khoá: bấm cấp trái nhất để đi xuống (XII,
        X, VIII lần lượt ra giữa) tới khi thấy VI khoá -> lưu LOCKED_KEY."""
        device = self._train_flow(
            SETTINGS,
            Step("locked_180117.png", tap_at(27, TIER_Y)),    # XII
            Step("locked_180112.png", tap_at(25, TIER_Y)),    # X
            Step("locked_180106.png", tap_at(23, TIER_Y)),    # VIII
            Step("locked_180100.png", end()),                 # VI..X khoá
        )
        self.assertIn(LOCKED_KEY, device.daily_done)

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
        self.assertIn("Ranged Troop: troops already training, finishing them first (not counted)",
                      device.logs)
        self.assertIn("Ranged Troop: Train batch 1/1", device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_building_busy_speed_up_from_menu(self):
        """Sau Go, trại cung đang có mẻ train (ảnh thật 11_speed_up_menu.png: menu có "Speed
        Up", không có Train; icon "View" khớp nhầm ảnh Train) -> Speed Up -> màn Training
        Speedup (speedup_archer_camp.png) -> Speedup Settings, Confirm -> Finish All -> về lại thành (dùng lại
        10_after_go.png) -> bấm giữa lần nữa -> menu có Train -> Train."""
        flow = [
            *TO_EVENT, *TO_FIRST_GO[:4],
            Step("11_speed_up_menu.png", tap(f"{TRAIN_DIR}/speedUp.png")),
            Step("speedup_archer_camp.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup_archer_camp.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("10_after_go.png", tap_at(*CENTER)),
            *TO_FIRST_GO[4:],
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn("Ranged Troop: building already training, Speed Up from menu (not counted)",
                      device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_no_go_marks_done(self):
        """Tab Ranged Troop không còn Go: đánh dấu xong."""
        flow = [*TO_EVENT, Step("09_day3_ranged_troop.png?no_go", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(KEY, device.daily_done)

    def test_already_done_skips(self):
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, daily_done={KEY: "2026-10-01T08:00:00"})

    def test_disabled_skips(self):
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, {KEY: {"value": 0, "level": None, "day": 3}})


if __name__ == "__main__":
    unittest.main()
