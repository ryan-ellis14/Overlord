from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout


class PageIndicator(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_page = 0
        self._total_pages = 1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel("1 / 1")
        self._label.setStyleSheet("""
            color: rgba(200, 200, 200, 200);
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(self._label)

        self.setFixedHeight(28)

    def set_page(self, current: int, total: int):
        self._current_page = current
        self._total_pages = total
        self._label.setText(f"{current + 1} / {total}")
