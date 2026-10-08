"""
black_market_tab.py — tab "Black Market", dựng từ danh mục vật phẩm bot/activities/black_market/items.py.

- Group "Setting": CheckGold (vàng < 2.000.000 thì dừng), Refresh (số lần Instant Refresh), Quantity Buy (số lần mua).
- Group "Resource": một ô tích "Resource" (mặc định tích) — mua mọi gói tài nguyên của 4 loại (lương thực / gỗ / đá /
  quặng), mọi mức số lượng trong `resource_packs` của items.py (10k .. 5M).
- Các group còn lại (`groups` trong items.py, trừ "resource"): một ô tích mỗi món; món có
  `"default": true` (Chips 100) mặc định tích.
Vị trí control tính tự động (ô tích xếp _COLS cột mỗi hàng).

Settings (cột `black_market` của DB):
{"check_gold": true, "refresh": "ALL", "quantity_buy": "ALL",
 "resources": true, "items": {"chips_100": true, "medal": false, ...}}
Cấu hình cũ: "black_market_items": {"CheckGold": true, ...} -> check_gold; "resource_packs" có ô nào tích -> resources.
"""
from bot.activities.black_market.items import DATA as CATALOG

from .tab_placeholder import DesignerTab

RESOURCE_GROUP = "resource"
RESOURCES_BOX = "checkBoxMarketResources"

LIMITS = ["ALL", "10", "20", "50", "100"]
_COLS = 4
_COL_W = 252
_ROW_H = 35
_GROUP_TOP, _GROUP_GAP = 65, 8


def _build(catalog):
    """DESIGNER_DATA, {item id: (tên ô, item)}, PAGE_SIZE."""
    data = {"buttonBlackMarketApplyALL": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL",
                                          "type": "Button"}}
    roots, y = [], _GROUP_TOP

    def group(key, title, boxes):
        """boxes: [(tên ô, chữ)] -> GroupBox xếp _COLS cột."""
        nonlocal y
        for i, (name, text) in enumerate(boxes):
            data[name] = {"loc": [10 + (i % _COLS) * _COL_W, 8 + (i // _COLS) * _ROW_H],
                          "size": [_COL_W - 2, 28], "text": text, "type": "CheckBox"}
        rows = max((len(boxes) + _COLS - 1) // _COLS, 1)
        panel_h = 10 + rows * _ROW_H
        add_group(key, title, [name for name, _ in boxes], panel_h)

    def add_group(key, title, children, panel_h):
        nonlocal y
        data[f"panelBlackMarket_{key}"] = {"children": children, "loc": [21, 25], "size": [1010, panel_h],
                                           "type": "Panel"}
        data[f"groupBoxBlackMarket_{key}"] = {"children": [f"panelBlackMarket_{key}"], "loc": [20, y],
                                              "size": [1047, panel_h + 30], "text": title, "type": "GroupBox"}
        roots.append(f"groupBoxBlackMarket_{key}")
        y += panel_h + 30 + _GROUP_GAP

    # Setting: CheckGold + Refresh + Quantity Buy trên một hàng.
    data["checkBoxCheckGoldMarket"] = {"loc": [10, 8], "size": [200, 28], "text": "CheckGold",
                                       "type": "CheckBox"}
    data["labelRefreshMarket"] = {"loc": [260, 10], "size": [80, 24], "text": "Refresh:", "type": "Label"}
    data["comboBoxRefreshMarket"] = {"loc": [345, 7], "size": [121, 30], "type": "ComboBox"}
    data["labelBuyMarket"] = {"loc": [500, 10], "size": [120, 24], "text": "Quantity Buy:", "type": "Label"}
    data["comboBoxBuyMarket"] = {"loc": [625, 7], "size": [121, 30], "type": "ComboBox"}
    add_group("setting", "Setting", ["checkBoxCheckGoldMarket", "labelRefreshMarket", "comboBoxRefreshMarket",
                                     "labelBuyMarket", "comboBoxBuyMarket"], 10 + _ROW_H)

    group(RESOURCE_GROUP, catalog["groups"][RESOURCE_GROUP], [(RESOURCES_BOX, "Resource")])
    data[RESOURCES_BOX]["checked"] = True   # mặc định mua tài nguyên

    items = {}
    for key, title in catalog["groups"].items():
        if key == RESOURCE_GROUP:
            continue
        members = [it for it in catalog["items"] if it["group"] == key]
        boxes = []
        for it in members:
            name = f"checkBoxMarketItem_{it['id']}"
            items[it["id"]] = (name, it)
            boxes.append((name, it["name"]))
        if boxes:
            group(key, title, boxes)
            for name, _ in boxes:
                data[name]["checked"] = bool(items[name.removeprefix("checkBoxMarketItem_")][1].get("default"))

    page_size = (1088, max(609, y))
    data["tabPage6"] = {"children": roots + ["buttonBlackMarketApplyALL"], "loc": [4, 31],
                        "size": list(page_size), "text": "Black Market", "type": "TabPage"}
    return data, items, page_size


DESIGNER_DATA, _ITEMS, PAGE_SIZE = _build(CATALOG)
COMBO_ITEMS = {"comboBoxRefreshMarket": LIMITS, "comboBoxBuyMarket": LIMITS}


class BlackMarketTab(DesignerTab):
    def __init__(self, parent=None):
        super().__init__("tabPage6", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)

    def get_settings(self) -> dict:
        c = self.controls
        return {
            "check_gold": c["checkBoxCheckGoldMarket"].isChecked(),
            "refresh": c["comboBoxRefreshMarket"].currentText(),
            "quantity_buy": c["comboBoxBuyMarket"].currentText(),
            "resources": c[RESOURCES_BOX].isChecked(),
            "items": {item_id: c[name].isChecked() for item_id, (name, _) in _ITEMS.items()},
        }

    def set_settings(self, data: dict):
        c = self.controls
        check_gold = data.get("check_gold", (data.get("black_market_items") or {}).get("CheckGold"))
        if check_gold is not None:
            c["checkBoxCheckGoldMarket"].setChecked(bool(check_gold))
        if "refresh" in data:
            c["comboBoxRefreshMarket"].setCurrentText(str(data["refresh"]))
        if "quantity_buy" in data:
            c["comboBoxBuyMarket"].setCurrentText(str(data["quantity_buy"]))
        resources = data.get("resources", any((data.get("resource_packs") or {}).values()) or None)
        if resources is not None:
            c[RESOURCES_BOX].setChecked(bool(resources))
        for item_id, (name, _) in _ITEMS.items():
            if item_id in data.get("items", {}):
                c[name].setChecked(bool(data["items"][item_id]))