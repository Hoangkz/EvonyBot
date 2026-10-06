"""
initialization_tab.py — 1:1 rebuild of tabPage1 ("Initialization") from
Form3_Designer.cs: same controls, same nesting, same X/Y/W/H.
"""
import time
from datetime import datetime

from PyQt5.QtCore import QTimer, pyqtSignal

from ..theme import COLORS
from .tab_placeholder import DesignerTab

DESIGNER_DATA = {
    "ButtonJoinMonsterWar": {"loc": [85, 53], "size": [230, 40], "text": "Join Monster War", "type": "Button"},
    "ButtonOpenGiftBox": {"loc": [85, 117], "size": [230, 40], "text": "Open Gift Box", "type": "Button"},
    "button10": {"loc": [85, 180], "size": [230, 40], "text": "Event", "type": "Button"},
    "button7": {"loc": [740, 117], "size": [230, 40], "text": "Battlefield Shop", "type": "Button"},
    # button9 (Start All) nằm cạnh buttonStopAll (Stop All) dưới GroupBox; 2 nút
    # 125x40 (nhỏ lại so với 140x50 gốc) căn phải theo mép phải GroupBox (x=1075).
    "button9": {"loc": [815, 377], "size": [125, 40], "text": "Start All", "type": "Button"},
    "buttonStopAll": {"loc": [950, 377], "size": [125, 40], "text": "Stop All", "type": "Button"},
    "buttonAllianceCapacity": {"loc": [409, 53], "size": [230, 40], "text": "Alliance Capacity", "type": "Button"},
    "buttonBlackMarket": {"loc": [409, 117], "size": [230, 40], "text": "Black Market", "type": "Button"},
    "buttonDailyActivities": {"loc": [740, 53], "size": [230, 40], "text": "Daily Activities", "type": "Button"},
    "buttonInitializationApplyAll": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "buttonStart": {"loc": [449, 447], "size": [217, 51], "text": "Start", "type": "Button"},
    "groupBox2": {
        "children": ["button10", "button7", "buttonBlackMarket", "ButtonOpenGiftBox",
                      "ButtonJoinMonsterWar", "buttonDailyActivities", "buttonAllianceCapacity"],
        "loc": [13, 106], "size": [1062, 253], "text": "Select Activity", "type": "GroupBox",
    },
    "checkBoxBubble": {"loc": [13, 62], "size": [75, 28], "text": "Bubble", "type": "CheckBox"},
    "comboBoxBubbleType": {"loc": [90, 62], "size": [60, 28], "type": "ComboBox"},
    "labelBubbleTime": {"loc": [158, 62], "size": [100, 28], "type": "Label"},
    "labelID": {"loc": [506, 18], "size": [200, 32], "text": "labelID", "type": "Label"},
    "labelServer": {"loc": [13, 22], "size": [60, 28], "text": "Server:", "type": "Label"},
    "textBoxServer": {"loc": [75, 22], "size": [200, 28], "type": "TextBox"},
    "tabPage1": {
        "children": ["button9", "buttonStopAll", "buttonInitializationApplyAll", "buttonStart",
                     "labelID",
                     "labelServer", "textBoxServer", "checkBoxBubble", "labelBubbleTime",
                     "comboBoxBubbleType",
                     "groupBox2"],
        "loc": [4, 31], "size": [1088, 609], "text": "Initialization", "type": "TabPage",
    },
}
# Loại bubble (khiên) có thể dùng.
BUBBLE_TYPES = ["8h", "24h", "3d", "7d"]
DEFAULT_BUBBLE_TYPE = "24h"
COMBO_ITEMS = {"comboBoxBubbleType": BUBBLE_TYPES}
PAGE_SIZE = (1088, 609)

