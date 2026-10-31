"""Attack Boss, màn March: Reset trước, rồi chọn đội; nút March xám (hết lính) thì Back, boss giữ lại (_march trả False, không bấm March)."""
import unittest
from pathlib import Path

from bot.activities.attack_boss.constants import RESET_BUTTON
from bot.activities.attack_boss.run import _march
from bot.activities.join_monster_war.constants import GENERAL_SEARCH, PRESET_DX, PRESET_X0, PRESET_Y, REGIONS
from tests.flow import Step, back, end, run_flow, tap_pct

SCREENS = Path(__file__).parent / "screens" / "march"

FLOW = [
    Step("01_march_no_troops.png", tap_pct(*RESET_BUTTON)),                   # vào màn March: bấm Reset trước
    Step("02_march_after_reset.png", tap_pct(PRESET_X0, PRESET_Y)),           # sau Reset chưa preset nào sáng: chọn đội 1
    Step("01_march_no_troops.png", back()),                                   # đội 1 sáng, có tướng, nhưng nút March xám: Back, không bấm March
    Step("03_world.png", end(result=False)),                                  # về bản đồ sạch, _march trả False (attack trả RETRY: boss đánh lại sau)
]


class MarchFlow(unittest.TestCase):
    def test_gray_march_button_goes_back(self):
        device = run_flow(self, lambda ctx, settings: _march(ctx, settings, REGIONS[GENERAL_SEARCH]), SCREENS, FLOW, {"troop": "Troop 1"})
        self.assertFalse(getattr(device.ctx, "attack_no_stamina", False))


if __name__ == "__main__":
    unittest.main()
