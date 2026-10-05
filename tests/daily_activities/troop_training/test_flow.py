"""
Flow test Daily Activities / Troop Training (bot/activities/daily_activities/troop_training/), phiên bản giao diện
mới: màn chính -> Quests -> tab Activity -> Claim All -> dòng "Train 300 troops in the Main City" đang là Claim
(đã làm xong) -> xong, không bấm Go. Giao diện cũ: thẻ Troop Training "Completed" -> xong, không bấm Go.
Luồng mới `after_go` (../train.py train_after_go, giống King's Path Train Troop): công trình train ở giữa -> menu
"Train" -> chọn cấp I (train_t01: đã ở cấp I, không bấm) -> số mặc định mỗi mẻ -> ceil(300 / số mỗi mẻ) mẻ -> mỗi mẻ Train -> Training Speedup ->
(lần đầu Speedup Settings) Finish All -> Back, xong hôm nay.

Ảnh chụp nguyên màn hình giả lập 396x704: 01..04 trong screens/ (chép từ tests/daily_activities/screens/); ảnh sau Go
dùng chung, không chép: train_after_go / train_menu / train_t01 (1580 mỗi mẻ) ở tests/event/kings_path/screens/,
speedup* / train_training ở tests/event/gather_troops/ground_troop/screens/, 28 ở tests/daily_activities/screens/.
"""
import unittest
from pathlib import Path

import cv2

from bot.activities.daily_activities import troop_training
from bot.activities.daily_activities.constants import TASK_DONE
from bot.activities.daily_activities.common import open_task_or_finish
from bot.activities.daily_activities.troop_training.constants import LABEL
from bot.activities.daily_activities.troop_training.run import after_go
from tests.daily_activities import (
    CLAIM_ALL_ONCE,
    GATHER,
    KP,
    TESTS_DIR,
    TO_ACTIVITY,
    old_grid_completed,
    open_task_of,
)
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
GROUND = f"{GATHER}ground_troop/screens/"
TRAIN_DIR = "Event/GatherTroops/Train"
TRAIN_BUTTON = f"{TRAIN_DIR}/trainButton.png"
BUILDING = (181, 333)   # công trình train trên train_after_go: nhận ra theo ảnh mẫu civ (không bấm đúng giữa)


def _training(bgr):
    """Biến thể ảnh: dán đáy màn Train đang train (ảnh thật train_training.png: nút "Training Speedup" thay nút
    Train)."""
    real = cv2.imread(str(TESTS_DIR / GROUND / "train_training.png"))
    bgr[560:] = real[560:]
    return bgr


VARIANTS = {"training": _training}


def _after_go(bot, _settings):
    return after_go(bot)


class TroopTrainingFlow(unittest.TestCase):
    def test_row_claimed_is_done(self):
        flow = [
            *TO_ACTIVITY, *CLAIM_ALL_ONCE,
            Step("03_activity_top.png", end(result=TASK_DONE)),
        ]
        run_flow(self, open_task_of(troop_training.TASK), SCREENS, flow, {})

    def test_open_task_completed_card(self):
        """Giao diện cũ: thẻ Troop Training "Completed" -> xong hôm nay, không bấm Go."""
        device = run_flow(self, lambda bot, _s: open_task_or_finish(bot, troop_training.TASK), TESTS_DIR,
                          old_grid_completed("28_old_grid_end_train_completed.png"), {})
        self.assertIn(LABEL, device.daily_done)

    def test_after_go_one_batch(self):
        """Công trình -> Train -> cấp I -> 1580 mỗi mẻ >= 300 -> 1 mẻ: Train -> Training Speedup -> Speedup Settings
        -> tích ô -> Confirm -> Finish All -> nút Train hiện lại -> Back, xong hôm nay. Không nhập số."""
        flow = [
            Step(f"{KP}train_after_go.png", tap_at(*BUILDING)),
            Step(f"{KP}train_menu.png", tap(f"{TRAIN_DIR}/train.png")),
            Step(f"{KP}train_t01.png", tap(TRAIN_BUTTON)),
            Step(f"{KP}train_t01.png?training", tap(f"{TRAIN_DIR}/trainingSpeedup.png")),
            Step(f"{GROUND}speedup.png", tap(f"{TRAIN_DIR}/speedupSettings.png")),
            Step(f"{GROUND}speedup_settings.png", tap(f"{TRAIN_DIR}/checkboxOff.png")),
            Step(f"{GROUND}speedup_settings_ticked.png", tap(f"{TRAIN_DIR}/confirm.png")),
            Step(f"{GROUND}speedup.png", tap(f"{TRAIN_DIR}/finishAll.png")),
            Step(f"{KP}train_t01.png", back()),
            Step(f"{KP}train_after_go.png", end(result=True)),
        ]
        device = run_flow(self, _after_go, TESTS_DIR, flow, {}, variants=VARIANTS)
        self.assertIn(f"{LABEL}: 1580 per batch -> 1 batch(es)", device.logs)
        self.assertIn(LABEL, device.daily_done)
        self.assertFalse([c for c in device.shells if c.startswith("input text")])


if __name__ == "__main__":
    unittest.main()
