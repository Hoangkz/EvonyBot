"""
battlefield_shop_tab.py — 1:1 rebuild of tabPage7 ("Battlefield Shop")
from Form3_Designer.cs.
(The empty 8x8 leftover "groupBox13" placeholder control from the
original designer carried no content and is not ported.)
"""
from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "buttonBattlefieldShopApplyALL": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "checkBoxBlackMarketBattlefield": {"loc": [685, 32], "size": [138, 28],
                                        "text": "Black Market", "type": "CheckBox"},
    "checkOpenBoxBattlefield": {"loc": [498, 32], "size": [113, 28], "text": "OpenBox", "type": "CheckBox"},
    "comboBoxRefreshBattlefieldShop": {"loc": [270, 32], "size": [121, 30], "type": "ComboBox"},
    "groupBox8": {"children": ["panel2"], "loc": [20, 69], "size": [1047, 142],
                  "text": "Setting", "type": "GroupBox"},
    "label4": {"loc": [76, 37], "size": [181, 24], "text": "Quantity To Refresh:", "type": "Label"},
    "panel2": {"children": ["checkOpenBoxBattlefield", "checkBoxBlackMarketBattlefield",
                             "label4", "comboBoxRefreshBattlefieldShop"],
               "loc": [31, 27], "size": [991, 98], "type": "Panel"},
    "tabPage7": {"children": ["buttonBattlefieldShopApplyALL", "groupBox8"],
                 "loc": [4, 31], "size": [1088, 609], "text": "Battlefield Shop", "type": "TabPage"},
}
COMBO_ITEMS = {"comboBoxRefreshBattlefieldShop": ["ALL", "10", "20", "50", "100"]}
PAGE_SIZE = (1088, 609)


class BattlefieldShopTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("tabPage7", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)

    def get_settings(self) -> dict:
        c = self.controls
        return {
            "open_box": c["checkOpenBoxBattlefield"].isChecked(),
            "black_market": c["checkBoxBlackMarketBattlefield"].isChecked(),
            "quantity_to_refresh": c["comboBoxRefreshBattlefieldShop"].currentText(),
        }

    def set_settings(self, data: dict):
        c = self.controls
        if "open_box" in data:
            c["checkOpenBoxBattlefield"].setChecked(bool(data["open_box"]))
        if "black_market" in data:
            c["checkBoxBlackMarketBattlefield"].setChecked(bool(data["black_market"]))
        if "quantity_to_refresh" in data:
            c["comboBoxRefreshBattlefieldShop"].setCurrentText(str(data["quantity_to_refresh"]))
