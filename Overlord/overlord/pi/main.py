import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, GLib, WebKit2

import logging
import time

from ..config import (
    APP_NAME, CORNER_SIZE, SWIPE_THRESHOLD, TAP_INTERVAL,
    DOUBLE_TAP_INTERVAL, SEQUENCE_TIMEOUT,
    GESTURE_CORNER_DOUBLE_TAP, GESTURE_FIVE_TAP_ANYWHERE, GESTURE_CORNER_SEQUENCE,
)
from ..pin_manager import PinManager
from .webview_widget import WebviewWidget
from .gesture_handler import GestureHandler
from .pin_dialog import PinDialog
from .settings_window import SettingsWindow
from .nav_bar import NavBar

logger = logging.getLogger("overlord")


class MainKioskWindow(Gtk.Window):

    def __init__(self):
        super().__init__(title=APP_NAME)
        self._pin_manager = PinManager()
        self._current_index = 0
        self._pages = []
        self._pin_dialog = None
        self._settings_window = None

        urls = self._pin_manager.get_urls()
        gesture_type = self._pin_manager.get_gesture_type()
        self._gesture_handler = GestureHandler(gesture_type)
        self._gesture_handler.connect("gesture-triggered", lambda h: self._on_gesture_triggered())

        self._setup_window()
        self._setup_pages(urls)
        self._setup_ui()
        self._inhibit_screensaver()

    def _setup_window(self):
        self.set_decorated(False)
        screen = Gdk.Screen.get_default()
        if screen:
            self.fullscreen()
            w = screen.get_width()
            h = screen.get_height()
            self.set_default_size(w, h)
        else:
            self.maximize()

        logger.info("Kiosk window initialized in fullscreen mode")

    def _setup_pages(self, urls):
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        for url in urls:
            page = WebviewWidget(url)
            self._pages.append(page)
            self._stack.add_named(page, f"page_{len(self._pages) - 1}")
        if not self._pages:
            page = WebviewWidget("about:blank")
            self._pages.append(page)
            self._stack.add_named(page, "page_0")

    def _setup_ui(self):
        self._overlay = Gtk.Overlay()
        self._overlay.add(self._stack)

        for page in self._pages:
            page.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            page.connect("button-press-event", self._on_gesture_click)

        self._nav_bar = NavBar(self._current_index, len(self._pages))
        self._nav_bar.connect("prev-clicked", lambda w: self._navigate_prev())
        self._nav_bar.connect("next-clicked", lambda w: self._navigate_next())
        self._nav_bar.connect("secret-activated", lambda w: self._show_pin_dialog())
        self._overlay.add_overlay(self._nav_bar)

        self.add(self._overlay)
        self.connect("key-press-event", self._on_key_press)

    def _inhibit_screensaver(self):
        try:
            import subprocess
            subprocess.run(
                ["xdg-screensaver", "suspend", str(Gdk.get_default_root_window().get_xid())],
                check=False, capture_output=True,
            )
            logger.info("Screensaver inhibited")
        except (FileNotFoundError, Exception) as e:
            logger.warning("Screensaver inhibit failed: %s", e)

    def _on_key_press(self, widget, event):
        key = event.keyval
        if key == Gdk.KEY_Escape:
            self._show_pin_dialog()
            return True
        elif key == Gdk.KEY_Left:
            self._navigate_prev()
            return True
        elif key == Gdk.KEY_Right:
            self._navigate_next()
            return True
        return False

    def _on_gesture_click(self, widget, event):
        x, y = event.x, event.y
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        corner = self._gesture_handler._detect_corner(x, y, w, h)
        if corner is not None:
            self._gesture_handler.handle_corner_click(x, y, w, h)
            self._gesture_handler.handle_any_tap(x, y, w, h)
        return Gdk.EVENT_PROPAGATE

    def _navigate_prev(self):
        if self._current_index > 0:
            self._current_index -= 1
            self._stack.set_visible_child(self._pages[self._current_index])
            self._nav_bar.set_page(self._current_index, len(self._pages))
            logger.debug("Navigated to page %d", self._current_index + 1)

    def _navigate_next(self):
        if self._current_index < len(self._pages) - 1:
            self._current_index += 1
            self._stack.set_visible_child(self._pages[self._current_index])
            self._nav_bar.set_page(self._current_index, len(self._pages))
            logger.debug("Navigated to page %d", self._current_index + 1)

    def _on_gesture_triggered(self):
        self._show_pin_dialog()

    def _show_pin_dialog(self):
        if self._pin_dialog is not None:
            return

        self._pin_dialog = PinDialog(
            exit_pin=self._pin_manager.get_exit_pin(),
            settings_pin=self._pin_manager.get_settings_pin(),
            kiosk_settings_pin=self._pin_manager.get_kiosk_settings_pin(),
        )
        self._pin_dialog.connect("exit-requested", lambda w: self._exit_app())
        self._pin_dialog.connect("settings-requested", lambda w: self._open_settings())
        self._pin_dialog.connect("kiosk-settings-requested", lambda w: self._open_kiosk_settings())
        self._pin_dialog.connect("destroy", self._on_pin_dialog_destroyed)

    def _on_pin_dialog_destroyed(self, widget):
        self._pin_dialog = None

    def _exit_app(self):
        logger.info("Exit requested via PIN")
        Gtk.main_quit()

    def _open_settings(self):
        logger.info("Device settings requested via PIN")
        import subprocess
        try:
            subprocess.run(["raspi-config"], check=False, start_new_session=True)
        except FileNotFoundError:
            try:
                subprocess.run(["gnome-control-center"], check=False, start_new_session=True)
            except FileNotFoundError:
                logger.error("No settings application found")

    def _open_kiosk_settings(self):
        logger.info("Kiosk settings requested via PIN")
        self._settings_window = SettingsWindow(self._pin_manager)
        self._settings_window.connect("settings-applied", lambda w: self._on_settings_applied())
        self._settings_window.show_all()

    def _on_settings_applied(self):
        logger.info("Settings applied, reloading views")
        urls = self._pin_manager.get_urls()
        gesture_type = self._pin_manager.get_gesture_type()
        self._gesture_handler.set_gesture_type(gesture_type)

        for page in self._pages:
            self._stack.remove(page)

        self._pages.clear()
        self._current_index = 0

        for url in urls:
            page = WebviewWidget(url)
            self._pages.append(page)
            self._stack.add_named(page, f"page_{len(self._pages) - 1}")

        self._stack.set_visible_child(self._pages[0])
        self._nav_bar.set_page(0, len(self._pages))

    def do_delete_event(self, event):
        self._show_pin_dialog()
        return True
