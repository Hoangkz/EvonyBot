"""
Flow test của "Gather Resources" trên ảnh chụp thật (giả lập 396x704): bản đồ thế giới -> kính lúp -> chọn loại mỏ -> Search ->
Occupy -> màn March -> March (không chọn preset); và các nhánh hết lính, hết đường march, mỏ trùng, không tìm thấy mỏ.
"""
import unittest
from pathlib import Path

from bot.activities.gather_resources import run
from bot.activities.gather_resources.constants import MARCH_BUTTON, OCCUPY, SEARCH_BUTTON, SEARCH_ICON
from tests.flow import Step, back, end, run_flow, tap, tap_at

SCREENS = Path(__file__).parent / "screens"

FOOD_ICON = (22, 490)    # icon trên chữ "Farm" (chữ ở y 525, icon cao hơn 5% màn hình)
GEMS_ICON = (159, 490)   # icon trên chữ "Gems Mine"

# Tới màn March: ở bản đồ thế giới bấm kính lúp, chọn Farm (ảnh 03 đã ở Lv 10, ô "full resources" đã tích: không bấm gì thêm),
# Search, menu tròn mở sẵn -> Occupy.
TO_MARCH = [
    Step("01_world.png", tap(SEARCH_ICON)),
    Step("02_search_types.png", tap_at(*FOOD_ICON)),
    Step("03_farm_lv10.png", tap(SEARCH_BUTTON)),
    Step("04_found_menu.png", tap(OCCUPY)),
]


def _squad(resource: str = "food", level: int = 10) -> dict:
    return {"squads": [{"resource": resource, "level": level}]}


class GatherResourcesFlow(unittest.TestCase):
    def test_main_flow(self):
        """Troop 1 đi thu thập Food Lv 10: màn March đọc giờ (thu thập 00:44:29, đi 00:02:47), bấm March luôn; lưu giờ đội về."""
        flow = TO_MARCH + [
            Step("05_march.png", tap(MARCH_BUTTON)),
            Step("07_marching.png", end()),
        ]
        device = run_flow(self, run, SCREENS, flow, _squad())
        keys = [k for k in device.daily_done if k.startswith("gather_resources_troop1_")]
        self.assertEqual(len(keys), 1, device.daily_done)

    def test_no_troops(self):
        """Màn March nút xám (hết lính): Back rồi dừng, đội chờ NO_TROOP_WAIT."""
        flow = TO_MARCH + [
            Step("05_march_no_troops.png", back()),
            Step("01_world.png", end()),
        ]
        device = run_flow(self, run, SCREENS, flow, _squad())
        self.assertTrue(any(k.startswith("gather_resources_troop1_") for k in device.daily_done))

    def test_march_full(self):
        """Đã dùng hết đường march (5/5): bấm Occupy, game báo "You cannot send more troops." -> dừng, mọi đội chờ 10 phút."""
        flow = TO_MARCH + [Step("05_march_full.png", end())]
        settings = {"squads": [{"resource": "food", "level": 10}, {"resource": "iron", "level": 8}]}
        device = run_flow(self, run, SCREENS, flow, settings)
        for troop in (1, 2):     # đội 2 chưa thử cũng phải chờ (không thử tiếp trong lượt này)
            self.assertTrue(any(k.startswith(f"gather_resources_troop{troop}_") for k in device.daily_done), device.daily_done)

    def test_target_taken(self):
        """Search ra mỏ đội mình đang đi tới: "You can only send one army to the target at a time." -> bỏ đội này, không thử lại."""
        flow = TO_MARCH + [Step("05_target_taken.png", end())]
        run_flow(self, run, SCREENS, flow, _squad())

    def test_no_target(self):
        """Gems Lv 15: game báo "No matching targets found near your Main City" -> bỏ đội đó (chờ FAIL_WAIT), không bấm gì nữa."""
        flow = [
            Step("01_world.png", tap(SEARCH_ICON)),
            Step("02_search_gems.png", tap_at(*GEMS_ICON)),
            Step("03_gems_lv15.png", tap(SEARCH_BUTTON)),
            Step("04_no_target.png", end()),
        ]
        run_flow(self, run, SCREENS, flow, _squad("gems", 15))


if __name__ == "__main__":
    unittest.main()
