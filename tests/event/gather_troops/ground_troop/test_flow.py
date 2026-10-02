"""
Flow test Event / Gather Troops / Ground Troop
(bot/activities/event/gather_troops/ground_troop/): quà đăng nhập -> nút dưới
Event Center -> danh sách event -> Gather Troops (giống hệt Cultivate Generals tới
05_gather_be_prepared.png) -> đếm ổ khoá trên hàng tab Day: Day 2 khoá (4 ổ khoá) thì
lưu "chưa thể thực hiện" và dừng.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (01..05 chép từ
tests/event/gather_troops/cultivate_generals/screens/).

TODO: 06_day_locked_tmp.png là ảnh TẠM (màn King's Path, Day 4 + Day 5 khoá) thay cho màn
Gather Troops có Day 2..5 khoá — thay bằng ảnh chụp thật rồi bỏ biến thể "day2_locked".
"""
import unittest
from pathlib import Path

import cv2

from bot.activities import event
from bot.activities.event.constants import DAY_LOCK
from bot.activities.event.gather_troops import ground_troop
from bot.activities.event.gather_troops.ground_troop.constants import LOCKED_KEY
from bot.activities.event.gather_troops.troop_tier import TIER_LOCK
from bot.context import TEMPLATE_DIR
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)

SCREENS = Path(__file__).parent / "screens"
KEY = ground_troop.KEY
SETTINGS = {KEY: {"value": 20000, "level": 13, "day": 2}}

# Toạ độ bấm cứng (lệch so với template, xem bot/activities/event/constants.py):
LOGIN_GIFT_ICON = (361, 148)   # icon Login Gifts ở cột phải (góc dưới trái cũng có)
LOGIN_REWARD = (37, 197)       # hộp quà dưới chữ "Login Gifts" (56, 141) + (-19, 56)
EVENT_BUTTON = (361, 280)   # nút event: đuôi ruy băng cột phải (331, 308) + (30, -28)
# Tâm ổ khoá trên tab Day 2 / Day 3 (Day 4 (250, 209), Day 5 (326, 209), cách nhau 76).
DAY_LOCKS = [(98, 209), (174, 209)]

FIRST_GO = (335, 344)          # nút Go gần tab Ground Troop nhất (dòng "0 / 500")
CENTER = (198, 352)            # giữa màn hình 396x704: doanh trại sau khi bấm Go
DAY_2 = "Event/GatherTroops/GroundTroop/day2.png"
TRAIN_DIR = "Event/GatherTroops/Train"
TRAIN_BUTTON = f"{TRAIN_DIR}/trainButton.png"
TRAINING_SPEEDUP = (295, 668)  # nút "Training Speedup" (cùng chỗ nút Train) khi đang train

# Màn chính -> Gather Troops vừa mở.
TO_EVENT = [
    Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
    Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
]
# Gather Troops (Day 1) -> Day 2 (tab Seize Time) -> tab Ground Troop -> Go đầu tiên.
TO_FIRST_GO = [
    Step("07_gather_day1.png", tap(DAY_2)),
    Step("08_day2_seize_time.png", tap("Event/GatherTroops/GroundTroop/groundTroop.png")),
    Step("09_day2_ground_troop.png", tap_at(*FIRST_GO)),
    # Sau Go (chờ 10 s): về thành, doanh trại ở giữa -> bấm giữa -> menu có icon Train.
    Step("10_after_go.png", tap_at(*CENTER)),
    Step("11_train_menu.png", tap("Event/GatherTroops/Train/train.png")),
    # Màn Train mở ở cấp train lần trước; XIII đang giữa, không khoá -> chọn 13, bấm Train
    # (hết kịch bản: harness bật Stop).
    Step("train_t13.png", tap(TRAIN_BUTTON)),
]

# Tâm vòng tròn cấp lính (x) trên màn Train đang chọn cấp c (train_t<c>.png): c-2..c+2.
TIER_Y = 452
TIER_X = {5: [20, 106, 192, 277, 367], 6: [21, 108, 195, 280, 368], 7: [21, 108, 196, 281, 368],
          8: [23, 109, 195, 281, 369], 9: [24, 110, 197, 286, 370], 10: [24, 112, 198, 284, 374],
          11: [24, 115, 199, 287, 372], 12: [27, 112, 200, 288, 375], 13: [28, 115, 201, 289, 375]}


def tier_at(center: int, tier: int):
    """tap_at vòng tròn cấp `tier` trên màn Train đang chọn cấp `center`."""
    return tap_at(TIER_X[center][tier - center + 2], TIER_Y)


