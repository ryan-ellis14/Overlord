import logging
import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from overlord.config import APP_NAME
from overlord.pi.splash_window import SplashWindow
from overlord.pi.main import MainKioskWindow
from overlord.pi.settings_window import SettingsWindow
from overlord.pin_manager import PinManager


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler("/tmp/overlord-pi.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger("overlord")

    logger.info("Starting %s (Raspberry Pi variant)", APP_NAME)

    pin_manager = PinManager()

    splash = SplashWindow()

    kiosk_window = None

    def launch_kiosk():
        nonlocal kiosk_window
        if kiosk_window is not None:
            return
        splash.destroy()
        if not pin_manager.is_setup_complete():
            pin_manager.save_setup_complete(True)
            logger.info("First launch complete; future starts will skip splash")
        kiosk_window = MainKioskWindow()
        kiosk_window.show_all()
        logger.info("Kiosk window shown")

    def open_settings():
        splash.destroy()
        settings = SettingsWindow(pin_manager)
        settings.connect("settings-applied", lambda w: launch_kiosk())
        settings.connect("destroy", lambda w: launch_kiosk())
        settings.show_all()

    splash._on_launch = launch_kiosk
    splash._btn_launch.connect("clicked", lambda w: launch_kiosk())
    splash._btn_settings.connect("clicked", lambda w: open_settings())

    if pin_manager.is_setup_complete():
        logger.info("Setup complete; skipping splash and launching kiosk")
        launch_kiosk()
    else:
        splash.show_all()
        splash.auto_launch_after(500)

    Gtk.main()


if __name__ == "__main__":
    main()
