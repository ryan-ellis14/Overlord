import logging
import subprocess
import time

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QGridLayout, QVBoxLayout, QLabel, QWidget

from ..config import APP_NAME, CORNER_SIZE, SWIPE_THRESHOLD, TAP_INTERVAL
from ..pin_manager import PinManager
from .webview_page import WebviewPage
from .gesture_handler import GestureHandler
from .pin_dialog import PinDialog
from .ui.pill_button import PillButton
from .ui.page_indicator import PageIndicator
from .update_checker import UpdateChecker, UpdateInfo
from .update_dialog import UpdateDialog

logger = logging.getLogger("overlord")

BAR_STYLE = """
    QWidget {
        background-color: #1a3a6e;
        border-top: 2px solid #2a5a9e;
    }
"""


class SecretPillButton(PillButton):

    secret_activated = pyqtSignal()

    def __init__(self, direction: str = "left", parent=None):
        super().__init__(direction, parent)
        self._tap_count = 0
        self._last_tap_time = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            now = time.time() * 1000
            if now - self._last_tap_time < TAP_INTERVAL and self._last_tap_time > 0:
                self._tap_count += 1
                logger.debug("Secret tap %d/5", self._tap_count)
                if self._tap_count >= 5:
                    logger.debug(">>> 5 SECRET TAPS DETECTED <<<")
                    self._tap_count = 0
                    self.secret_activated.emit()
                    return
            else:
                self._tap_count = 1
            self._last_tap_time = now
            self.clicked.emit()
        else:
            super().mousePressEvent(event)


class MainKioskWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._pin_manager = PinManager()
        self._current_index = 0
        self._pages: list[WebviewPage] = []
        self._swipe_start_x = 0
        self._swiping = False
        self._pin_dialog: PinDialog | None = None
        self._update_info: UpdateInfo | None = None
        self._update_dialog: UpdateDialog | None = None
        self._update_in_progress = False

        urls = self._pin_manager.get_urls()
        gesture_type = self._pin_manager.get_gesture_type()
        self._gesture_handler = GestureHandler(gesture_type)
        self._gesture_handler.gesture_triggered.connect(self._on_gesture_triggered)

        self._setup_window()
        self._setup_pages(urls)
        self._setup_ui()
        self._setup_bottom_bar()
        self._setup_update_checker()
        self._inhibit_screensaver()

    def _setup_window(self):
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            self.setGeometry(geometry)
            self.showFullScreen()
        else:
            self.showMaximized()

        logger.info("Kiosk window initialized in fullscreen mode")

    def _setup_pages(self, urls: list[str]):
        for url in urls:
            page = WebviewPage(url)
            self._pages.append(page)
        if not self._pages:
            page = WebviewPage("about:blank")
            self._pages.append(page)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._stacked_widget = QStackedWidget()
        for page in self._pages:
            self._stacked_widget.addWidget(page)

        self._main_layout.addWidget(self._stacked_widget, 1)

        self._update_page_indicator()

    def _setup_bottom_bar(self):
        bar = QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet(BAR_STYLE)
        bar_layout = QGridLayout(bar)
        bar_layout.setContentsMargins(16, 6, 16, 6)
        bar_layout.setColumnStretch(0, 0)
        bar_layout.setColumnStretch(1, 0)
        bar_layout.setColumnStretch(2, 1)
        bar_layout.setColumnStretch(3, 0)

        self._btn_prev = PillButton("left")
        self._btn_prev.clicked.connect(self._navigate_prev)
        bar_layout.addWidget(self._btn_prev, 0, 0)

        self._update_label = QLabel()
        self._update_label.setStyleSheet("""
            QLabel {
                color: #ffd966;
                font-size: 12px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 80);
                border-radius: 10px;
                padding: 4px 10px;
            }
        """)
        self._update_label.setText("\u25cf Overlord Update Available")
        self._update_label.setVisible(False)
        bar_layout.addWidget(self._update_label, 0, 1)

        self._page_indicator = PageIndicator()
        bar_layout.addWidget(self._page_indicator, 0, 2)

        self._btn_next = SecretPillButton("right")
        self._btn_next.clicked.connect(self._navigate_next)
        self._btn_next.secret_activated.connect(self._show_pin_dialog)
        bar_layout.addWidget(self._btn_next, 0, 3)

        self._main_layout.addWidget(bar)

    def _setup_update_checker(self):
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_result.connect(self._on_update_result)
        self._update_checker.check_failed.connect(
            lambda msg: logger.warning("Update check failed: %s", msg)
        )
        self._update_checker.start()
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._cleanup_update_checker)

    def _cleanup_update_checker(self):
        if self._update_checker is not None and self._update_checker.isRunning():
            self._update_checker.requestInterruption()
            self._update_checker.wait(2000)

    def _on_update_result(self, info: UpdateInfo):
        self._update_info = info
        if info.available:
            logger.info(
                "Update available: local=%s (%s) remote=%s (%s)",
                info.local_version,
                info.short_local_sha(),
                info.remote_version,
                info.short_remote_sha(),
            )
            self._update_label.setVisible(True)
            if self._pin_manager.get_auto_update_enabled() and not self._update_in_progress:
                logger.info("Auto-update enabled; starting update")
                QTimer.singleShot(1000, self._start_update)
        else:
            self._update_label.setVisible(False)

    def _start_update(self):
        if self._update_in_progress:
            return
        if self._update_info is None or not self._update_info.available:
            return
        self._update_in_progress = True
        username = self._get_username()
        logger.info("Starting update flow as user '%s'", username)
        self._update_dialog = UpdateDialog(username, parent=self)
        self._update_dialog.show()
        self._update_dialog.raise_()
        self._update_dialog.activateWindow()

    def _get_username(self) -> str:
        try:
            import os
            return os.environ.get("USER") or os.environ.get("LOGNAME") or "overlord"
        except Exception:
            return "overlord"

    def _inhibit_screensaver(self):
        try:
            subprocess.run(
                ["xdg-screensaver", "suspend", str(self.winId())],
                check=False,
                capture_output=True,
            )
            logger.info("Screensaver inhibited via xdg-screensaver")
        except FileNotFoundError:
            logger.warning("xdg-screensaver not found, screensaver not inhibited")

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._show_pin_dialog()
            return
        elif key == Qt.Key.Key_Left:
            self._navigate_prev()
            return
        elif key == Qt.Key.Key_Right:
            self._navigate_next()
            return
        super().keyPressEvent(event)

    def _navigate_prev(self):
        if self._current_index > 0:
            self._current_index -= 1
            self._stacked_widget.setCurrentIndex(self._current_index)
            self._update_page_indicator()
            logger.debug("Navigated to page %d", self._current_index + 1)

    def _navigate_next(self):
        if self._current_index < len(self._pages) - 1:
            self._current_index += 1
            self._stacked_widget.setCurrentIndex(self._current_index)
            self._update_page_indicator()
            logger.debug("Navigated to page %d", self._current_index + 1)

    def _update_page_indicator(self):
        if hasattr(self, "_page_indicator"):
            self._page_indicator.set_page(self._current_index, len(self._pages))

    def _on_gesture_triggered(self):
        self._show_pin_dialog()

    def _show_pin_dialog(self):
        if self._pin_dialog is not None and self._pin_dialog.isVisible():
            return

        self._pin_dialog = PinDialog(
            exit_pin=self._pin_manager.get_exit_pin(),
            settings_pin=self._pin_manager.get_settings_pin(),
            kiosk_settings_pin=self._pin_manager.get_kiosk_settings_pin(),
            parent=self,
        )
        self._pin_dialog.exit_requested.connect(self._exit_app)
        self._pin_dialog.settings_requested.connect(self._open_settings)
        self._pin_dialog.kiosk_settings_requested.connect(self._open_kiosk_settings)
        self._pin_dialog.finished.connect(self._on_pin_dialog_finished)
        self._pin_dialog.open()

    def _on_pin_dialog_finished(self, result):
        self._pin_dialog = None

    def _exit_app(self):
        logger.info("Exit requested via PIN")
        QApplication.quit()

    def _open_settings(self):
        logger.info("Device settings requested via PIN")
        self.hide()
        try:
            subprocess.run(["cinnamon-settings"], check=False, start_new_session=True)
        except FileNotFoundError:
            try:
                subprocess.run(["gnome-control-center"], check=False, start_new_session=True)
            except FileNotFoundError:
                logger.error("No settings application found")

    def _open_kiosk_settings(self):
        logger.info("Kiosk settings requested via PIN")
        from .settings_window import SettingsWindow
        self._settings_window = SettingsWindow(
            self._pin_manager,
            update_info=self._update_info,
            parent=self,
        )
        self._settings_window.settings_applied.connect(self._on_settings_applied)
        self._settings_window.update_requested.connect(self._start_update)
        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

    def _on_settings_applied(self):
        logger.info("Settings applied, reloading views")
        urls = self._pin_manager.get_urls()
        gesture_type = self._pin_manager.get_gesture_type()
        self._gesture_handler.set_gesture_type(gesture_type)

        self._pages.clear()
        self._current_index = 0

        for i in range(self._stacked_widget.count()):
            widget = self._stacked_widget.widget(i)
            self._stacked_widget.removeWidget(widget)
            widget.deleteLater()

        for url in urls:
            page = WebviewPage(url)
            self._pages.append(page)
            self._stacked_widget.addWidget(page)

        self._stacked_widget.setCurrentIndex(0)
        self._update_page_indicator()

    def closeEvent(self, event):
        event.ignore()
        self._show_pin_dialog()
