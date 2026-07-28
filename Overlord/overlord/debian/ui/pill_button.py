from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget

NORMAL_BG = QColor(70, 130, 210, 200)
HOVER_BG = QColor(100, 160, 240, 240)
NORMAL_BORDER = QColor(50, 100, 180, 200)
HOVER_BORDER = QColor(80, 140, 220, 240)
ARROW_COLOR = QColor(230, 240, 255, 240)


class PillButton(QWidget):

    clicked = pyqtSignal()

    def __init__(self, direction: str = "left", parent=None):
        super().__init__(parent)
        self._direction = direction
        self._hovered = False
        self.setFixedSize(60, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = HOVER_BG if self._hovered else NORMAL_BG
        border = HOVER_BORDER if self._hovered else NORMAL_BORDER

        painter.setBrush(bg)
        painter.setPen(QPen(border, 1.5))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 18, 18)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(ARROW_COLOR)

        cx = self.width() / 2
        cy = self.height() / 2
        s = 8

        if self._direction == "left":
            points = [QPointF(cx + s, cy - s), QPointF(cx - s, cy), QPointF(cx + s, cy + s)]
        else:
            points = [QPointF(cx - s, cy - s), QPointF(cx + s, cy), QPointF(cx - s, cy + s)]

        painter.drawPolygon(QPolygonF(points))
        painter.end()
