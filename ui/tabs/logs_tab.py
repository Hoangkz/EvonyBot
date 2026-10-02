"""
logs_tab.py — tab Logs của một thiết bị, chỉ đọc (không sửa / xoá được), gồm 2 phần:
- Info: mọi dòng log BotWorker gửi lên trong lần mở app này (kèm giờ), giữ tối đa MAX_INFO_LINES dòng.
- History: sự kiện đã lưu DB (bắt đầu / xong / dừng nhiệm vụ, lỗi...), kèm ngày giờ; mở app thì
  nạp lại các dòng trong SHOW_SECONDS gần nhất từ DB.
Cả hai chỉ hiện log trong SHOW_SECONDS (1 giờ) gần nhất: dòng cũ hơn tự ẩn khỏi màn hình (DB vẫn giữ đủ).
Không có cấu hình nên không lưu vào settings.
"""
from collections import deque
from datetime import datetime, timedelta

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import QPlainTextEdit, QTabWidget, QVBoxLayout, QWidget

SHOW_SECONDS = 3600          # chỉ hiện log trong 1 giờ gần nhất
PRUNE_INTERVAL_MS = 60_000   # mỗi phút ẩn các dòng đã quá SHOW_SECONDS
MAX_INFO_LINES = 2000


class _LogView(QPlainTextEdit):
    """Ô log chỉ đọc; chỉ tự cuộn xuống cuối khi người dùng đang ở cuối. Mỗi dòng 1 block, nhớ thời
    điểm của từng dòng để ẩn dòng quá SHOW_SECONDS."""

    def __init__(self, max_lines: int = 0, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(max_lines)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFont(QFont("Consolas", 9))
        # Cùng giới hạn với số block: Qt bỏ block đầu thì deque cũng bỏ thời điểm đầu.
        self._times: deque[datetime] = deque(maxlen=max_lines or None)

    def append_line(self, at: datetime, line: str):
        if at < datetime.now() - timedelta(seconds=SHOW_SECONDS):
            return
        bar = self.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        self.appendPlainText(line)
        self._times.append(at)
        if at_bottom:
            bar.setValue(bar.maximum())

    def prune(self):
        """Ẩn các dòng đầu (cũ nhất) đã quá SHOW_SECONDS."""
        cutoff = datetime.now() - timedelta(seconds=SHOW_SECONDS)
        old = 0
        while self._times and self._times[0] < cutoff:
            self._times.popleft()
            old += 1
        if not old:
            return
        if not self._times:
            self.clear()
            return
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.NextBlock, QTextCursor.MoveMode.KeepAnchor, old)
        cursor.removeSelectedText()


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

        self._prune_timer = QTimer(self)
        self._prune_timer.setInterval(PRUNE_INTERVAL_MS)
        self._prune_timer.timeout.connect(self._prune)
        self._prune_timer.start()

    def append(self, message: str):
        """Log thông tin (không lưu DB)."""
        now = datetime.now()
        self.info_view.append_line(now, f"{now:%H:%M:%S}  {message}")

    def append_history(self, created_at: str, message: str):
        """Sự kiện đã lưu DB; `created_at` ISO "YYYY-MM-DDTHH:MM:SS"."""
        self.history_view.append_line(datetime.fromisoformat(created_at),
                                      f"{created_at.replace('T', ' ')}  {message}")

    def _prune(self):
        self.info_view.prune()
        self.history_view.prune()
