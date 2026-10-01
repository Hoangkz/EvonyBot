"""
Flow test Event / Gather Troops / Defense Force (xây bẫy)
(bot/activities/event/gather_troops/defense_force/, flow chung ở ../train_troop/): giống
Siege Machine (Day 4) nhưng tab phụ bên phải "Defense Force", xưởng bẫy (Trap Factory, menu
có "Build" thay "Train"), màn "Trap Building Speedup", cấp thấp nhất 3 và mỗi cấp có 4 loại
bẫy liền nhau trên hàng (Trap, Rock, Abatis, Fire Arrow — loại nào cũng được).

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704. 01..04, 06, 07 và
speedup_settings* chép từ siege_machine/screens/.
- train_<cấp>_<loại>.png: tài khoản A (mở tới VII, chỉ Abatis VII khoá), vòng ở giữa là
  <cấp>_<loại>.
- b_*.png: tài khoản B (mở tới cấp III trừ Fire Arrow III; cấp IV trở lên khoá).
"""
import unittest
from pathlib import Path

import cv2

from bot.activities import event
from bot.activities.event.gather_troops import defense_force
from bot.activities.event.gather_troops.defense_force.constants import LOCKED_KEY
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
KEY = defense_force.KEY
SETTINGS = {KEY: {"value": 7000, "level": 6, "day": 4}}

LOGIN_GIFT_ICON = (361, 148)
LOGIN_REWARD = (122, 587)
EVENT_BUTTON = (369, 281)

FIRST_GO = (335, 344)          # nút Go gần tab Defense Force nhất (dòng "0 / 1,000")
CENTER = (198, 352)            # giữa màn hình: xưởng bẫy sau khi bấm Go
DF = "Event/GatherTroops/DefenseForce"
TRAIN_DIR = "Event/GatherTroops/Train"
TRAIN_BUTTON = f"{TRAIN_DIR}/trainButton.png"
TIER_Y = 452

TO_EVENT = [
    Step("03_main.png?claimed", tap_at(*EVENT_BUTTON)),
    Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
]
# Gather Troops (Day 1) -> Day 4 (mở ở tab Siege Machine) -> tab Defense Force -> Go đầu tiên
# -> xưởng bẫy -> menu "Build" -> màn Train (Rock VI ở giữa, mở) -> bấm Train (hết kịch bản).
TO_FIRST_GO = [
    Step("07_gather_day1.png", tap("Event/GatherTroops/SiegeMachine/day4.png")),
    Step("08_day4_siege_machine.png", tap(f"{DF}/defenseForce.png")),
    Step("09_day4_defense_force.png", tap_at(*FIRST_GO)),
    Step("10_after_go.png", tap_at(*CENTER)),
    Step("11_build_menu.png", tap(f"{DF}/build.png")),
    Step("train_6_rock.png", tap(TRAIN_BUTTON)),
]


def _blank(y0, y1, x0, x1):
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


def _training(bgr):
    """Biến thể ảnh: dán đáy màn Train đang xây (ảnh thật b_training.png: "Training Troops"
    thay thanh kéo / nút "+", nút "Training Speedup" thay nút Train)."""
    real = cv2.imread(str(SCREENS / "b_training.png"))
    bgr[560:] = real[560:]
    return bgr


VARIANTS = {
    "claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    "no_go": _blank(320, 704, 290, 380),
    "training": _training,
}


