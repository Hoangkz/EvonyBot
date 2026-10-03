"""
event_tab.py — "Event" TabPage built from event.json.

event.json liệt kê từng group (Gather Troops, King's Path, ...): các ô tích
(`checkboxes`) và ô chọn (`combos`). Mỗi nhiệm vụ có:
- `key`: tên trong settings.
- `day`: ngày của event mở nhiệm vụ này (hiện khi rê chuột vào nhiệm vụ).
- `default`: giá trị lúc chưa có cấu hình lưu (không ghi thì ô tích bỏ trống,
  ô chọn lấy giá trị đầu).
- `values` (ô chọn): số, hoặc object `{"value": 500, "level": 5}` khi lựa chọn gắn
  với cấp lính. Có level thì ô chọn hiện "500 (Lv 5)".
Vị trí control được tính tự động (ô tích bên trái, ô chọn xếp 3 cột mỗi hàng).

Settings (lưu ở cột `event` của DB) giữ đủ thông tin mỗi nhiệm vụ:
{"gather_troops_ground_troop": {"value": 500, "level": 7, "day": 1},
 "gather_troops_cultivate_generals": {"enabled": true, "day": 1}, ...}
"""
import json
from pathlib import Path

from PyQt5.QtCore import pyqtSignal

from .tab_placeholder import DesignerTab

EVENT_JSON = Path(__file__).with_name("event.json")
GROUPS = json.loads(EVENT_JSON.read_text(encoding="utf-8-sig"))["groups"]

_COMBO_X = [220, 490, 760]   # cột nhãn; combo nằm ngay sau nhãn
_ROW_H = 35
_GROUP_TOP, _GROUP_GAP = 65, 8


def _option(raw) -> dict:
    """Một lựa chọn của ô chọn: số `500` hoặc `{"value": 500, "level": 5}`."""
    return dict(raw) if isinstance(raw, dict) else {"value": raw}


def _option_text(option: dict) -> str:
    level = option.get("level")
    return f"{option['value']}" if level is None else f"{option['value']} (Lv {level})"


def _build(groups):
    """DESIGNER_DATA, {key: (tên checkbox, spec)}, {key: (tên combo, spec)}, PAGE_SIZE."""
    data = {"buttonEventApplyALL": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL",
                                    "type": "Button"}}
    checkboxes, combos = {}, {}
    roots, y = [], _GROUP_TOP
    for g, group in enumerate(groups):
        children = []
        for i, box in enumerate(group.get("checkboxes", [])):
            name = f"checkBoxEvent{g}_{i}"
            data[name] = {"loc": [10, 8 + i * _ROW_H], "size": [200, 28], "text": box["label"],
                          "type": "CheckBox", "checked": bool(box.get("default", False))}
            checkboxes[box["key"]] = (name, box)
            children.append(name)
        for i, combo in enumerate(group.get("combos", [])):
            x, row_y = _COMBO_X[i % 3], 10 + (i // 3) * _ROW_H
            name = f"comboBoxEvent{g}_{i}"
            data[f"labelEvent{g}_{i}"] = {"loc": [x, row_y], "size": [115, 24],
                                          "text": combo["label"], "type": "Label"}
            data[name] = {"loc": [x + 115, row_y - 3], "size": [135, 30], "type": "ComboBox"}
            combos[combo["key"]] = (name, combo)
            children += [f"labelEvent{g}_{i}", name]
        rows = max(len(group.get("checkboxes", [])),
                   (len(group.get("combos", [])) + 2) // 3, 1)
        panel_h = 10 + rows * _ROW_H
        data[f"panelEvent{g}"] = {"children": children, "loc": [21, 25], "size": [1010, panel_h],
                                  "type": "Panel"}
        data[f"groupBoxEvent{g}"] = {"children": [f"panelEvent{g}"], "loc": [20, y],
                                     "size": [1047, panel_h + 30], "text": group["title"],
                                     "type": "GroupBox"}
        roots.append(f"groupBoxEvent{g}")
        y += panel_h + 30 + _GROUP_GAP
    page_size = (1088, max(609, y))
    data["Event"] = {"children": roots + ["buttonEventApplyALL"], "loc": [4, 31],
                     "size": list(page_size), "text": "Event", "type": "TabPage"}
    return data, checkboxes, combos, page_size


DESIGNER_DATA, _CHECKBOXES, _COMBOS, PAGE_SIZE = _build(GROUPS)


class EventTab(DesignerTab):
    # Người dùng đổi một ô (không phát khi set_settings nạp cấu hình) -> lưu DB.
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Event", DESIGNER_DATA, {}, PAGE_SIZE, parent=parent)
        c = self.controls
        for name, spec in _CHECKBOXES.values():
            self._set_day_tip(spec, c[name])
            c[name].clicked.connect(self.settings_changed)
        for name, spec in _COMBOS.values():
            combo = c[name]
            for option in map(_option, spec["values"]):
                combo.addItem(_option_text(option), option)
            label = c[name.replace("comboBox", "label", 1)]
            self._set_day_tip(spec, label, combo)
            if "default" in spec:
                self._select(combo, {"value": spec["default"]})
            combo.activated.connect(self.settings_changed)

    @staticmethod
    def _set_day_tip(spec, *widgets):
        if spec.get("day") is not None:
            for widget in widgets:
                widget.setToolTip(f"Day {spec['day']}")

    @staticmethod
    def _select(combo, wanted: dict):
        """Chọn lựa chọn khớp value (và level nếu có); không có thì giữ nguyên."""
        matches = [i for i in range(combo.count())
                   if str(combo.itemData(i)["value"]) == str(wanted.get("value"))]
        if "level" in wanted:
            matches = [i for i in matches
                       if combo.itemData(i).get("level") == wanted["level"]] or matches
        if matches:
            combo.setCurrentIndex(matches[0])

    def get_settings(self) -> dict:
        """{key: {"enabled", "day"}} cho ô tích, {key: {"value", "level"?, "day"}} cho ô chọn."""
        c = self.controls
        settings = {}
        for key, (name, spec) in _CHECKBOXES.items():
            settings[key] = {"enabled": c[name].isChecked(), "day": spec.get("day")}
        for key, (name, spec) in _COMBOS.items():
            settings[key] = {**(c[name].currentData() or {}), "day": spec.get("day")}
        return settings

    def set_settings(self, data: dict):
        # Nhận cả cấu hình cũ dạng phẳng ({key: "500", key_level: 7} / {key: true}).
        # `day` luôn lấy theo event.json, không lấy từ dữ liệu đã lưu.
        c = self.controls
        for key, (name, _) in _CHECKBOXES.items():
            if key in data:
                saved = data[key]
                c[name].setChecked(bool(saved.get("enabled") if isinstance(saved, dict) else saved))
        for key, (name, _) in _COMBOS.items():
            if key not in data:
                continue
            saved = data[key]
            if isinstance(saved, dict):
                wanted = {k: saved[k] for k in ("value", "level") if k in saved}
            else:
                wanted = {"value": saved}
                if f"{key}_level" in data:
                    wanted["level"] = data[f"{key}_level"]
            self._select(c[name], wanted)
