import logging
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from overlord.config import APP_NAME
from overlord.debian.splash_window import SplashWindow
from overlord.debian.main import MainKioskWindow
from overlord.debian.settings_window import SettingsWindow
from overlord.pin_manager import PinManager


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler("/tmp/overlord.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger("overlord")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(True)

    logger.info("Starting %s (Debian variant)", APP_NAME)

    splash = SplashWindow()
    splash.show()

    kiosk_window = None
    settings_window = None
    pin_manager = PinManager()

    def launch_kiosk():
        nonlocal kiosk_window
        splash.close()
        kiosk_window = MainKioskWindow()
        kiosk_window.show()
        logger.info("Kiosk window shown")

    def open_settings():
        nonlocal settings_window
        splash.close()
        settings_window = SettingsWindow(pin_manager)
        settings_window.settings_applied.connect(launch_kiosk)
        settings_window.finished.connect(lambda: launch_kiosk())
        settings_window.show()

    splash._btn_launch.clicked.connect(launch_kiosk)
    splash._btn_settings.clicked.connect(open_settings)
    splash.auto_launch_after(500)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
