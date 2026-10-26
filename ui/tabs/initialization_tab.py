"""
initialization_tab.py — 1:1 rebuild of tabPage1 ("Initialization") from
Form3_Designer.cs: same controls, same nesting, same X/Y/W/H.
"""
import subprocess
import time
from datetime import datetime

from PyQt5.QtCore import QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen, QPixmap, QPolygon
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QMenu, QMessageBox, QPushButton, QWidget

from .constants import (
    ACTIVITY_BUTTONS,
    ACTIVITY_BUTTON_STYLE,
    ACTIVITY_BUTTON_TARGETS,
    BUBBLE_TYPES,
    CIVILIZATIONS,
    COMBO_ITEMS,
    DEFAULT_BUBBLE_TYPE,
    DESIGNER_DATA,
    PAGE_SIZE,
    PROFILE_BUTTON_GAP,
    PROFILE_BUTTON_HEIGHT,
    PROFILE_BUTTON_MIN_WIDTH,
    PROFILE_MAX,
    PROFILE_NAME_MAX,
    PROFILE_ROW_POS,
)
from ..dialogs import TextInputDialog
from ..emulator_window import EmulatorWindowError, toggle_maximize
from ..theme import COLORS
from .tab_placeholder import DesignerTab, confirm_reset


def _new_icon_canvas() -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    return pixmap, painter


def _symbol_icon() -> QIcon:
    """Dấu + xanh lá (màu success của theme), nền trong suốt, nằm chính giữa ảnh."""
    pixmap, painter = _new_icon_canvas()
    painter.setPen(QPen(QColor(COLORS["success"]), 8, Qt.SolidLine, Qt.FlatCap))
    painter.drawLine(32, 4, 32, 60)
    painter.drawLine(4, 32, 60, 32)
    painter.end()
    return QIcon(pixmap)


