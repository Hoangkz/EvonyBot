import unittest
from pathlib import Path

from bot.activities import refine_equipment
from bot.activities.refine_equipment.constants import (
    ALL_TAB_X,
    CRAFT_REFINE,
    ENHANCE,
    EQUIPMENT_REFINE,
    FEATURES_ICON,
    FIRST_GENERAL,
    MENU_GENERALS,
    SLOTS,
    TYPE_TAB_Y,
    VIEW,
)
from tests.flow import Step, back, end, run_flow, tap, tap_pct

SCREENS = Path(__file__).parent / "screens"
WEAPON = SLOTS[0][2]

# Chụp trên máy 21913 (396x704): màn thành -> ••• -> Generals -> tướng đầu -> ô vũ khí -> View -> Refine -> Refine -> màn Refine Equipment.
# Chưa đọc được dòng New (READY = False) nên bot chỉ Back về thành, không bấm Refine.
FLOW = [
    Step("01_home.png", tap(FEATURES_ICON)),
    Step("02_menu.png", tap(MENU_GENERALS)),
    Step("03_generals.png", tap_pct(ALL_TAB_X, TYPE_TAB_Y), tap_pct(*FIRST_GENERAL)),
    Step("04_general.png", tap_pct(*WEAPON)),
    Step("05_popup.png", tap(VIEW, 0.85)),
    Step("06_equipment.png", tap(EQUIPMENT_REFINE)),
    Step("07_craft.png", tap(CRAFT_REFINE)),
    Step("08_refine_equipment.png", back()),
    Step("07_craft.png", back()),
    Step("06_equipment.png", back()),
    Step("04_general.png", back(4)),
    Step("01_home.png", end()),
]
SETTINGS = {"slots": {"weapon": {"lines": [{"attribute": "Ground Troop Attack", "color": "gold", "lock": True}]}}}


class RefineEquipmentFlow(unittest.TestCase):
    def test_main_flow(self):
        run_flow(self, refine_equipment.run, SCREENS, FLOW, SETTINGS)

    def test_no_attribute_does_nothing(self):
        run_flow(self, refine_equipment.run, SCREENS, [Step("01_home.png", end())], {"slots": {}})


if __name__ == "__main__":
    unittest.main()
