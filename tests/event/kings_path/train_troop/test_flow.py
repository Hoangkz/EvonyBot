"""
Flow test Event / King's Path / Train Troop (bot/activities/event/kings_path/train_troop/): tách từ test_flow.py.
Ảnh dùng chung ở ../screens/ (không chép sang thư mục nhiệm vụ).
"""
import unittest
from bot.activities.event.kings_path import train_troop
from bot.activities.event.kings_path.train_troop.tier import choose_first_tier
from bot.activities.event.kings_path.train_troop.constants import TIERS as TRAIN_TIERS
from tests.flow import Step, end, run_flow, tap, tap_at
from tests.event.kings_path.common import SCREENS, KP, _run
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)


class TrainTroopFlow(unittest.TestCase):
    def test_train_troop(self):
        """Day 3 -> tab Strong Troops (ảnh thật, tiến độ xuống 2 dòng "23,530 / 50,000") -> Go ->
        doanh trại -> menu Train -> màn Train (đang chọn cấp I) -> Train."""
        flow = [
            Step("day3_healing_heart.png", tap(f"{KP}/Tab/strongTroops.png")),
            Step("day3_strong_troops_go.png", tap_at(335, 344)),
            # Doanh trại đã có ảnh học sẵn (Images/Event/Building): bấm đúng chỗ nhận ra, không bấm giữa màn.
            Step("train_after_go.png", tap_at(181, 333, tol=5)),
            Step("train_menu.png", tap("Event/GatherTroops/Train/train.png")),
            # Vòng đang chọn đã là cấp I và train được: không bấm vòng nào, bấm Train luôn.
            Step("train_t01.png", tap("Event/GatherTroops/Train/trainButton.png")),
        ]
        device = _run(self, flow, {train_troop.KEY: {"value": 50000, "day": 3}})
        # Tiến độ xuống 2 dòng "23,530 /" + "50,000" -> đã làm 23530, còn 26470 / 1580 = 17 mẻ.
        self.assertIn("Train Troop: done 23530, remaining 26470", device.logs)
        self.assertIn("Train Troop: 1580 per batch -> 17 batch(es)", device.logs)

    def test_train_first_tier_walks_down(self):
        """Công trình mở ở cấp cao (ảnh lính bộ cấp XIII .. V của test Ground Troop): đọc huy hiệu cấp của vòng đang
        chọn rồi bấm vòng cách nó 2 ô về phía cấp I (x giảm dần theo vị trí vòng đang chọn), đọc lại; tới khi vòng
        đang chọn là cấp I và train được (train_t01) thì xong."""
        g = "../../gather_troops/ground_troop/screens/"
        flow = [
            Step(g + "train_t13.png", tap_at(111, 452, tol=3)),
            Step(g + "train_t11.png", tap_at(109, 452, tol=3)),
            Step(g + "train_t09.png", tap_at(106, 452, tol=3)),
            Step(g + "train_t07.png", tap_at(104, 452, tol=3)),
            Step(g + "train_t05.png", tap_at(102, 452, tol=3)),
            Step("train_t01.png", end(1)),
        ]
        run_flow(self, lambda bot, _: choose_first_tier(bot, TRAIN_TIERS), SCREENS, flow, {})

    def test_train_first_tier_other_kind(self):
        """Game mở chuồng ngựa (lính kỵ, đang chọn cấp II): đọc huy hiệu rồi bấm vòng cấp I bên trái (38, 452); thấy
        cấp I được chọn và train được thì xong (ảnh sau khi bấm lấy từ test Train Troop)."""
        flow = [
            Step("../../gather_troops/mounted_troop/screens/train_t02.png", tap_at(38, 452, tol=3)),
            Step("train_t01.png", end(1)),
        ]
        run_flow(self, lambda bot, _: choose_first_tier(bot, TRAIN_TIERS), SCREENS, flow, {})


if __name__ == "__main__":
    unittest.main()