def _tier_locks(center: int, *tiers: int):
    """Biến thể ảnh: dán ổ khoá (tierLock.png) lên các vòng tròn `tiers` của train_t<center>
    (chưa có ảnh thật của tài khoản bị khoá ở cấp 7..13)."""
    def fn(bgr):
        lock = cv2.imread(str(TEMPLATE_DIR / TIER_LOCK))
        h, w = lock.shape[:2]
        for tier in tiers:
            x, y = TIER_X[center][tier - center + 2] + 21, TIER_Y - 21   # góc trên phải
            x0, y0 = x - w // 2, y - h // 2
            part = bgr[y0:y0 + h, x0:x0 + w]
            bgr[y0:y0 + h, x0:x0 + w] = lock[:part.shape[0], :part.shape[1]]
        return bgr
    return fn


def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng (xoá nút / icon chưa có ảnh chụp thật)."""
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


def _day2_locked(bgr):
    """Biến thể ảnh: dán thêm ổ khoá lên tab Day 2, Day 3 -> 4 ổ khoá (Day 2..5 khoá)."""
    lock = cv2.imread(str(TEMPLATE_DIR / DAY_LOCK))
    h, w = lock.shape[:2]
    for x, y in DAY_LOCKS:
        bgr[y - h // 2:y - h // 2 + h, x - w // 2:x - w // 2 + w] = lock
    return bgr


def _training(bgr):
    """Biến thể ảnh: dán đáy màn Train đang train (ảnh thật train_training.png: dòng "Training
    Troops" thay thanh kéo / nút "+", nút "Training Speedup" thay nút Train)."""
    real = cv2.imread(str(SCREENS / "train_training.png"))
    bgr[560:] = real[560:]
    return bgr


VARIANTS = {
    # Màn chính đã nhận quà: không còn icon Login Gifts (cột phải + góc dưới trái).
    "claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    # Danh sách event không có Gather Troops.
    "no_gather_troops": _blank(330, 400, 15, 85),
    # TODO: bỏ khi có ảnh Gather Troops thật với Day 2..5 khoá.
    "day2_locked": _day2_locked,
    # Tab Ground Troop không còn nút Go nào (mọi dòng đã xong).
    "no_go": _blank(320, 704, 290, 380),
    # Màn Train: tài khoản chỉ mở tới cấp 11 (XII, XIII khoá) — chưa có ảnh thật.
    "locked_12": _tier_locks(11, 12, 13),
    # Màn Train: cấp ở giữa khoá (không có thanh kéo / nút "+"), các vòng khác không có ổ khoá.
    "center_locked": _blank(560, 600, 0, 396),
    # Màn Train đang train: đáy màn hình (nút "Training Speedup", không có nút "+") từ ảnh thật.
    "training": _training,
}


class GroundTroopFlow(unittest.TestCase):
    def test_main_flow(self):
        """Nhận quà đăng nhập trước, rồi Event Center -> danh sách event -> Gather Troops
        (không có ổ khoá: Day 2 đã mở) -> Day 2 -> Ground Troop -> OCR "0 / 500" -> Go đầu
        tiên."""
        flow = [
            Step("01_main_login_gift.png", tap_at(*LOGIN_GIFT_ICON)),
            Step("02_login_gifts.png", tap_at(*LOGIN_REWARD), back()),
            # 03_main vẫn còn icon Login Gifts nhưng quà đã nhận trong lượt này -> bỏ qua.
            Step("03_main.png", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
            *TO_FIRST_GO,
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertNotIn(LOCKED_KEY, device.daily_done)
        self.assertIn("Ground Troop: done 0, remaining 20000", device.logs)

    def test_day2_locked_saved(self):
        """4 ổ khoá trên hàng tab Day (Day 2..5 khoá): lưu LOCKED_KEY rồi dừng."""
        flow = [*TO_EVENT, Step("06_day_locked_tmp.png?day2_locked", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_later_days_locked_day2_open(self):
        """Chỉ Day 4, Day 5 khoá (2 ổ khoá): Day 2 đã mở, không lưu LOCKED_KEY, đi tiếp
        (ảnh tạm King's Path có "Claim All" nên bước kế là bấm Claim All; hết kịch bản
        harness bật Stop)."""
        flow = [*TO_EVENT, Step("06_day_locked_tmp.png", tap("Event/claimAll.png"))]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_go_waits_then_opens_barracks(self):
        """Bấm Go -> bấm giữa màn hình ngay sau đó (không thao tác nào khác xen giữa) ->
        thấy icon Train -> dừng (TODO). Thời gian chờ không kiểm ở đây (đồng hồ giả)."""
        flow = [*TO_EVENT, *TO_FIRST_GO]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        go = next(i for i, (_, e) in enumerate(device.events) if e[1:] == FIRST_GO)
        self.assertEqual(device.events[go + 1][1][1:], CENTER)

    def test_train_menu_not_shown_taps_again(self):
        """Bấm giữa lần 1 chưa hiện menu Train: chờ 3 s, bấm giữa thêm 1 lần, chờ 3 s,
        rồi vòng lặp kế tiếp thấy menu."""
        flow = [
            *TO_EVENT, *TO_FIRST_GO[:3],
            Step("10_after_go.png", tap_at(*CENTER)),
            *TO_FIRST_GO[3:],
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn("Ground Troop: Train menu not shown, tapping center again", device.logs)

    def _train_flow(self, settings, *train_steps):
        """Tới màn Train (mở ở cấp train lần trước) rồi các bước chọn cấp `train_steps`."""
        flow = [*TO_EVENT, *TO_FIRST_GO[:-1], *train_steps]
        device = run_flow(self, event.run, SCREENS, flow, settings, variants=VARIANTS)
        # Không bao giờ bấm "Instant Train" (tốn gems), nút trái đáy màn Train.
        instant = [(i, e) for i, e in device.events
                   if e[0] == "tap" and flow[i].screen.startswith(("train_t", "locked_"))
                   and e[1] < 190 and e[2] > 640]
        self.assertEqual(instant, [], "bấm vào Instant Train")
        return device

    def test_tier_walk_up_to_chosen(self):
        """Màn Train mở ở cấp 5, người dùng chọn 13: bấm cấp phải nhất (7, 9, 11, 13 lần lượt
        nhảy ra giữa) tới khi XIII ở giữa và không khoá -> train cấp 13, mục tiêu 20000."""
        device = self._train_flow(
            SETTINGS,
            Step("train_t05.png", tier_at(5, 7)),
            Step("train_t07.png", tier_at(7, 9)),
            Step("train_t09.png", tier_at(9, 11)),
            Step("train_t11.png", tier_at(11, 13)),
            Step("train_t13.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Ground Troop: train tier 13 (chosen 13), goal 20000, count 20000",
                      device.logs)

    def test_tier_stops_at_chosen_level(self):
        """Người dùng chọn cấp 10 (5000): không đi tới 13; thấy X (chưa khoá) thì bấm X."""
        settings = {KEY: {"value": 5000, "level": 10, "day": 2}}
        device = self._train_flow(
            settings,
            Step("train_t05.png", tier_at(5, 7)),
            Step("train_t07.png", tier_at(7, 9)),
            Step("train_t09.png", tier_at(9, 10)),
            Step("train_t10.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Ground Troop: train tier 10 (chosen 10), goal 5000, count 5000",
                      device.logs)

    def test_tier_walk_down_from_higher(self):
        """Màn Train mở ở cấp 13, người dùng chọn 7: đi xuống (bấm cấp trái nhất)."""
        settings = {KEY: {"value": 500, "level": 7, "day": 2}}
        device = self._train_flow(
            settings,
            Step("train_t13.png", tier_at(13, 11)),
            Step("train_t11.png", tier_at(11, 9)),
            Step("train_t09.png", tier_at(9, 7)),
            Step("train_t07.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Ground Troop: train tier 7 (chosen 7), goal 500, count 500", device.logs)

    def test_chosen_tier_locked_uses_highest_open(self):
        """Chọn 13 nhưng XII, XIII khoá: train cấp 11, mục tiêu theo event.json (10000)."""
        device = self._train_flow(SETTINGS, Step("train_t11.png?locked_12", tap(TRAIN_BUTTON)))
        self.assertIn("Ground Troop: train tier 11 (chosen 13), goal 10000, count 10000",
                      device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_train_speedup_finish_all(self):
        """Cấp 13, mỗi lần train tối đa 20812 (OCR) -> 20000 lính cần 1 lần. Bấm Train -> nút
        thành Training Speedup -> bấm -> màn speedup: lần đầu bấm Speedup Settings, tích ô
        góc dưới trái, Confirm -> Finish All -> về màn Train, đủ 1 lần -> đánh dấu xong."""
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
        self.assertIn("Ground Troop: 20812 per batch -> 1 batch(es)", device.logs)
        self.assertIn(KEY, device.daily_done)

    def test_existing_training_finished_not_counted(self):
        """Vừa vào màn Train đã có mẻ đang train (nút Training Speedup): bấm speedup, Finish
        All mẻ đó trước (không tính), về màn Train mới chọn cấp, tính 1 lần và bấm Train
        (lần 1/1, chưa đánh dấu xong)."""
        device = self._train_flow(
            SETTINGS,
            Step("train_t13.png?training", tap_at(*TRAINING_SPEEDUP)),
            Step("speedup.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("train_t13.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Ground Troop: troops already training, finishing them first (not counted)",
                      device.logs)
        self.assertIn("Ground Troop: Train batch 1/1", device.logs)
        self.assertNotIn(KEY, device.daily_done)

    def test_speedup_settings_already_ticked(self):
        """Hộp Finish All đã tích sẵn ô góc dưới trái: không bấm ô, bấm Confirm luôn."""
        device = self._train_flow(
            SETTINGS,
            Step("train_t13.png", tap(TRAIN_BUTTON)),
            Step("train_t13.png?training", tap_at(*TRAINING_SPEEDUP)),
            Step("speedup.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("train_t13.png", end()),
        )
        self.assertIn(KEY, device.daily_done)

    def test_tapped_tier_locked_checked_by_plus(self):
        """Mở ở cấp 9, chọn 13: bấm XI -> XI ra giữa nhưng không có nút "+" (khoá, không cần
        ổ khoá ở vòng tròn khác) -> lùi về X (mở) -> train 10, mục tiêu 5000."""
        device = self._train_flow(
            SETTINGS,
            Step("train_t09.png", tier_at(9, 11)),
            Step("train_t11.png?center_locked", tier_at(11, 10)),
            Step("train_t10.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Ground Troop: train tier 10 (chosen 13), goal 5000, count 5000",
                      device.logs)

    def test_tier_7_locked_saved(self):
        """Tài khoản chỉ mở cấp I (ảnh thật locked_*: cấp II trở lên khoá), màn Train mở ở
        cấp 7: VII khoá -> lưu "chưa thể thực hiện" (LOCKED_KEY) rồi dừng."""
        device = self._train_flow(SETTINGS, Step("locked_140711.png", end()))
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_all_locked_walks_down_to_7(self):
        """Màn Train mở ở cấp 12, mọi cấp đang thấy (X..XIV) đều khoá: bấm cấp trái nhất để
        đi xuống (X, rồi VIII) tới khi thấy VII khoá -> lưu LOCKED_KEY."""
        device = self._train_flow(
            SETTINGS,
            Step("locked_140736.png", tap_at(29, TIER_Y)),    # X
            Step("locked_140724.png", tap_at(24, TIER_Y)),    # VIII
            Step("locked_140715.png", end()),
        )
        self.assertIn(LOCKED_KEY, device.daily_done)

    def test_building_busy_speed_up_from_menu(self):
        """Sau Go, doanh trại đang có mẻ train (ảnh thật 11_speed_up_menu.png: menu có "Speed
        Up", không có Train; icon "View" khớp nhầm ảnh Train 0,84) -> Speed Up -> màn Training
        Speedup (speedup_barracks.png) -> Speedup Settings, Confirm -> Finish All -> về lại
        thành (dùng lại 10_after_go.png) -> bấm giữa lần nữa -> menu có Train -> Train."""
        flow = [
            *TO_EVENT, *TO_FIRST_GO[:4],
            Step("11_speed_up_menu.png", tap(f"{TRAIN_DIR}/speedUp.png")),
            Step("speedup_barracks.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup_barracks.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("10_after_go.png", tap_at(*CENTER)),
            *TO_FIRST_GO[4:],
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn("Ground Troop: building already training, Speed Up from menu (not counted)",
                      device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_no_go_marks_done(self):
        """Tab Ground Troop không còn Go: đánh dấu nhiệm vụ đã xong rồi kết thúc."""
        flow = [*TO_EVENT, Step("09_day2_ground_troop.png?no_go", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(KEY, device.daily_done)

    def test_already_done_skips(self):
        """Đã đánh dấu xong từ lần reset server gần nhất: không làm gì."""
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, daily_done={KEY: "2026-10-01T08:00:00"})

    def test_locked_skips_until_reset(self):
        """Đã lưu Day 2 khoá từ lần reset server gần nhất: không làm gì."""
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, SETTINGS,
                 daily_done={LOCKED_KEY: "2026-10-01T08:00:00"})

    def test_disabled_skips(self):
        """Ô Ground Troop chọn 0: không làm gì."""
        flow = [Step("03_main.png", end())]
        run_flow(self, event.run, SCREENS, flow, {KEY: {"value": 0, "level": None, "day": 2}})

    def test_gather_troops_not_found(self):
        """Danh sách event không có Gather Troops: cuộn xuống 4 lần rồi BACK, bỏ nhiệm vụ."""
        flow = [
            Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png?no_gather_troops",
                 *[swipe(50, 80, 50, 50) for _ in range(4)], back()),
            Step("03_main.png?claimed", end()),
        ]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)


if __name__ == "__main__":
    unittest.main()
