"""
dialogs.py — popup nhập liệu dùng chung, cùng một kiểu: tiêu đề, dòng gợi ý, ô nhập, báo lỗi ngay trong popup,
nút Cancel + nút chính (xanh). Màu / bo góc nằm trong ui/theme.py (#StyledDialog, #DialogTitle, #DialogHint,
#DialogInput, #DialogError).

Lớp con ghi đè `_submit()`: kiểm tra `self.edit.text()`, lỗi thì `show_error(...)`, hợp lệ thì `accept()`.
"""
from typing import Callable

from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from .theme import COLORS

DIALOG_WIDTH = 380
CONTENT_WIDTH = DIALOG_WIDTH - 48     # trừ lề trái + phải
BUTTON_WIDTH = 96


class Spinner(QWidget):
    """Vòng tròn xoay: nền xám nhạt, một cung xanh chạy quanh."""

    STEP_DEGREES = 9
    INTERVAL_MS = 16

    def __init__(self, size: int = 46, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(self.INTERVAL_MS)
        self._timer.timeout.connect(self._step)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def _step(self):
        self._angle = (self._angle + self.STEP_DEGREES) % 360
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = 4
        box = QRectF(self.rect()).adjusted(width, width, -width, -width)
        painter.setPen(QPen(QColor(COLORS["border"]), width))
        painter.drawEllipse(box)
        pen = QPen(QColor(COLORS["accent"]), width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(box, int((90 - self._angle) * 16), -110 * 16)    # cung 110 độ, quay theo chiều kim đồng hồ


class BusyOverlay(QWidget):
    """Lớp phủ mờ phủ kín popup, vòng xoay + chữ ở giữa; chặn chuột / bàn phím vào phần bên dưới."""

    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        self.spinner = Spinner()
        self.label = QLabel()
        self.label.setObjectName("DialogHint")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spinner, 0, Qt.AlignCenter)
        layout.addWidget(self.label, 0, Qt.AlignCenter)
        self.hide()

    def paintEvent(self, _):
        QPainter(self).fillRect(self.rect(), QColor(255, 255, 255, 246))

    def run(self, text: str):
        self.label.setText(text)
        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
        self.spinner.start()
        self.setFocus()

    def finish(self):
        self.spinner.stop()
        self.hide()


class StyledDialog(QDialog):
    def __init__(self, title: str, heading: str, hint: str = "", placeholder: str = "", ok_text: str = "OK",
                 max_length: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("StyledDialog")
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)   # bỏ nút "?" trên thanh tiêu đề
        self.setMinimumWidth(DIALOG_WIDTH)
        self.ok_text = ok_text

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(8)
        layout.setSizeConstraint(QLayout.SetFixedSize)    # popup tự co / giãn theo nội dung (hiện / ẩn dòng lỗi)

        head = QLabel(heading)
        head.setObjectName("DialogTitle")
        layout.addWidget(head)
        if hint:
            note = QLabel(hint)
            note.setObjectName("DialogHint")
            note.setWordWrap(True)
            note.setFixedWidth(CONTENT_WIDTH)      # nhãn xuống dòng theo chiều rộng popup, không kéo giãn popup
            layout.addWidget(note)
        layout.addSpacing(6)

        self.edit = QLineEdit()
        self.edit.setObjectName("DialogInput")
        self.edit.setPlaceholderText(placeholder)
        if max_length:
            self.edit.setMaxLength(max_length)
        self.edit.returnPressed.connect(self._submit)
        self.edit.textChanged.connect(lambda _=None: self.clear_error())
        layout.addWidget(self.edit)

        self.error = QLabel()
        self.error.setObjectName("DialogError")
        self.error.setWordWrap(True)
        self.error.setFixedWidth(CONTENT_WIDTH)
        self.error.hide()
        layout.addWidget(self.error)
        layout.addSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addStretch(1)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(BUTTON_WIDTH)
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton(ok_text)
        self.ok_button.setProperty("primary", True)       # kiểu nút chính trong theme.py
        self.ok_button.setMinimumWidth(BUTTON_WIDTH)
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self._submit)
        row.addWidget(self.cancel_button)
        row.addWidget(self.ok_button)
        layout.addLayout(row)
        self._overlay = BusyOverlay(self)
        self.edit.setFocus()

    def set_busy(self, busy: bool, text: str = ""):
        """Hiện / ẩn vòng xoay ở giữa popup (đang làm việc nền); lớp phủ chặn thao tác vào popup."""
        if busy:
            self._overlay.run(text)
        else:
            self._overlay.finish()
            self.edit.setFocus()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._overlay.setGeometry(self.rect())

    def show_error(self, message: str):
        self.error.setText(f"⚠  {message}")
        self.error.show()

    def clear_error(self):
        if not self.error.isHidden():
            self.error.hide()

    def _submit(self):
        raise NotImplementedError


class TextInputDialog(StyledDialog):
    """Hỏi một chuỗi (VD tên hồ sơ). `validate(text)` trả thông báo lỗi (hiện ngay trong popup, giữ popup mở để sửa)
    hoặc None nếu hợp lệ. Lấy kết quả bằng `value()` sau khi exec_() trả Accepted."""

    def __init__(self, title: str, heading: str, hint: str = "", placeholder: str = "", ok_text: str = "OK",
                 max_length: int = 0, validate: Callable[[str], str | None] | None = None, parent=None):
        super().__init__(title, heading, hint, placeholder, ok_text, max_length, parent)
        self._validate = validate

    def value(self) -> str:
        return self.edit.text().strip()

    def _submit(self):
        text = self.value()
        if not text:
            self.show_error("Please enter a value.")
            self.edit.setFocus()
            return
        error = self._validate(text) if self._validate else None
        if error:
            self.show_error(error)
            self.edit.setFocus()
            self.edit.selectAll()
            return
        self.accept()
