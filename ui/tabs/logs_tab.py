"""
logs_tab.py — tab Logs của một thiết bị, chỉ đọc (không sửa / xoá được), gồm 2 phần:
- Info: mọi dòng log BotWorker gửi lên trong lần mở app này (kèm giờ), giữ tối đa MAX_INFO_LINES dòng.
- History: sự kiện đã lưu DB (bắt đầu / xong / dừng nhiệm vụ, lỗi...), kèm ngày giờ; mở app thì
  nạp lại các dòng gần nhất từ DB.
Không có cấu hình nên không lưu vào settings.
"""
from datetime import datetime

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPlainTextEdit, QTabWidget, QVBoxLayout, QWidget

MAX_INFO_LINES = 2000


class _LogView(QPlainTextEdit):
    """Ô log chỉ đọc; chỉ tự cuộn xuống cuối khi người dùng đang ở cuối."""

    def __init__(self, max_lines: int = 0, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(max_lines)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFont(QFont("Consolas", 9))

    def append_line(self, line: str):
        bar = self.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        self.appendPlainText(line)
        if at_bottom:
            bar.setValue(bar.maximum())


class LogsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.info_view = _LogView(MAX_INFO_LINES)
        self.history_view = _LogView()
        tabs = QTabWidget()
        tabs.addTab(self.info_view, "Info")
        tabs.addTab(self.history_view, "History")
        layout.addWidget(tabs)

    def append(self, message: str):
        """Log thông tin (không lưu DB)."""
        self.info_view.append_line(f"{datetime.now():%H:%M:%S}  {message}")

    def append_history(self, created_at: str, message: str):
        """Sự kiện đã lưu DB; `created_at` ISO "YYYY-MM-DDTHH:MM:SS"."""
        self.history_view.append_line(f"{created_at.replace('T', ' ')}  {message}")
