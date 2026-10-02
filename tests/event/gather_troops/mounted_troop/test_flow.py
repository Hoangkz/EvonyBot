"""
Flow test Event / Gather Troops / Mounted Troop
(bot/activities/event/gather_troops/mounted_troop/, flow chung ở ../train_troop/): giống hệt
Ground Troop, chỉ khác tab Day 3, tab phụ "Mounted Troop", chuồng ngựa (Stables) và ảnh
cấp lính kỵ.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704. 01..04, 06 và speedup*
chép từ tests/event/gather_troops/ground_troop/screens/ (màn Training Speedup dùng chung).
train_t<c>.png: tài khoản mở tới cấp XIII (XIV khoá), cấp c đang ở giữa. locked_*.png: tài
khoản chỉ mở cấp I.

TODO: 06_day_locked_tmp.png là ảnh TẠM (màn King's Path, Day 4 + Day 5 khoá) — thay bằng
ảnh Gather Troops thật có Day 3..5 khoá rồi bỏ biến thể "day3_locked".
"""
import unittest
from pathlib import Path

import cv2

from bot.activities import event
from bot.activities.event.constants import DAY_LOCK
from bot.activities.event.gather_troops import mounted_troop
from bot.activities.event.gather_troops.mounted_troop.constants import LOCKED_KEY
from bot.context import TEMPLATE_DIR
from tests.flow import Step, back, end, run_flow, tap, tap_at
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)

SCREENS = Path(__file__).parent / "screens"
KEY = mounted_troop.KEY
SETTINGS = {KEY: {"value": 20000, "level": 13, "day": 3}}

LOGIN_GIFT_ICON = (361, 148)   # icon Login Gifts ở cột phải
LOGIN_REWARD = (37, 197)       # hộp quà dưới chữ "Login Gifts" (56, 141) + (-19, 56)
EVENT_BUTTON = (361, 280)   # nút event: đuôi ruy băng cột phải (331, 308) + (30, -28)
# Tâm ổ khoá trên tab Day 3 (Day 4 (250, 209), Day 5 (326, 209), cách nhau 76).
DAY_3_LOCK = (174, 209)

FIRST_GO = (335, 344)          # nút Go gần tab Mounted Troop nhất (dòng "0 / 500")
CENTER = (198, 352)            # giữa màn hình: chuồng ngựa sau khi bấm Go
MT = "Event/GatherTroops/MountedTroop"
TRAIN_DIR = "Event/GatherTroops/Train"
TRAIN_BUTTON = f"{TRAIN_DIR}/trainButton.png"
TRAINING_SPEEDUP = (295, 668)  # nút "Training Speedup" (cùng chỗ nút Train) khi đang train

TO_EVENT = [
    Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
    Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
]
# Gather Troops (Day 1) -> Day 3 (mở ở tab phụ Mounted Troop) -> Go đầu tiên -> chuồng ngựa
# -> menu Train -> màn Train (XIII ở giữa, không khoá) -> bấm Train (hết kịch bản: Stop).
TO_FIRST_GO = [
    Step("07_gather_day1.png", tap(f"{MT}/day3.png")),
    Step("08_day3_mounted_troop.png", tap_at(*FIRST_GO)),
    Step("10_after_go.png", tap_at(*CENTER)),
    Step("11_train_menu.png", tap(f"{TRAIN_DIR}/train.png")),
    Step("train_t13.png", tap(TRAIN_BUTTON)),
]

# Tâm vòng tròn cấp lính (x) trên train_t<c>.png: cấp c-2..c+2.
TIER_Y = 452
TIER_X = {7: [26, 106, 196, 280, 368], 8: [24, 111, 196, 282, 370], 9: [22, 110, 197, 283, 370],
          10: [24, 113, 199, 286, 371], 11: [26, 111, 198, 286, 370], 12: [27, 115, 199, 287, 375],
          13: [26, 113, 203, 288, 372]}


def tier_at(center: int, tier: int):
    """tap_at vòng tròn cấp `tier` trên màn Train đang chọn cấp `center`."""
    return tap_at(TIER_X[center][tier - center + 2], TIER_Y)


