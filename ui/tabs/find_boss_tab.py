"""
find_boss_tab.py — tab "Find Boss": group Setting = góc quét (bắt đầu / kết thúc, 0 .. 360 bước 15°, theo màn hình), nút Auto (chia đều 360° cho mọi
tài khoản cùng server, do main.py xử lý qua `auto_clicked`), bán kính, chia sẻ liên minh.
"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QComboBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from bot.activities.find_boss.constants import (
    ANGLE_STEP, BOSSES_KEY, END_DEFAULT, EXCLUDED_BOSSES, END_KEY, RADIUS_DEFAULT, RADIUS_KEY, RADIUS_MAX, SHARE_DEFAULT, SHARE_KEY,
    START_DEFAULT, START_KEY,
)

from .boss import DATA
from .tab_placeholder import BaseTab

CARD_COLUMNS = 4     # số boss mỗi hàng trong group Bosses
LEVEL_COLUMNS = 4    # số ô cấp mỗi hàng trong một boss

ANGLES = list(range(0, 361, ANGLE_STEP))


def _angle_combo(value: int) -> QComboBox:
    combo = QComboBox()
    combo.addItems([f"{a}°" for a in ANGLES])
    combo.setCurrentIndex(ANGLES.index(value))
    combo.setFixedWidth(110)
    return combo


def _spin(low: int, high: int, value: int, suffix: str) -> QSpinBox:
    box = QSpinBox()
    box.setRange(low, high)
    box.setValue(value)
    box.setSuffix(suffix)
    box.setFixedWidth(110)
    return box


class FindBossTab(BaseTab):
    auto_clicked = pyqtSignal()     # nút Auto: chia đều góc cho mọi tài khoản cùng server (main.py)

    def __init__(self, parent=None):
        super().__init__(title="Find Boss", parent=parent)
        group = QGroupBox("Setting")
        form = QFormLayout(group)
        self.start = _angle_combo(START_DEFAULT)
        self.end = _angle_combo(END_DEFAULT)
        self.auto_button = QPushButton("Auto")
        self.auto_button.setToolTip("Chia đều 0° → 360° cho mọi tài khoản cùng server")
        self.auto_button.clicked.connect(self.auto_clicked)
        angles = QWidget()
        row = QHBoxLayout(angles)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.start)
        row.addWidget(QLabel("→"))
        row.addWidget(self.end)
        row.addWidget(self.auto_button)
        row.addStretch(1)
        self.radius = _spin(10, RADIUS_MAX, RADIUS_DEFAULT, " km")
        self.share = QCheckBox("Share active bosses to alliance")
        self.share.setChecked(SHARE_DEFAULT)
        form.addRow("Angle (start → end):", angles)
        form.addRow("Radius:", self.radius)
        form.addRow(self.share)
        hint = QLabel("Angles are on screen: 0° = right, 90° = up, counter-clockwise from start to end (0° → 360° = full circle). "
                      "Auto splits the circle evenly between all accounts on the same server.")
        hint.setWordWrap(True)
        form.addRow(hint)
        self.add_row(group)
        self.boss_choices = []     # (category_key, tên boss, ô tích khi boss không có cấp | None, {cấp: ô tích})
        self._build_boss_groups()

    def _build_boss_groups(self):
        """Group Bosses (dưới Setting): mỗi nhóm boss.py một group, mỗi boss một thẻ (ô tích, hoặc các ô cấp). Ô nào "active" trong boss.py thì tích sẵn. Bỏ EXCLUDED_BOSSES."""
        for category in DATA["boss_categories"]:
            group = QGroupBox(f"Bosses: {category['label']}")
            grid = QGridLayout(group)
            count = 0
            for boss in category["list"]:
                if boss["name"] in EXCLUDED_BOSSES:
                    continue
                levels = boss.get("levels") or []
                card = QGroupBox(boss["name"]) if levels else QWidget()
                box = QVBoxLayout(card)
                box.setContentsMargins(8, 8, 8, 4) if levels else box.setContentsMargins(0, 0, 0, 0)
                enabled, level_boxes = None, {}
                if not levels:
                    enabled = QCheckBox(boss["name"])
                    enabled.setChecked(bool(boss.get("active")))
                    box.addWidget(enabled)
                else:
                    inner = QGridLayout()
                    for i, info in enumerate(levels):
                        level = QCheckBox(str(info["level"]))
                        detail = ", ".join(str(info[k]) for k in ("tier", "power") if info.get(k))
                        level.setToolTip(f"{boss['name']} - Level {info['level']}" + (f" ({detail})" if detail else ""))
                        level.setChecked(bool(info.get("active")))
                        level_boxes[info["level"]] = level
                        inner.addWidget(level, i // LEVEL_COLUMNS, i % LEVEL_COLUMNS)
                    box.addLayout(inner)
                grid.addWidget(card, count // CARD_COLUMNS, count % CARD_COLUMNS)
                count += 1
                self.boss_choices.append((category["category_key"], boss["name"], enabled, level_boxes))
            self.add_row(group)

    @staticmethod
    def _set_angle(combo: QComboBox, value, default: int):
        try:
            angle = int(value)
        except (TypeError, ValueError):
            angle = default
        combo.setCurrentIndex(ANGLES.index(angle) if angle in ANGLES else ANGLES.index(default))

    def get_settings(self) -> dict:
        return {START_KEY: ANGLES[self.start.currentIndex()], END_KEY: ANGLES[self.end.currentIndex()], RADIUS_KEY: self.radius.value(),
                SHARE_KEY: self.share.isChecked(),
                BOSSES_KEY: [{"category_key": category, "name": name, "levels": [lv for lv, box in levels.items() if box.isChecked()]}
                             for category, name, enabled, levels in self.boss_choices
                             if (enabled.isChecked() if enabled is not None else any(box.isChecked() for box in levels.values()))]}

    def set_settings(self, data: dict):
        """Chỉ đổi những key có trong `data` (Auto chỉ gửi hai góc)."""
        if START_KEY in data:
            self._set_angle(self.start, data[START_KEY], START_DEFAULT)
        if END_KEY in data:
            self._set_angle(self.end, data[END_KEY], END_DEFAULT)
        if RADIUS_KEY in data:
            self.radius.setValue(int(data[RADIUS_KEY]))
        if SHARE_KEY in data:
            self.share.setChecked(bool(data[SHARE_KEY]))
        if BOSSES_KEY in data:
            selected = {boss["name"]: boss.get("levels", []) for boss in data[BOSSES_KEY]}
            for _, name, enabled, levels in self.boss_choices:
                if enabled is not None:
                    enabled.setChecked(name in selected)
                for level, box in levels.items():
                    box.setChecked(level in selected.get(name, []))