def _trash_icon() -> QIcon:
    """Thùng rác đỏ: nắp + quai, thân hơi thon xuống, hai vạch dọc."""
    pixmap, painter = _new_icon_canvas()
    painter.setPen(QPen(QColor("#d9534f"), 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(8, 16, 56, 16)                               # nắp
    painter.drawPolyline(QPolygon([QPoint(24, 16), QPoint(24, 7), QPoint(40, 7), QPoint(40, 16)]))   # quai
    painter.drawPolyline(QPolygon([QPoint(14, 16), QPoint(18, 58), QPoint(46, 58), QPoint(50, 16)]))   # thân
    painter.drawLine(26, 28, 26, 46)
    painter.drawLine(38, 28, 38, 46)
    painter.end()
    return QIcon(pixmap)


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


class InitializationTab(DesignerTab):
    start_clicked = pyqtSignal()
    start_all_clicked = pyqtSignal()
    stop_all_clicked = pyqtSignal()      # Stop All: dừng mọi bot đang chạy
    server_changed = pyqtSignal(str)   # server mới sau khi nhập xong
    settings_changed = pyqtSignal()    # bật/tắt bubble hoặc đổi loại bubble
    civilization_changed = pyqtSignal(int)   # người dùng chọn nền văn minh (1..7, 0 = tự nhận)
    reset_info_clicked = pyqtSignal()        # nút Reset info: xoá bubble, server, nền văn minh, route của máy
    profile_clicked = pyqtSignal(str)        # bấm nút hồ sơ: chọn nó (bấm lại hồ sơ đang chọn = về default)
    profile_added = pyqtSignal(str)          # nút "+": tên hồ sơ mới
    active_clicked = pyqtSignal(bool)        # nút Active/Inactive: muốn kích hoạt máy này?
    profile_deleted = pyqtSignal(str)        # chuột phải một nút hồ sơ -> Delete

    def __init__(self, device_id="", parent=None):
        super().__init__("tabPage1", DESIGNER_DATA, COMBO_ITEMS, PAGE_SIZE, parent=parent)
        c = self.controls

        apply_all = c["buttonInitializationApplyAll"]
        reset = QPushButton("Reset info", self.page)
        reset.setToolTip("Xoá bubble, server, nền văn minh và route (bản đồ thành) đã lưu của máy này: "
                         "lần chạy sau bot đọc / quét lại từ đầu.")
        hint = reset.sizeHint()
        reset.setGeometry(apply_all.x() - hint.width() - 6, apply_all.y() + (apply_all.height() - hint.height()) // 2,
                          hint.width(), hint.height())
        reset.clicked.connect(self._confirm_reset_info)

        c["labelID"].setStyleSheet("font-size: 16.2pt;")
        if device_id:
            c["labelID"].setText(device_id)

        # Server của thiết bị: không bắt buộc, riêng từng máy (Apply ALL không copy).
        c["textBoxServer"].setPlaceholderText("(tuỳ chọn)")
        c["textBoxServer"].editingFinished.connect(
            lambda: self.server_changed.emit(c["textBoxServer"].text().strip()))

        # Nền văn minh của thiết bị: riêng từng máy (lưu cột devices.civilization, Apply ALL không copy). activated chỉ
        # phát khi người dùng chọn, không phát khi set_civilization đổi bằng code.
        c["comboBoxCivilization"].activated.connect(
            lambda index: self.civilization_changed.emit(index))

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

        # Hàng hồ sơ dưới Bubble. Hồ sơ default của máy luôn có nhưng không hiện nút.
        self._profile_names: list[str] = []
        self._profile_row = QWidget(self.page)
        self._profile_row.move(*PROFILE_ROW_POS)
        row = QHBoxLayout(self._profile_row)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(PROFILE_BUTTON_GAP)       # các nút hồ sơ đứng kế nhau, cách một chút
        self._profile_buttons = QHBoxLayout()
        self._profile_buttons.setContentsMargins(0, 0, 0, 0)
        self._profile_buttons.setSpacing(PROFILE_BUTTON_GAP)
        row.addLayout(self._profile_buttons)
        add = QPushButton()
        add.setFixedSize(PROFILE_BUTTON_HEIGHT + 12, PROFILE_BUTTON_HEIGHT)
        add.setStyleSheet("padding: 0px;")      # theme có padding lớn
        add.setIcon(_symbol_icon())            # dấu + vẽ tay để nằm chính giữa nút (chữ "+" lệch theo đường cơ sở)
        add.setIconSize(QSize(14, 14))
        add.setToolTip("New profile (copies this device's current settings)")
        add.clicked.connect(self._add_profile)
        row.addWidget(add)
        self._add_button = add
        # Nút × xoá hồ sơ đang chọn; ẩn khi đang dùng default (default không xoá được).
        self._active_profile = ""
        self._delete_button = QPushButton()
        self._delete_button.setFixedSize(PROFILE_BUTTON_HEIGHT + 12, PROFILE_BUTTON_HEIGHT)
        self._delete_button.setStyleSheet("padding: 0px;")
        self._delete_button.setIcon(_trash_icon())
        self._delete_button.setIconSize(QSize(14, 14))
        self._delete_button.setToolTip("Delete the selected profile")
        self._delete_button.clicked.connect(lambda: self._confirm_delete_profile(self._active_profile))
        self._delete_button.hide()
        row.addWidget(self._delete_button)
        self._resize_profile_row()

        c["buttonStart"].setStyleSheet("font-size: 13.8pt;")
        c["buttonStart"].clicked.connect(self.start_clicked.emit)
        # 2 nút riêng biệt (không còn toggle Start All <-> Stop All trên cùng 1 nút).
        c["button9"].clicked.connect(self.start_all_clicked.emit)
        c["buttonStopAll"].clicked.connect(self.stop_all_clicked.emit)
        # 2 nút gọn lại (125x40 thay vì 140x50): giảm padding ngang để chữ
        # "Start All(10)" vẫn vừa vẹn, không bị cắt.
        for key in ("button9", "buttonStopAll"):
            c[key].setStyleSheet("padding: 6px 8px;")
        # Nút Active/Inactive của máy: cùng hàng, ngay bên trái Reset info (cách 6px như Reset info - Apply ALL);
        # rộng theo chữ "Inactive" để đổi nhãn không xô nút.
        self._active = True
        self.active_button = QPushButton("Inactive", self.page)
        width = self.active_button.sizeHint().width()
        self.active_button.setGeometry(reset.x() - width - 6, reset.y(), width, reset.height())
        self.active_button.clicked.connect(lambda: self.active_clicked.emit(not self._active))
        self.set_active(True)
        # Nút Maximize: phóng to cửa sổ giả lập MEmu của máy này (bấm lại thì thu về), ngay bên trái Active.
        self._device_id = device_id
        maximize = QPushButton("Maximize", self.page)
        maximize.setToolTip("Phóng to cửa sổ giả lập của máy này (bấm lại để thu về).")
        width = maximize.sizeHint().width()
        maximize.setGeometry(self.active_button.x() - width - 6, reset.y(), width, reset.height())
        maximize.clicked.connect(self._toggle_emulator_window)
        # Chưa có số liệu -> tắt cả 2; main sẽ set_run_counts() ngay khi đăng ký thiết bị.
        c["button9"].setEnabled(False)
        c["buttonStopAll"].setEnabled(False)

        # Activity buttons are toggles: they pick which activities the bot
        # runs (shown green when selected) instead of jumping to the tab.
        for name in ACTIVITY_BUTTON_TARGETS:
            c[name].setCheckable(True)
            c[name].setStyleSheet(ACTIVITY_BUTTON_STYLE)
            c[name].toggled.connect(lambda checked, name=name: self._on_activity_toggled(name, checked))

    def _on_activity_toggled(self, name: str, checked: bool):
        """Nút exclusive chạy một mình: nó được tích -> bỏ tích mọi nút khác; nút thường được tích -> bỏ tích các nút
        exclusive. Bỏ tích bằng code không phát lại tín hiệu."""
        if checked:
            exclusive = ACTIVITY_BUTTONS[name]["exclusive"]
            for other, info in ACTIVITY_BUTTONS.items():
                if other != name and (exclusive or info["exclusive"]):
                    button = self.controls[other]
                    button.blockSignals(True)
                    button.setChecked(False)
                    button.blockSignals(False)
        self.settings_changed.emit()

    def set_profiles(self, names: list, active: str = ""):
        """Dựng lại hàng nút hồ sơ (không gồm default); nút `active` được tích xanh, không nút nào tích = default."""
        self._profile_names = list(names)
        self._active_profile = active if active in names else ""
        self._delete_button.setVisible(bool(self._active_profile))
        self._add_button.setVisible(len(names) < PROFILE_MAX)   # đủ số hồ sơ thì ẩn nút +
        while self._profile_buttons.count():
            item = self._profile_buttons.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for name in names:
            button = QPushButton(name)
            button.setCheckable(True)
            button.setChecked(name == active)
            # padding dọc 0 (theme để lớn nên chữ bị cắt ở nút cao 28 px); chữ đậm cả khi chưa chọn để nút không đổi cỡ.
            button.setStyleSheet("QPushButton { padding: 0px 12px; }" + ACTIVITY_BUTTON_STYLE)
            button.setFixedHeight(PROFILE_BUTTON_HEIGHT)
            # Chữ thường khi chưa chọn, đậm khi chọn (ACTIVITY_BUTTON_STYLE): chừa sẵn chỗ cho chữ đậm để nút không đổi cỡ.
            bold = QFont(button.font())
            bold.setWeight(QFont.DemiBold)
            button.setMinimumWidth(max(PROFILE_BUTTON_MIN_WIDTH, QFontMetrics(bold).horizontalAdvance(name) + 28))
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.clicked.connect(lambda _=False, name=name: self.profile_clicked.emit(name))
            button.customContextMenuRequested.connect(
                lambda _pos, name=name, button=button: self._profile_menu(name, button))
            self._profile_buttons.addWidget(button)
            button.show()       # tạo sau khi trang đã hiện: phải show() tay, không thì nút trống tới khi bấm
        self._resize_profile_row()

    def _resize_profile_row(self):
        """Đo lại hàng theo các nút hiện có (layout chưa tự đo vì cha là trang cố định kích cỡ)."""
        self._profile_row.layout().activate()
        self._profile_row.resize(self._profile_row.sizeHint())

    def _profile_menu(self, name: str, button: QPushButton):
        menu = QMenu(self)
        delete = menu.addAction(f"Delete '{name}'")
        if menu.exec_(button.mapToGlobal(button.rect().bottomLeft())) is delete:
            self._confirm_delete_profile(name)

    def _confirm_delete_profile(self, name: str):
        if name and confirm_reset(self, "Delete profile", f"Delete profile '{name}'?"):
            self.profile_deleted.emit(name)

    def _add_profile(self):
        if len(self._profile_names) >= PROFILE_MAX:
            QMessageBox.warning(self, "New profile", f"Each device can have at most {PROFILE_MAX} profiles.")
            return
        dialog = TextInputDialog(
            "New profile", "New profile",
            hint="Copies this device's current settings into a new profile.",
            placeholder="Profile name", ok_text="Create", max_length=PROFILE_NAME_MAX,
            validate=self._profile_name_error, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.profile_added.emit(dialog.value())

    def _profile_name_error(self, name: str) -> str | None:
        """Thông báo lỗi nếu `name` không dùng được làm tên hồ sơ mới, ngược lại None."""
        if name.lower() == "default" or name.lower() in (n.lower() for n in self._profile_names):
            return f"A profile named '{name}' already exists."
        return None

    def _toggle_emulator_window(self):
        try:
            toggle_maximize(self._device_id)
        except (EmulatorWindowError, OSError, ValueError, AttributeError, subprocess.SubprocessError) as e:
            QMessageBox.warning(self, "Maximize", str(e))

    def _confirm_reset_info(self):
        if confirm_reset(self, "Reset info",
                         "Xoá bubble, server, nền văn minh và route (bản đồ thành) đã lưu của máy này?\n"
                         "Lần chạy sau bot sẽ đọc / quét lại từ đầu."):
            self.reset_info_clicked.emit()

    def set_running(self, running: bool):
        """While the bot runs, Start becomes Stop (same button, same signal)."""
        self.controls["buttonStart"].setText("Stop" if running else "Start")
        self.controls["buttonStart"].setStyleSheet("background-color: #d9534f; color: white;" if running else "")

    def set_active(self, active: bool):
        self._active = active
        self.active_button.setText("Active" if active else "Inactive")
        self.controls["buttonStart"].setEnabled(active)   # máy Inactive không được Start

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

    def set_civilization(self, civilization):
        """Hiện nền văn minh (1..7); None / 0 / ngoài khoảng = chưa biết."""
        index = civilization if isinstance(civilization, int) and 0 < civilization <= len(CIVILIZATIONS) else 0
        self.controls["comboBoxCivilization"].setCurrentIndex(index)

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
        if "civilization" in data:
            self.set_civilization(data["civilization"])
        if "bubble_until" in data:
            # Thời điểm bubble hết đã lưu trong DB -> đếm ngược tiếp khi mở app.
            self.set_bubble_remaining(seconds_until(data["bubble_until"]))
        if data.get("bubble_type") in BUBBLE_TYPES:
            self.controls["comboBoxBubbleType"].setCurrentText(data["bubble_type"])
        if "activities" in data:
            selected = set(data["activities"])
            for name, target in ACTIVITY_BUTTON_TARGETS.items():
                self.controls[name].setChecked(target in selected)
