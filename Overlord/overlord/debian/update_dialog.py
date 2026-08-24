import logging
import os
import subprocess

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)

logger = logging.getLogger("overlord")

UPDATE_STATUS_FILE = "/tmp/overlord-update-status"
UPDATE_SERVICE_TEMPLATE = "overlord-update@{}.service"

_DIALOG_STYLE = """
    QDialog {
        background-color: #1e1e1e;
    }
"""

_FRAME_STYLE = """
    QFrame {
        background-color: #1e1e1e;
        border-radius: 16px;
        border: 2px solid #444;
    }
"""

_SPINNER_STYLE = """
    QLabel {
        color: #4a90d9;
        font-size: 36px;
        font-weight: bold;
    }
"""

_STATUS_STYLE = """
    QLabel {
        color: #ccc;
        font-size: 14px;
    }
"""

_SPINNER_FRAMES = ["|", "/", "-", "\\"]


class UpdateDialog(QDialog):

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self._username = username
        self._frame_idx = 0
        self._poll_count = 0
        self._setup_ui()

        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        self._spinner_timer.start(150)

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._poll_status)
        self._status_timer.start(750)

        self._trigger_update()

    def _setup_ui(self):
        self.setWindowTitle("Updating Overlord")
        self.setStyleSheet(_DIALOG_STYLE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(420, 220)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setStyleSheet(_FRAME_STYLE)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Updating Overlord")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4a90d9; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self._spinner_label = QLabel("|")
        self._spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner_label.setStyleSheet(_SPINNER_STYLE)
        layout.addWidget(self._spinner_label)

        self._status_label = QLabel("Starting update service...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(_STATUS_STYLE)
        self._status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        hint = QLabel("The kiosk will restart automatically when finished.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #777; font-size: 12px;")
        layout.addWidget(hint)

        outer.addWidget(frame)

    def _trigger_update(self):
        service = UPDATE_SERVICE_TEMPLATE.format(self._username)
        try:
            subprocess.run(
                ["sudo", "-n", "systemctl", "start", service],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            logger.info("Triggered update service %s", service)
        except subprocess.TimeoutExpired:
            logger.error("Timed out starting update service")
            self._fail("Could not start update service (timeout).")
        except FileNotFoundError:
            logger.error("sudo not available")
            self._fail("sudo is not available on this system.")

    def _tick_spinner(self):
        self._frame_idx = (self._frame_idx + 1) % len(_SPINNER_FRAMES)
        self._spinner_label.setText(_SPINNER_FRAMES[self._frame_idx])

    def _poll_status(self):
        self._poll_count += 1

        status_line = self._read_status_file()
        if status_line:
            self._status_label.setText(status_line)

        service = UPDATE_SERVICE_TEMPLATE.format(self._username)
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            state = result.stdout.strip()
        except subprocess.TimeoutExpired:
            state = "unknown"

        logger.debug("Update service state: %s (poll %d)", state, self._poll_count)

        if state == "failed":
            self._fail("Update service reported a failure. See /tmp/overlord-update.log.")
            return

        if state in ("inactive", "unknown") and self._poll_count > 2:
            if status_line and "complete" in status_line.lower():
                self._succeed()
            elif state == "inactive":
                self._succeed()
            return

    def _read_status_file(self) -> str:
        try:
            if os.path.exists(UPDATE_STATUS_FILE):
                with open(UPDATE_STATUS_FILE, "r") as f:
                    return f.read().strip()
        except OSError as e:
            logger.debug("Could not read status file: %s", e)
        return ""

    def _succeed(self):
        logger.info("Update completed successfully")
        self._status_label.setText("Update complete. Restarting kiosk...")
        self._stop_timers()
        QTimer.singleShot(1500, self.accept)

    def _fail(self, message: str):
        logger.error("Update failed: %s", message)
        self._status_label.setText("Update failed: " + message)
        self._stop_timers()
        QTimer.singleShot(4000, self.reject)

    def _stop_timers(self):
        self._spinner_timer.stop()
        self._status_timer.stop()

    def closeEvent(self, event):
        event.ignore()
