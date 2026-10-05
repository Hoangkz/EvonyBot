"""
Flow test Daily Activities / Trap Building (bot/activities/daily_activities/trap_building/), luồng mới `after_go`
(../train.py train_after_go, giống Gather Troops Defense Force): về thành, Trap Factory ở giữa -> menu "Build" -> bẫy
đang hiện khi vào (không chọn loại / cấp) -> số mặc định mỗi mẻ -> ceil(150 / số mỗi mẻ) mẻ -> mỗi mẻ Build -> Trap
Building Speedup -> (lần đầu Speedup Settings) Finish All -> Back, xong hôm nay. Thêm phần mở nhiệm vụ
(open_task_or_finish, giao diện CŨ): thẻ Trap Building "Completed" -> xong hôm nay, không bấm Go.

Ảnh dùng chung, không chép (ảnh chụp nguyên màn hình giả lập 396x704): 10_after_go, 11_*, train_6_rock, b_training,
speedup_* ở tests/event/gather_troops/defense_force/screens/ (train_6_rock: Rock VI, 13102 mỗi mẻ); 30 ở
tests/daily_activities/screens/ (thẻ Trap Building "Completed", máy 21943).
"""
import unittest

import cv2

from bot.activities.daily_activities.common import open_task_or_finish
from bot.activities.daily_activities.trap_building.constants import LABEL
from bot.activities.daily_activities.trap_building.run import TASK, after_go
from tests.daily_activities import GATHER, OLD_GRID_VARIANTS, TESTS_DIR, old_grid_completed
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = TESTS_DIR
DF = f"{GATHER}defense_force/screens/"
CENTER = (198, 352)   # giữa màn hình: Trap Factory sau khi bấm Go
TRAIN_DIR = "Event/GatherTroops/Train"
TRAIN_BUTTON = f"{TRAIN_DIR}/trainButton.png"
TO_BUILD = [
    Step(f"{DF}10_after_go.png", tap_at(*CENTER)),
    Step(f"{DF}11_build_menu.png", tap("Event/GatherTroops/DefenseForce/build.png")),
]
# Mẻ vừa bấm Build -> Training Speedup -> Trap Building Speedup: Speedup Settings -> tích ô -> Confirm -> Finish All.
FINISH_FIRST = [
    Step(f"{DF}train_6_rock.png?training", tap(f"{TRAIN_DIR}/trainingSpeedup.png")),
    Step(f"{DF}speedup_trap.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
    Step(f"{DF}speedup_settings.png", tap(f"{TRAIN_DIR}/checkboxOff.png")),
    Step(f"{DF}speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
    Step(f"{DF}speedup_trap.png", tap(f"{TRAIN_DIR}/finishAll.png")),
]


def _training(bgr):
    """Biến thể ảnh: dán đáy màn Train đang xây (ảnh thật b_training.png: nút "Training Speedup" thay nút Train)."""
    real = cv2.imread(str(SCREENS / DF / "b_training.png"))
    bgr[560:] = real[560:]
    return bgr


VARIANTS = {"training": _training}


def _after_go(bot, _settings):
    return after_go(bot)


class TrapBuildingFlow(unittest.TestCase):
    def test_after_go_one_batch(self):
        """13102 bẫy mỗi mẻ (OCR) >= 150 -> 1 mẻ: Build -> Finish All -> nút Build hiện lại -> Back, xong hôm nay.
        Không chọn loại / cấp, không nhập số."""
        flow = [
            *TO_BUILD,
            Step(f"{DF}train_6_rock.png", tap(TRAIN_BUTTON)),
            *FINISH_FIRST,
            Step(f"{DF}train_6_rock.png", back()),
            Step(f"{DF}10_after_go.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {}, variants=VARIANTS)
        self.assertIn(f"{LABEL}: 13102 per batch -> 1 batch(es)", device.logs)
        self.assertIn(LABEL, device.daily_done)
        self.assertFalse([c for c in device.shells if c.startswith("input text")])

    def test_building_busy_speed_up_from_menu(self):
        """Trap Factory đang xây (menu có "Speed Up"): Speed Up -> Finish All mẻ đó (không tính) -> mở lại menu ->
        Build -> 1 mẻ -> xong."""
        flow = [
            Step(f"{DF}10_after_go.png", tap_at(*CENTER)),
            Step(f"{DF}11_speed_up_menu.png", tap(f"{TRAIN_DIR}/speedUp.png")),
            Step(f"{DF}speedup_trap.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step(f"{DF}speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step(f"{DF}speedup_trap.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            *TO_BUILD,
            Step(f"{DF}train_6_rock.png", tap(TRAIN_BUTTON)),
            Step(f"{DF}train_6_rock.png?training", tap(f"{TRAIN_DIR}/trainingSpeedup.png")),
            Step(f"{DF}speedup_trap.png", tap(f"{TRAIN_DIR}/finishAll.png")),   # Speedup Settings đã làm
            Step(f"{DF}train_6_rock.png", back()),
            Step(f"{DF}10_after_go.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {}, variants=VARIANTS)
        self.assertIn(f"{LABEL}: building busy, Speed Up from menu (not counted)", device.logs)
        self.assertIn(LABEL, device.daily_done)

    def test_existing_batch_finished_first(self):
        """Vào màn Train đã có mẻ đang xây (b_training): Finish All mẻ đó trước rồi mới Build mẻ của nhiệm vụ."""
        flow = [
            *TO_BUILD,
            Step(f"{DF}b_training.png", tap(f"{TRAIN_DIR}/trainingSpeedup.png")),
            Step(f"{DF}speedup_trap.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step(f"{DF}speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step(f"{DF}speedup_trap.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step(f"{DF}train_6_rock.png", tap(TRAIN_BUTTON)),
            Step(f"{DF}train_6_rock.png?training", tap(f"{TRAIN_DIR}/trainingSpeedup.png")),
            Step(f"{DF}speedup_trap.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step(f"{DF}train_6_rock.png", back()),
            Step(f"{DF}10_after_go.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, SCREENS, flow, {}, variants=VARIANTS)
        self.assertIn(f"{LABEL}: Train batch 1/1", device.logs)
        self.assertIn(LABEL, device.daily_done)

    def test_open_task_completed_card(self):
        """Giao diện cũ: lưới Activity -> cuộn -> thẻ Trap Building "Completed" -> xong hôm nay, không bấm Go."""
        flow = old_grid_completed("30_old_grid_end_trap_completed.png", "no_trap")
        device = run_flow(self, lambda bot, _s: open_task_or_finish(bot, TASK), SCREENS, flow, {}, variants=OLD_GRID_VARIANTS)
        self.assertIn(LABEL, device.daily_done)


if __name__ == "__main__":
    unittest.main()
