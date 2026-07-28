import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QApplication,
)

from ..config import APP_NAME

logger = logging.getLogger("overlord")

SPLASH_STYLE = """
    QWidget {
        background-color: #1a1a2e;
    }
"""


class SplashWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(SPLASH_STYLE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(500, 300)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #4a90d9;
            font-size: 48px;
            font-weight: bold;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Multi-View Kiosk Browser")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            color: #888;
            font-size: 16px;
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_launch = QPushButton("Launch")
        btn_launch.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 32px;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #5aa0e9; }
        """)
        btn_layout.addWidget(btn_launch)

        btn_settings = QPushButton("Settings")
        btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 8px;
                font-size: 14px;
                padding: 12px 24px;
                min-width: 100px;
            }
            QPushButton:hover { background-color: #4a4a4a; color: white; }
        """)
        btn_layout.addWidget(btn_settings)

        layout.addLayout(btn_layout)

        self._btn_launch = btn_launch
        self._btn_settings = btn_settings

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(x, y)

    def auto_launch_after(self, ms: int = 500):
        QTimer.singleShot(ms, self._auto_launch)

    def _auto_launch(self):
        self._do_launch()

    def _do_launch(self):
        logger.info("Launching kiosk browser")

    def showEvent(self, event):
        super().showEvent(event)
        self._center_on_screen()
