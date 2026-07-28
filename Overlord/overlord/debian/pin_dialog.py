import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QWidget,
    QSizePolicy,
)

logger = logging.getLogger("overlord")

PIN_DOT_FILLED_STYLE = """
    background-color: #4a90d9;
    border-radius: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
"""

PIN_DOT_EMPTY_STYLE = """
    background-color: #2a2a2a;
    border: 2px solid #555;
    border-radius: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
"""

NUM_BUTTON_STYLE = """
    QPushButton {
        background-color: #3a3a3a;
        color: white;
        border: 1px solid #555;
        border-radius: 8px;
        font-size: 24px;
        font-weight: bold;
        min-width: 70px;
        min-height: 60px;
    }
    QPushButton:hover {
        background-color: #4a4a4a;
    }
    QPushButton:pressed {
        background-color: #5a5a5a;
    }
"""

ACTION_BUTTON_STYLE = """
    QPushButton {
        background-color: #4a90d9;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        padding: 8px 16px;
        min-height: 40px;
    }
    QPushButton:hover {
        background-color: #5aa0e9;
    }
"""

CANCEL_BUTTON_STYLE = """
    QPushButton {
        background-color: #666;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        padding: 8px 16px;
        min-height: 40px;
    }
    QPushButton:hover {
        background-color: #777;
    }
"""


class PinDialog(QDialog):

    exit_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    kiosk_settings_requested = pyqtSignal()

    def __init__(self, exit_pin: str, settings_pin: str, kiosk_settings_pin: str, parent=None):
        super().__init__(parent)
        self._exit_pin = exit_pin
        self._settings_pin = settings_pin
        self._kiosk_settings_pin = kiosk_settings_pin
        self._current_entry = ""
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(340, 440)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 16px;
                border: 2px solid #444;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(16)

        title = QLabel("Enter 4-digit PIN")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ccc; font-size: 18px; font-weight: bold;")
        container_layout.addWidget(title)

        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(12)
        dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pin_dots = []
        for _ in range(4):
            dot = QWidget()
            dot.setStyleSheet(PIN_DOT_EMPTY_STYLE)
            dots_layout.addWidget(dot)
            self._pin_dots.append(dot)
        container_layout.addLayout(dots_layout)

        self._feedback_label = QLabel("")
        self._feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feedback_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
        self._feedback_label.setVisible(False)
        container_layout.addWidget(self._feedback_label)

        grid_layout = self._create_numpad()
        container_layout.addLayout(grid_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet(CANCEL_BUTTON_STYLE)
        btn_cancel.clicked.connect(self.reject)
        bottom_layout.addWidget(btn_cancel)

        btn_clear = QPushButton("Clear")
        btn_clear.setStyleSheet(CANCEL_BUTTON_STYLE)
        btn_clear.clicked.connect(self._clear_entry)
        bottom_layout.addWidget(btn_clear)

        container_layout.addLayout(bottom_layout)

        main_layout.addWidget(container)

    def _create_numpad(self):
        from PyQt6.QtWidgets import QGridLayout

        grid = QGridLayout()
        grid.setSpacing(8)

        buttons = [
            ("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("", 3, 0), ("0", 3, 1), ("", 3, 2),
        ]

        for label, row, col in buttons:
            if label == "":
                spacer = QWidget()
                grid.addWidget(spacer, row, col)
                continue
            btn = QPushButton(label)
            btn.setStyleSheet(NUM_BUTTON_STYLE)
            btn.clicked.connect(lambda checked, d=label: self._add_digit(d))
            grid.addWidget(btn, row, col)

        return grid

    def _add_digit(self, digit: str):
        if len(self._current_entry) >= 4:
            return
        self._current_entry += digit
        self._update_dots()
        self._feedback_label.setVisible(False)

        if len(self._current_entry) == 4:
            self._check_pin()

    def _clear_entry(self):
        self._current_entry = ""
        self._update_dots()
        self._feedback_label.setVisible(False)

    def _update_dots(self):
        for i, dot in enumerate(self._pin_dots):
            if i < len(self._current_entry):
                dot.setStyleSheet(PIN_DOT_FILLED_STYLE)
            else:
                dot.setStyleSheet(PIN_DOT_EMPTY_STYLE)

    def _check_pin(self):
        pin = self._current_entry
        if pin == self._exit_pin:
            logger.debug("Exit PIN correct")
            self.accept()
            self.exit_requested.emit()
        elif pin == self._settings_pin:
            logger.debug("Settings PIN correct")
            self.accept()
            self.settings_requested.emit()
        elif pin == self._kiosk_settings_pin:
            logger.debug("Kiosk Settings PIN correct")
            self.accept()
            self.kiosk_settings_requested.emit()
        else:
            self._feedback_label.setText("Incorrect PIN")
            self._feedback_label.setVisible(True)
            self._current_entry = ""
            self._update_dots()

    def showEvent(self, event):
        super().showEvent(event)
        self._current_entry = ""
        self._update_dots()
        self._feedback_label.setVisible(False)
