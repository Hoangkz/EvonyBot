"""
black_market_tab.py — 1:1 rebuild of tabPage6 ("Black Market")
from Form3_Designer.cs.
"""
from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "buttonBlackMarketApplyALL": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "checkBox16": {"loc": [10, 31], "size": [123, 28], "text": "Resources", "type": "CheckBox"},
    "checkBox18": {"loc": [176, 31], "size": [99, 28], "text": "Stamina", "type": "CheckBox"},
    "checkBox20": {"loc": [329, 31], "size": [80, 28], "text": "Chips", "type": "CheckBox"},
    "checkBoxBuyAuctionHouse": {"loc": [32, 27], "size": [82, 28], "text": "Is Buy", "type": "CheckBox"},
    "checkBoxCheckGoldMarket": {"loc": [855, 66], "size": [126, 28], "text": "CheckGold", "type": "CheckBox"},
    "checkBoxEvent": {"loc": [475, 31], "size": [80, 28], "text": "Event", "type": "CheckBox"},
    "checkBoxResourcesGem": {"loc": [654, 66], "size": [169, 28], "text": "Resources Gem", "type": "CheckBox"},
    "comboBoxBuyMarket": {"loc": [362, 21], "size": [121, 30], "type": "ComboBox"},
    "comboBoxMaxPriceAuctionHouse": {"loc": [308, 22], "size": [121, 30], "type": "ComboBox"},
    "comboBoxRefreshMarket": {"loc": [92, 21], "size": [121, 30], "type": "ComboBox"},
    "groupAuctionHouse": {"children": ["panel3"], "loc": [572, 221], "size": [495, 142],
                          "text": "Auction House", "type": "GroupBox"},
    "groupBox10": {"children": ["checkBoxResourcesGem", "checkBoxCheckGoldMarket", "panelBlackMarket"],
                   "loc": [20, 69], "size": [1047, 135], "text": "Select Black Market", "type": "GroupBox"},
    "groupBox11": {"children": ["panel1"], "loc": [20, 221], "size": [535, 142],
                   "text": "Times Market", "type": "GroupBox"},
    "label1": {"loc": [236, 27], "size": [120, 24], "text": "Quantity Buy:", "type": "Label"},
    "label2": {"loc": [6, 27], "size": [80, 24], "text": "Refresh:", "type": "Label"},
    "label8": {"loc": [198, 26], "size": [104, 24], "text": "Max Price: ", "type": "Label"},
    "panel1": {"children": ["label2", "label1", "comboBoxRefreshMarket", "comboBoxBuyMarket"],
               "loc": [17, 35], "size": [502, 82], "type": "Panel"},
    "panel3": {"children": ["checkBoxBuyAuctionHouse", "label8", "comboBoxMaxPriceAuctionHouse"],
               "loc": [21, 35], "size": [457, 82], "type": "Panel"},
    "panelBlackMarket": {"children": ["checkBoxEvent", "checkBox18", "checkBox20", "checkBox16"],
                         "loc": [21, 35], "size": [605, 82], "type": "Panel"},
    "tabPage6": {"children": ["groupAuctionHouse", "groupBox11", "groupBox10", "buttonBlackMarketApplyALL"],
                 "loc": [4, 31], "size": [1088, 609], "text": "Black Market", "type": "TabPage"},
}
COMBO_ITEMS = {
    "comboBoxBuyMarket": ["ALL", "10", "20", "50", "100"],
    "comboBoxMaxPriceAuctionHouse": ["100000", "200000", "300000", "400000", "500000", "600000", "700000", "800000"],
    "comboBoxRefreshMarket": ["ALL", "10", "20", "50", "100"],
}
PAGE_SIZE = (1088, 609)

MARKET_CHECKBOXES = ["checkBox16", "checkBox18", "checkBox20", "checkBoxEvent",
                      "checkBoxResourcesGem", "checkBoxCheckGoldMarket"]


class BlackMarketTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("tabPage6", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)

    def get_settings(self) -> dict:
        c = self.controls
        return {
            "black_market_items": {c[n].text(): c[n].isChecked() for n in MARKET_CHECKBOXES},
            "refresh": c["comboBoxRefreshMarket"].currentText(),
            "quantity_buy": c["comboBoxBuyMarket"].currentText(),
            "auction_is_buy": c["checkBoxBuyAuctionHouse"].isChecked(),
            "auction_max_price": c["comboBoxMaxPriceAuctionHouse"].currentText(),
        }

    def set_settings(self, data: dict):
        c = self.controls
        values = data.get("black_market_items", {})
        for n in MARKET_CHECKBOXES:
            if c[n].text() in values:
                c[n].setChecked(bool(values[c[n].text()]))
        if "refresh" in data:
            c["comboBoxRefreshMarket"].setCurrentText(str(data["refresh"]))
        if "quantity_buy" in data:
            c["comboBoxBuyMarket"].setCurrentText(str(data["quantity_buy"]))
        if "auction_is_buy" in data:
            c["checkBoxBuyAuctionHouse"].setChecked(bool(data["auction_is_buy"]))
        if "auction_max_price" in data:
            c["comboBoxMaxPriceAuctionHouse"].setCurrentText(str(data["auction_max_price"]))
