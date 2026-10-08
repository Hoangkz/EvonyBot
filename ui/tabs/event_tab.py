"""
event_tab.py — "Event" TabPage built from event.py.

event.py liệt kê từng group (Gather Troops, King's Path, ...): các ô tích
(`checkboxes`) và ô chọn (`combos`). Mỗi nhiệm vụ có:
- `key`: tên trong settings.
- `day`: ngày của event mở nhiệm vụ này (hiện khi rê chuột vào nhiệm vụ).
- `default`: giá trị lúc chưa có cấu hình lưu (không ghi thì ô tích bỏ trống,
  ô chọn lấy giá trị đầu).
- `values` (ô chọn): số, hoặc object `{"value": 500, "level": 5}` khi lựa chọn gắn
  với cấp lính. Có level thì ô chọn hiện "500 (Lv 5)".
Vị trí control được tính tự động (ô tích bên trái, ô chọn xếp 3 cột mỗi hàng).

Mỗi group có `key`; ô tích ở tiêu đề group = group đang bật (settings "<key>_active").
Group có `redeem` (danh sách quà đổi): ô danh sách kéo / nút Up Down để xếp thứ tự ưu tiên
(settings {redeem.key: {"order": [id, ...]}}).

Settings (lưu ở cột `event` của DB) giữ đủ thông tin mỗi nhiệm vụ:
{"gather_troops_ground_troop": {"value": 500, "level": 7, "day": 1},
 "gather_troops_cultivate_generals": {"enabled": true, "day": 1}, ...}
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem, QPushButton

from .event import DATA
from .tab_placeholder import DesignerTab

GROUPS = DATA["groups"]

_COMBO_X = [220, 490, 760]   # cột nhãn; combo nằm ngay sau nhãn
_ROW_H = 35
_GROUP_TOP, _GROUP_GAP = 65, 8
_REDEEM_H = 190   # chiều cao ô danh sách quà (nhóm có "redeem")


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
    checkboxes, combos, redeems = {}, {}, {}
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
        if group.get("redeem"):
            redeems[f"panelEvent{g}"] = (10 + rows * _ROW_H, group["redeem"])
            panel_h += _REDEEM_H
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
    return data, checkboxes, combos, redeems, page_size


DESIGNER_DATA, _CHECKBOXES, _COMBOS, _REDEEMS, PAGE_SIZE = _build(GROUPS)


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
        for g, group in enumerate(GROUPS):
            box = c[f"groupBoxEvent{g}"]
            box.setCheckable(True)
            box.setChecked(bool(group.get("active", True)))
            box.clicked.connect(self.settings_changed)
        self._lists = {}
        for panel, (y, spec) in _REDEEMS.items():
            self._lists[spec["key"]] = self._build_redeem(c[panel], y, spec)

    def _build_redeem(self, panel, y, spec) -> QListWidget:
        """Danh sách quà xếp thứ tự ưu tiên (kéo thả hoặc nút Up / Down) dưới các ô chọn."""
        from PyQt5.QtWidgets import QLabel
        QLabel(spec["label"], panel).setGeometry(10, y, 700, 22)
        lst = QListWidget(panel)
        lst.setGeometry(10, y + 24, 520, _REDEEM_H - 34)
        lst.setDragDropMode(QAbstractItemView.InternalMove)
        for item in spec["items"]:
            row = QListWidgetItem(item["label"])
            row.setData(Qt.UserRole, item["id"])
            lst.addItem(row)
        lst.model().rowsMoved.connect(self.settings_changed)
        for i, (text, step) in enumerate((("▲", -1), ("▼", 1))):
            button = QPushButton(text, panel)
            button.setGeometry(540, y + 24 + i * 36, 34, 30)
            button.setToolTip("Up" if step < 0 else "Down")
            button.clicked.connect(lambda _=False, l=lst, d=step: self._move(l, d))
        lst.setCurrentRow(0)
        lst.show()
        return lst

    def _move(self, lst: QListWidget, step: int):
        row = lst.currentRow()
        target = row + step
        if row < 0 or not 0 <= target < lst.count():
            return
        lst.insertItem(target, lst.takeItem(row))
        lst.setCurrentRow(target)
        self.settings_changed.emit()

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
        for g, group in enumerate(GROUPS):
            settings[f"{group['key']}_active"] = {"enabled": c[f"groupBoxEvent{g}"].isChecked()}
        for key, lst in self._lists.items():
            settings[key] = {"order": [lst.item(i).data(Qt.UserRole) for i in range(lst.count())]}
        return settings

    def set_settings(self, data: dict):
        # Nhận cả cấu hình cũ dạng phẳng ({key: "500", key_level: 7} / {key: true}).
        # `day` luôn lấy theo event.py, không lấy từ dữ liệu đã lưu.
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
        for g, group in enumerate(GROUPS):
            saved = data.get(f"{group['key']}_active")
            if saved is not None:
                c[f"groupBoxEvent{g}"].setChecked(bool(saved.get("enabled") if isinstance(saved, dict) else saved))
        for key, lst in self._lists.items():
            saved = (data.get(key) or {}).get("order") if isinstance(data.get(key), dict) else None
            for position, item_id in enumerate(i for i in (saved or []) if self._row_of(lst, i) >= 0):
                lst.insertItem(position, lst.takeItem(self._row_of(lst, item_id)))

    @staticmethod
    def _row_of(lst: QListWidget, item_id) -> int:
        return next((i for i in range(lst.count()) if lst.item(i).data(Qt.UserRole) == item_id), -1)
