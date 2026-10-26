"""
guide_view.py — màn "Hướng dẫn": danh mục bên trái, nội dung bên phải (nội dung ở guide_content.py).
"""
from PyQt5.QtWidgets import QHBoxLayout, QListWidget, QTextBrowser, QWidget

from .guide_content import GUIDE


class GuideView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GuideView")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.topics = QListWidget()
        self.topics.setFixedWidth(200)
        self.topics.addItems([title for title, _ in GUIDE])
        layout.addWidget(self.topics)

        self.page = QTextBrowser()
        self.page.setOpenExternalLinks(True)
        layout.addWidget(self.page, 1)

        self.topics.currentRowChanged.connect(self._show_topic)
        self.topics.setCurrentRow(0)

    def _show_topic(self, row: int):
        if 0 <= row < len(GUIDE):
            self.page.setHtml(GUIDE[row][1])

    def show_topic(self, title: str):
        """Nhảy tới mục có tiêu đề `title` (dùng cho nút "?" của từng tab sau này)."""
        for row, (name, _) in enumerate(GUIDE):
            if name == title:
                self.topics.setCurrentRow(row)
                return