# Original button.Tag values in the C# form matched the activity's
# display text, which in turn matches this app's tab titles.
ACTIVITY_BUTTON_TARGETS = {
    "ButtonJoinMonsterWar": "Join Monster War",
    "buttonAllianceCapacity": "Alliance Capacity",
    "buttonDailyActivities": "Daily Activities",
    "ButtonOpenGiftBox": "Open Gift Box",
    "buttonBlackMarket": "Black Market",
    "button7": "Battlefield Shop",
    "button10": "Event",
}

def seconds_until(iso: str) -> float | None:
    """Số giây từ bây giờ tới thời điểm ISO (giờ máy); None nếu rỗng / sai định dạng."""
    try:
        return (datetime.fromisoformat(iso) - datetime.now()).total_seconds()
    except (TypeError, ValueError):
        return None


def format_remaining(seconds: float) -> str:
    """Giây còn lại -> '2d 03:15:20' / '05:00:00'."""
    seconds = max(0, int(seconds))
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    clock = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{days}d {clock}" if days else clock


# Set on each button directly: the designer page's own "background: white"
# stylesheet would otherwise win over the app-level theme.
ACTIVITY_BUTTON_STYLE = f"""
QPushButton:checked {{
    background: {COLORS['success']};
    border-color: {COLORS['success']};
    color: white;
    font-weight: 600;
}}
QPushButton:checked:hover {{
    background: #28985f;
    color: white;
}}
"""