class DefenseForceFlow(unittest.TestCase):
    def test_main_flow(self):
        """Nhận quà đăng nhập, Event Center -> Gather Troops -> Day 4 -> tab Defense Force ->
        OCR "0 / 1,000" -> Go -> xưởng bẫy -> Build -> Rock VI (cấp 6 mở) -> Train."""
        flow = [
            Step("01_main_login_gift.png", tap_at(*LOGIN_GIFT_ICON)),
            Step("02_login_gifts.png", tap_at(*LOGIN_REWARD), back()),
            Step("03_main.png", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap("Event/GatherTroops/icon.png")),
            *TO_FIRST_GO,
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertNotIn(LOCKED_KEY, device.daily_done)
        self.assertIn("Defense Force: done 0, remaining 7000", device.logs)
        self.assertIn("Defense Force: train tier 6 (chosen 6), goal 7000, count 7000", device.logs)
        self.assertIn("Defense Force: 13102 per batch -> 1 batch(es)", device.logs)

    def test_defense_tab_already_selected(self):
        """Day 4 đang ở tab Defense Force: bấm Go luôn."""
        flow = [*TO_EVENT, *TO_FIRST_GO[2:4]]
        run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_day4_locked_saved(self):
        """2 ổ khoá trên hàng tab Day (Day 4, 5 khoá): lưu LOCKED_KEY rồi dừng."""
        flow = [*TO_EVENT, Step("06_day_locked_tmp.png", end())]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn(LOCKED_KEY, device.daily_done)

    def _train_flow(self, settings, *train_steps, flow_to_menu=None):
        """Tới màn Train rồi các bước chọn cấp `train_steps`."""
        flow = [*TO_EVENT, *(flow_to_menu or TO_FIRST_GO[:-1]), *train_steps]
        device = run_flow(self, event.run, SCREENS, flow, settings, variants=VARIANTS)
        # Không bao giờ bấm "Instant Train" (tốn gems), nút trái đáy màn Train.
        instant = [(i, e) for i, e in device.events
                   if e[0] == "tap" and flow[i].screen.startswith(("train_", "b_"))
                   and e[1] < 190 and e[2] > 640]
        self.assertEqual(instant, [], "bấm vào Instant Train")
        return device

    def test_walk_down_four_kinds_per_level(self):
        """Mở ở Rock VII, chọn cấp 3: bấm vòng trái nhất (lùi 2 vòng mỗi lần, qua từng loại
        bẫy) tới khi thấy một vòng cấp III (Fire Arrow III) -> bấm nó -> mở -> train cấp 3."""
        settings = {KEY: {"value": 1000, "level": 3, "day": 4}}
        device = self._train_flow(
            settings,
            Step("train_7_rock.png", tap_at(26, TIER_Y)),         # Fire Arrow VI
            Step("train_6_fireArrow.png", tap_at(26, TIER_Y)),    # Rock VI
            Step("train_6_rock.png", tap_at(24, TIER_Y)),         # Fire Arrow V
            Step("train_5_fireArrow.png", tap_at(23, TIER_Y)),    # Rock V
            Step("train_5_rock.png", tap_at(22, TIER_Y)),         # Fire Arrow IV
            Step("train_4_fireArrow.png", tap_at(20, TIER_Y)),    # Rock IV
            Step("train_4_rock.png", tap_at(20, TIER_Y)),         # Fire Arrow III (cấp 3)
            Step("train_3_fireArrow.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Defense Force: train tier 3 (chosen 3), goal 1000, count 1000", device.logs)

    def test_level_visible_taps_nearest_kind(self):
        """Fire Arrow III ở giữa, chọn cấp 4: thấy Trap IV, Rock IV -> bấm Trap IV (gần giữa
        nhất) -> mở -> train cấp 4."""
        settings = {KEY: {"value": 3000, "level": 4, "day": 4}}
        device = self._train_flow(
            settings,
            Step("train_3_fireArrow.png", tap_at(279, TIER_Y)),
            Step("train_4_trap.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Defense Force: train tier 4 (chosen 4), goal 3000, count 3000", device.logs)

    def test_locked_per_kind_falls_back_to_lower_level(self):
        """Tài khoản B, chọn cấp 4. Rock IV ở giữa khoá (không có "+"), Trap IV / Abatis IV có
        ổ khoá, Fire Arrow IV chưa biết -> bấm Fire Arrow IV -> cũng khoá -> cả 4 loại cấp IV
        khoá -> cấp 3: lùi (bấm vòng trái nhất) tới loại cấp III còn mở -> train cấp 3, mục
        tiêu theo event.json. (Bước cuối dùng ảnh Abatis III ở giữa thay cho Fire Arrow III.)"""
        settings = {KEY: {"value": 3000, "level": 4, "day": 4}}
        device = self._train_flow(
            settings,
            Step("b_locked_4_rock.png", tap_at(367, TIER_Y)),        # Fire Arrow IV
            Step("b_locked_4_fireArrow.png", tap_at(20, TIER_Y)),    # Rock IV
            Step("b_locked_4_rock.png", tap_at(20, TIER_Y)),         # Fire Arrow III (khoá)
            Step("b_train_3_abatis.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Defense Force: train tier 3 (chosen 4), goal 2000, count 2000", device.logs)
        self.assertNotIn(LOCKED_KEY, device.daily_done)

    def test_existing_building_finished_first(self):
        """Ảnh thật: vừa vào màn Train đã có mẻ bẫy đang xây (nút "Training Speedup") ->
        màn "Trap Building Speedup" -> Finish All trước (không tính) -> chọn cấp, Train."""
        settings = {KEY: {"value": 1000, "level": 3, "day": 4}}
        device = self._train_flow(
            settings,
            Step("b_training.png", tap(f"{TRAIN_DIR}/trainingSpeedup.png")),
            Step("speedup_trap.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup_trap.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("b_train_3_abatis.png", tap(TRAIN_BUTTON)),
        )
        self.assertIn("Defense Force: troops already training, finishing them first (not counted)",
                      device.logs)
        self.assertIn("Defense Force: Train batch 1/1", device.logs)

    def test_train_speedup_finish_all(self):
        """Cấp 6, mỗi lần tối đa 13102 (OCR) -> 7000 bẫy cần 1 lần: Train -> Training
        Speedup -> Trap Building Speedup: Speedup Settings, tích ô, Confirm -> Finish All."""
        device = self._train_flow(
            SETTINGS,
            Step("train_6_rock.png", tap(TRAIN_BUTTON)),
            Step("train_6_rock.png?training", tap(f"{TRAIN_DIR}/trainingSpeedup.png")),
            Step("speedup_trap.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings.png", tap(f"{TRAIN_DIR}/checkboxOff.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup_trap.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("train_6_rock.png", end()),
        )
        self.assertIn(KEY, device.daily_done)

    def test_building_busy_speed_up_from_menu(self):
        """Sau Go, xưởng bẫy đang xây (menu có "Speed Up", không có Build; icon "View" khớp
        nhầm ảnh Train 0,95) -> Speed Up -> Trap Building Speedup -> Finish All -> về thành
        -> bấm giữa lần nữa -> menu có Build -> Build."""
        flow = [
            *TO_EVENT, *TO_FIRST_GO[:4],
            Step("11_speed_up_menu.png", tap(f"{TRAIN_DIR}/speedUp.png")),
            Step("speedup_trap.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step("speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step("speedup_trap.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step("10_after_go.png", tap_at(*CENTER)),
            *TO_FIRST_GO[4:],
        ]
        device = run_flow(self, event.run, SCREENS, flow, SETTINGS, variants=VARIANTS)
        self.assertIn("Defense Force: building already training, Speed Up from menu (not counted)",
                      device.logs)

    def test_no_go_marks_done(self):
        flow = [*TO_EVENT, Step("09_day4_defense_force.png?no_go", end())]
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
