"""
sidebar.py — left navigation panel.

Python/PyQt5 counterpart of the C# `panelistbutton` (an AutoScroll Panel
docked left that hosted one button per running bot instance). Here it
becomes a proper widget: a title, the Home button, one button per device and
the "Add device" button.

Thứ tự từ trên xuống: Home, các port, nút Add. Nút Add đứng ngay sau port cuối (chưa có port thì ngay sau Home);
danh sách port dài tới mức hết chỗ thì vùng port cuộn còn nút Add vẫn nằm ở đáy sidebar.
"""
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup,
    QDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .add_device_dialog import AddDeviceDialog


MAX_LIST_HEIGHT = 480


class _FitScrollArea(QScrollArea):
    """Vùng cuộn cao đúng bằng nội dung (lớn nhất là phần còn trống): nút Add đứng ngay dưới port cuối, không bị
    đẩy xuống đáy khi còn chỗ; hết chỗ thì vùng này co lại và cuộn."""

    def sizeHint(self):
        widget = self.widget()
        return QSize(super().sizeHint().width(), (widget.sizeHint().height() if widget else 0) + 2 * self.frameWidth())

    def minimumSizeHint(self):
        return QSize(super().minimumSizeHint().width(), 0)


class Sidebar(QWidget):
    device_selected = pyqtSignal(str)      # device_id
    home_selected = pyqtSignal()
    add_device_requested = pyqtSignal(str)   # port người dùng nhập

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("EvonyBot")
        title.setObjectName("SidebarTitle")
        outer.addWidget(title)

        self.home_button = QPushButton("🏠  Home")
        self.home_button.setCheckable(True)
        self.home_button.setChecked(True)
        self.home_button.clicked.connect(self.home_selected.emit)
        self._group.addButton(self.home_button)
        outer.addWidget(self.home_button)

        self._scroll = _FitScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(2)
        self._scroll.setWidget(self._list_container)
        outer.addWidget(self._scroll)

        self.add_button = QPushButton("＋  Add device")
        self.add_button.setToolTip("Add device by port")
        self.add_button.clicked.connect(self._ask_port)
        outer.addWidget(self.add_button)
        outer.addStretch(1)

    def _ask_port(self):
        """Popup nhập port (Enter / Connect); phát `add_device_requested` với port đã nhập."""
        dialog = AddDeviceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.add_device_requested.emit(dialog.address)

    def _list_changed(self):
        # Chiều cao tối thiểu = đúng nội dung (tối đa MAX_LIST_HEIGHT, quá thì cuộn): layout không ép vùng này về 0
        # làm nút Add đè lên port.
        # Tính từ chính các nút (nút vừa thêm chưa được show nên layout.sizeHint() còn bỏ qua nó).
        margins = self._list_layout.contentsMargins()
        count = len(self._buttons)
        height = (margins.top() + margins.bottom() + self._list_layout.spacing() * (count - 1)
                  + sum(b.sizeHint().height() for b in self._buttons.values())) if count else 0
        self._scroll.setMinimumHeight(min(height, MAX_LIST_HEIGHT))
        self._scroll.updateGeometry()

    def add_device(self, device_id: str, label: str | None = None) -> QPushButton:
        """Add a device entry to the list; returns the created button."""
        if device_id in self._buttons:
            return self._buttons[device_id]

        btn = QPushButton(label or device_id)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.device_selected.emit(device_id))
        self._group.addButton(btn)
        self._list_layout.addWidget(btn)
        self._buttons[device_id] = btn
        self._list_changed()
        return btn

    def remove_device(self, device_id: str):
        btn = self._buttons.pop(device_id, None)
        if btn is not None:
            self._group.removeButton(btn)
            self._list_layout.removeWidget(btn)
            btn.hide()
            btn.deleteLater()
            self._list_changed()

    def select_device(self, device_id: str):
        btn = self._buttons.get(device_id)
        if btn is not None:
            btn.setChecked(True)

    def select_home(self):
        self.home_button.setChecked(True)

    def device_ids(self):
        return list(self._buttons.keys())
