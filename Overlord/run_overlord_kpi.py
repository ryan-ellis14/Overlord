import logging
import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from overlord.kpi.kpi_config import KpiConfig
from overlord.kpi.splash_window import SplashWindow
from overlord.kpi.kpi_display import KpiDisplay

logger = logging.getLogger("overlord-kpi")


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler("/tmp/overlord-kpi.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    setup_logging()
    logger.info("Starting Overlord - KPI")

    auto_mode = "--auto" in sys.argv
    config = KpiConfig()

    def show_kpi(left_url, rotation_urls, interval):
        KpiDisplay(left_url, rotation_urls, interval, on_exit=show_splash)

    def show_splash():
        GLib.idle_add(_show_splash_impl)

    def _show_splash_impl():
        splash = SplashWindow(
            config,
            on_launch=show_kpi,
            on_exit=lambda: Gtk.main_quit(),
        )
        splash.show_all()

    if auto_mode and config.is_configured:
        logger.info("Auto mode: launching KPI display directly")
        show_kpi(
            config.get_left_screen_url(),
            config.get_rotation_urls(),
            config.get_rotation_interval(),
        )
    else:
        if auto_mode and not config.is_configured:
            logger.info("Auto mode but no config found, showing splash")
        show_splash()

    Gtk.main()


if __name__ == "__main__":
    main()