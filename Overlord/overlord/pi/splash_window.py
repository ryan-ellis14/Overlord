import logging

from ..config import (
    APP_NAME,
    CORNER_SIZE,
    SWIPE_THRESHOLD,
    TAP_INTERVAL,
    GESTURE_CORNER_DOUBLE_TAP,
    GESTURE_FIVE_TAP_ANYWHERE,
    GESTURE_CORNER_SEQUENCE,
)
from ..pin_manager import PinManager
from .gesture_handler import GestureHandler

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

logger = logging.getLogger("overlord")

SPLASH_CSS = """
    .overlord-splash-title {
        color: #4a90d9;
        font-size: 48px;
        font-weight: bold;
    }
    .overlord-splash-subtitle {
        color: #888;
        font-size: 16px;
    }
    .overlord-launch-btn {
        background-color: #4a90d9;
        color: white;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
    }
    .overlord-launch-btn:hover {
        background-color: #5aa0e9;
    }
    .overlord-settings-btn {
        background-color: #3a3a3a;
        color: #aaa;
        border-radius: 8px;
        font-size: 14px;
    }
    .overlord-settings-btn:hover {
        background-color: #4a4a4a;
        color: white;
    }
"""


class SplashWindow(Gtk.Window):

    def __init__(self):
        super().__init__(title=APP_NAME)
        self.set_decorated(False)
        self.set_default_size(500, 300)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_type_hint(Gdk.WindowTypeHint.SPLASHSCREEN)
        self.stick()

        self._provider = Gtk.CssProvider()
        self._provider.load_from_data(SPLASH_CSS.encode())

        self._setup_ui()

    def _setup_ui(self):
        bg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        bg.set_name("overlord-splash")
        bg.set_valign(Gtk.Align.CENTER)
        bg.set_halign(Gtk.Align.CENTER)
        bg.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        title = Gtk.Label(label="Overlord")
        title.set_name("overlord-splash-title")
        title.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        title.set_halign(Gtk.Align.CENTER)
        bg.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Multi-View Kiosk Browser")
        subtitle.set_name("overlord-splash-subtitle")
        subtitle.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        subtitle.set_halign(Gtk.Align.CENTER)
        bg.pack_start(subtitle, False, False, 0)

        btn_box = Gtk.Box(spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)

        self._btn_launch = Gtk.Button(label="Launch")
        self._btn_launch.set_name("overlord-launch-btn")
        self._btn_launch.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self._btn_settings = Gtk.Button(label="Settings")
        self._btn_settings.set_name("overlord-settings-btn")
        self._btn_settings.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        btn_box.pack_start(self._btn_launch, False, False, 0)
        btn_box.pack_start(self._btn_settings, False, False, 0)
        bg.pack_start(btn_box, False, False, 40)

        self.add(bg)

    def auto_launch_after(self, ms=500):
        pass