def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng (xoá nút / icon chưa có ảnh chụp thật)."""
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


def _day345_locked(bgr):
    """Biến thể ảnh: dán ổ khoá lên tab Day 3, 4, 5 (3 ổ khoá -> Day 3..5 khoá)."""
    for x in (DAY_3_LOCK[0], DAY_3_LOCK[0] + 76, DAY_3_LOCK[0] + 152):
        lock = cv2.imread(str(TEMPLATE_DIR / DAY_LOCK))
        h, w = lock.shape[:2]
        y = DAY_3_LOCK[1]
        bgr[y - h // 2:y - h // 2 + h, x - w // 2:x - w // 2 + w] = lock
    return bgr


VARIANTS = {
    "day345_locked": _day345_locked,
    "claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    "day3_locked": _day3_locked,
    "no_go": _blank(320, 704, 290, 380),
    "training": _training,
}


class MountedTroopFlow(unittest.TestCase):
    def test_main_flow(self):
        """Nhận quà đăng nhập, Event Center -> Gather Troops -> Day 3 -> Mounted Troop (tab
        mặc định) -> OCR "0 / 500" -> Go -> chuồng ngựa -> Train -> cấp XIII -> Train."""
        flow = [
            Step("01_main_login_gift.png", tap_at(*LOGIN_GIFT_ICON)),
            Step("02_login_gifts.png", tap_at(*LOGIN_REWARD), back()),
            Step("03_main.png", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
            *TO_FIRST_GO,
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertNotIn(LOCKED_KEY, device.daily_done)
        self.assertIn("Mounted Troop: done 0, remaining 20000", device.logs)
        self.assertIn("Mounted Troop: train tier 13 (chosen 13), goal 20000, count 20000",
                      device.logs)

    def test_ranged_tab_selected_opens_mounted(self):
        """Day 3 đang ở tab phụ Ranged Troop: bấm tab Mounted Troop rồi mới Go."""
        flow = [
            *TO_EVENT,
            Step("09_day3_ranged_troop.png", tap(f"{MT}/mountedTroop.png")),
            *TO_FIRST_GO[1:3],
        ]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_day3_locked_saved(self):
        """3 ổ khoá trên hàng tab Day (Day 3..5 khoá): lưu LOCKED_KEY rồi dừng."""
        flow = [*TO_EVENT, Step("06_day_locked_tmp.png?day3_locked", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_later_days_locked_day3_open(self):
        """Chỉ Day 4, Day 5 khoá (2 ổ khoá): Day 3 đã mở, không lưu LOCKED_KEY (ảnh tạm
        King's Path có "Claim All" nên bước kế là bấm Claim All)."""
        flow = [*TO_EVENT, Step("06_day_locked_tmp.png", tap("Event/claimAll.png"))]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

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
        """Màn Train mở ở cấp 7, chọn 13: bấm cấp phải nhất (9, 11, 13 lần lượt ra giữa)."""
        device = self._train_flow(
            SETTINGS,
            Step("train_t07.png", tier_at(7, 9)),
            Step("train_t09.png", tier_at(9, 11)),
            Step("train_t11.png", tier_at(11, 13)),
            Step("train_t13.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Mounted Troop: train tier 13 (chosen 13), goal 20000, count 20000",
                      device.logs)

    def test_tier_stops_at_chosen_level(self):
        """Chọn cấp 10 (5000): thấy X thì bấm X, không đi tiếp."""
        settings = {KEY: {"value": 5000, "level": 10, "day": 3}}
        device = self._train_flow(
            settings,
            Step("train_t07.png", tier_at(7, 9)),
            Step("train_t09.png", tier_at(9, 10)),
            Step("train_t10.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Mounted Troop: train tier 10 (chosen 10), goal 5000, count 5000",
                      device.logs)

    def test_tier_walk_down_from_higher(self):
        """Màn Train mở ở cấp 13 (XIV khoá), chọn 7: đi xuống (bấm cấp trái nhất)."""
        settings = {KEY: {"value": 500, "level": 7, "day": 3}}
        device = self._train_flow(
            settings,
            Step("train_t13.png", tier_at(13, 11)),
            Step("train_t11.png", tier_at(11, 9)),
            Step("train_t09.png", tier_at(9, 7)),
            Step("train_t07.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Mounted Troop: train tier 7 (chosen 7), goal 500, count 500", device.logs)

    def test_train_speedup_finish_all(self):
        """Cấp 13, mỗi lần train tối đa 40785 (OCR) -> 20000 lính cần 1 lần: Train ->
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
        self.assertIn("Mounted Troop: 40785 per batch -> 1 batch(es)", device.logs)
        self.assertIn(KEY, device.daily_done)

    def test_tier_7_locked_saved(self):
        """Tài khoản chỉ mở cấp I (ảnh thật: I ở giữa, II..IV khoá): lưu LOCKED_KEY."""
        device = self._train_flow(SETTINGS, Step("locked_175430.png", end()))
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_all_locked_walks_down_to_7(self):
        """Mọi cấp đang thấy (X..XIII) đều khoá: bấm cấp trái nhất để đi xuống (X, rồi IX)
        tới khi thấy VII khoá -> lưu LOCKED_KEY."""
        device = self._train_flow(
            SETTINGS,
            Step("locked_175511.png", tap_at(54, TIER_Y)),    # X
            Step("locked_175459.png", tap_at(43, TIER_Y)),    # IX
            Step("locked_175449.png", end()),                 # VI..IX khoá
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
        self.assertIn("Mounted Troop: troops already training, finishing them first (not counted)",
                      device.logs)
        self.assertIn("Mounted Troop: Train batch 1/1", device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_building_busy_speed_up_from_menu(self):
        """Sau Go, chuồng ngựa đang có mẻ train (ảnh thật 11_speed_up_menu.png: menu có "Speed
        Up", không có Train; icon "View" khớp nhầm ảnh Train) -> Speed Up -> màn Training
        Speedup (speedup_stables.png) -> Speedup Settings, Confirm -> Finish All -> về lại thành (dùng lại
        10_after_go.png) -> bấm giữa lần nữa -> menu có Train -> Train."""
        flow = [
            *TO_EVENT, *TO_FIRST_GO[:3],
            Step("11_speed_up_menu.png", tap(f"{TRAIN_DIR}/speedUp.png")),
            Step("speedup_stables.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup_stables.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("10_after_go.png", tap_at(*CENTER)),
            *TO_FIRST_GO[3:],
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn("Mounted Troop: building already training, Speed Up from menu (not counted)",
                      device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_started_on_train_screen_goes_back_to_event(self):
        """Bắt đầu khi đang ở màn Train (VD nhiệm vụ trước dừng ở đó): chưa mở event / chưa
        bấm Go của Mounted Troop trong lượt này -> Back, đi lại từ màn chính qua Gather
        Troops (kiểm tra Day khoá, đọc số đã làm) rồi mới Go -> Train."""
        flow = [
            Step("train_t13.png", back()),
            *TO_EVENT,
            *TO_FIRST_GO,
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn("Mounted Troop: on_train_screen before Go, back", device.logs)
        self.assertIn("Mounted Troop: done 0, remaining 20000", device.logs)

    def test_started_on_gather_troops_continues_there(self):
        """Bắt đầu khi đang ở sẵn màn Gather Troops (Day 3, nhiệm vụ trước để lại): không về
        thành, kiểm tra Day khoá ngay trên màn đó rồi bấm Go luôn."""
        flow = [*TO_FIRST_GO[1:]]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn("Mounted Troop: done 0, remaining 20000", device.logs)

    def test_started_on_gather_troops_day_locked(self):
        """Đang ở sẵn màn Gather Troops mà Day 3 khoá: lưu LOCKED_KEY ngay, không về thành."""
        flow = [Step("08_day3_mounted_troop.png?day345_locked", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_no_go_marks_done(self):
        """Tab Mounted Troop không còn Go: đánh dấu xong."""
        flow = [*TO_EVENT, Step("08_day3_mounted_troop.png?no_go", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(KEY, device.daily_done)

    def test_already_done_skips(self):
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, daily_done={KEY: "2026-10-01T08:00:00"})

    def test_locked_skips_until_reset(self):
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, SETTINGS,
                 daily_done={LOCKED_KEY: "2026-10-01T08:00:00"})

    def test_disabled_skips(self):
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, {KEY: {"value": 0, "level": None, "day": 3}})


if __name__ == "__main__":
    unittest.main()