class InitializationTab(DesignerTab):
    start_clicked = pyqtSignal()
    start_all_clicked = pyqtSignal()
    stop_all_clicked = pyqtSignal()      # Stop All: dừng mọi bot đang chạy
    server_changed = pyqtSignal(str)   # server mới sau khi nhập xong
    settings_changed = pyqtSignal()    # bật/tắt bubble hoặc đổi loại bubble

    def __init__(self, device_id="", parent=None):
        super().__init__("tabPage1", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)
        c = self.controls

        c["labelID"].setStyleSheet("font-size: 16.2pt;")
        if device_id:
            c["labelID"].setText(device_id)

        # Server của thiết bị: không bắt buộc, riêng từng máy (Apply ALL không copy).
        c["textBoxServer"].setPlaceholderText("(tuỳ chọn)")
        c["textBoxServer"].editingFinished.connect(
            lambda: self.server_changed.emit(c["textBoxServer"].text().strip()))

        # Bubble: tích để bot giữ khiên, chọn loại 8h/24h/3d/7d để dùng.
        c["comboBoxBubbleType"].setCurrentText(DEFAULT_BUBBLE_TYPE)
        c["comboBoxBubbleType"].currentTextChanged.connect(lambda _: self.settings_changed.emit())
        c["checkBoxBubble"].toggled.connect(self._update_bubble_enabled)
        c["checkBoxBubble"].toggled.connect(lambda _: self.settings_changed.emit())
        self._update_bubble_enabled(c["checkBoxBubble"].isChecked())

        # Thời gian bubble còn lại, đếm ngược mỗi giây khi đã biết.
        self._bubble_expiry = None
        self._bubble_timer = QTimer(self)
        self._bubble_timer.setInterval(1000)
        self._bubble_timer.timeout.connect(self._refresh_bubble_time)
        self._refresh_bubble_time()

        c["buttonStart"].setStyleSheet("font-size: 13.8pt;")
        c["buttonStart"].clicked.connect(self.start_clicked.emit)
        # 2 nút riêng biệt (không còn toggle Start All <-> Stop All trên cùng 1 nút).
        c["button9"].clicked.connect(self.start_all_clicked.emit)
        c["buttonStopAll"].clicked.connect(self.stop_all_clicked.emit)
        # 2 nút gọn lại (125x40 thay vì 140x50): giảm padding ngang để chữ
        # "Start All(10)" vẫn vừa vẹn, không bị cắt.
        for key in ("button9", "buttonStopAll"):
            c[key].setStyleSheet("padding: 6px 8px;")
        # Chưa có số liệu -> tắt cả 2; main sẽ set_run_counts() ngay khi đăng ký thiết bị.
        c["button9"].setEnabled(False)
        c["buttonStopAll"].setEnabled(False)

        # Activity buttons are toggles: they pick which activities the bot
        # runs (shown green when selected) instead of jumping to the tab.
        for name in ACTIVITY_BUTTON_TARGETS:
            c[name].setCheckable(True)
            c[name].setStyleSheet(ACTIVITY_BUTTON_STYLE)
            c[name].toggled.connect(self.settings_changed.emit)

    def set_running(self, running: bool):
        """While the bot runs, Start becomes Stop (same button, same signal)."""
        self.controls["buttonStart"].setText("Stop" if running else "Start")
        self.controls["buttonStart"].setStyleSheet("background-color: #d9534f; color: white;" if running else "")

    def set_run_counts(self, running: int, total: int):
        """Cập nhật 2 nút Start All / Stop All theo (số bot đang chạy, tổng số thiết bị).

        Cùng nguyên tắc màn Home: Start All bật khi còn thiết bị chưa chạy,
        Stop All bật khi có ít nhất 1 thiết bị đang chạy; nhãn kèm số lượng.
        """
        idle = max(total - running, 0)
        start = self.controls["button9"]
        stop = self.controls["buttonStopAll"]
        start.setText(f"Start All({idle})")
        start.setEnabled(idle > 0)
        stop.setText(f"Stop All({running})")
        stop.setEnabled(running > 0)

    def set_device_id(self, device_id: str):
        self.controls["labelID"].setText(device_id)

    def _update_bubble_enabled(self, enabled: bool):
        self.controls["comboBoxBubbleType"].setEnabled(enabled)

    def bubble_type(self) -> str:
        return self.controls["comboBoxBubbleType"].currentText() or DEFAULT_BUBBLE_TYPE

    def set_bubble_remaining(self, seconds):
        """Hiện thời gian bubble còn lại (giây); None = chưa biết / không có bubble."""
        if seconds is None or seconds <= 0:
            self._bubble_expiry = None
            self._bubble_timer.stop()
        else:
            self._bubble_expiry = time.monotonic() + seconds
            self._bubble_timer.start()
        self._refresh_bubble_time()

    def _refresh_bubble_time(self):
        label = self.controls["labelBubbleTime"]
        remaining = 0 if self._bubble_expiry is None else self._bubble_expiry - time.monotonic()
        if remaining <= 0:
            # Không có bubble -> ẩn hẳn, không hiện "--".
            self._bubble_expiry = None
            self._bubble_timer.stop()
            label.hide()
            return
        label.setText(format_remaining(remaining))
        label.show()

    def selected_activities(self) -> list[str]:
        return [target for name, target in ACTIVITY_BUTTON_TARGETS.items()
                if self.controls[name].isChecked()]

    def get_settings(self) -> dict:
        return {
            "device_id": self.controls["labelID"].text(),
            "activities": self.selected_activities(),
            "server": self.controls["textBoxServer"].text().strip(),
            "bubble": self.controls["checkBoxBubble"].isChecked(),
            "bubble_type": self.bubble_type(),
        }

    def set_settings(self, data: dict):
        if "device_id" in data:
            self.set_device_id(data["device_id"])
        if "server" in data:
            self.controls["textBoxServer"].setText(data["server"] or "")
        if "bubble" in data:
            self.controls["checkBoxBubble"].setChecked(bool(data["bubble"]))
        if "bubble_until" in data:
            # Thời điểm bubble hết đã lưu trong DB -> đếm ngược tiếp khi mở app.
            self.set_bubble_remaining(seconds_until(data["bubble_until"]))
        if data.get("bubble_type") in BUBBLE_TYPES:
            self.controls["comboBoxBubbleType"].setCurrentText(data["bubble_type"])
        if "activities" in data:
            selected = set(data["activities"])
            for name, target in ACTIVITY_BUTTON_TARGETS.items():
                self.controls[name].setChecked(target in selected)
