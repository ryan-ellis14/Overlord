import logging

from .webview_widget import KpiWebview

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

logger = logging.getLogger("overlord-kpi")


class KpiDisplay:

    def __init__(self, left_url, rotation_urls, rotation_interval, on_exit):
        self._left_url = left_url
        self._rotation_urls = rotation_urls
        self._rotation_interval = rotation_interval
        self._on_exit = on_exit
        self._current_rotation_index = 0
        self._rotation_timer = None
        self._windows = []
        self._right_webview = None

        self._setup_screens()
        self._setup_rotation_timer()
        logger.info("KPI display started: left=%s, %d rotation URLs, %ds interval",
                     "enabled" if left_url else "disabled",
                     len(rotation_urls), rotation_interval)

    def _setup_screens(self):
        screen = Gdk.Screen.get_default()
        n_monitors = screen.get_n_monitors()
        logger.info("Detected %d monitor(s)", n_monitors)

        if n_monitors >= 2:
            geo_left = screen.get_monitor_geometry(0)
            geo_right = screen.get_monitor_geometry(1)
        else:
            geo_left = None
            geo_right = screen.get_monitor_geometry(0)

        if geo_left and self._left_url:
            left_win = self._create_browser_window(geo_left, self._left_url)
            self._windows.append(left_win)
        elif geo_left:
            blank_win = Gtk.Window()
            blank_win.set_decorated(False)
            blank_win.move(geo_left.x, geo_left.y)
            blank_win.resize(geo_left.width, geo_left.height)
            blank_win.override_background_color(
                Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1)
            )
            blank_win.stick()
            blank_win.connect("key-press-event", self._on_key_press)
            blank_win.connect("delete-event", lambda w, e: True)
            blank_win.show()
            self._windows.append(blank_win)

        first_url = self._rotation_urls[0] if self._rotation_urls else "about:blank"
        right_win = self._create_browser_window(geo_right, first_url)
        self._right_webview = right_win.get_child()
        self._windows.append(right_win)

    def _create_browser_window(self, geo, url):
        win = Gtk.Window()
        win.set_decorated(False)
        win.move(geo.x, geo.y)
        win.resize(geo.width, geo.height)
        win.stick()

        webview = KpiWebview(url)
        win.add(webview)

        win.connect("key-press-event", self._on_key_press)
        win.connect("delete-event", lambda w, e: True)
        win.show_all()

        return win

    def _on_key_press(self, widget, event):
        state = event.state
        if (event.keyval == Gdk.KEY_x
                and state & Gdk.ModifierType.CONTROL_MASK
                and state & Gdk.ModifierType.SHIFT_MASK):
            logger.info("Ctrl+Shift+X pressed, returning to splash")
            GLib.idle_add(self._exit_to_splash)
            return True
        return False

    def _exit_to_splash(self):
        self.destroy()
        if self._on_exit:
            self._on_exit()

    def _setup_rotation_timer(self):
        if len(self._rotation_urls) > 1 and self._rotation_interval > 0:
            self._rotation_timer = GLib.timeout_add_seconds(
                self._rotation_interval, self._rotate
            )
            logger.info("Rotation timer set: %ds", self._rotation_interval)

    def _rotate(self):
        self._current_rotation_index = (
            (self._current_rotation_index + 1) % len(self._rotation_urls)
        )
        url = self._rotation_urls[self._current_rotation_index]
        logger.info("Rotating to URL %d/%d: %s",
                     self._current_rotation_index + 1,
                     len(self._rotation_urls), url)
        self._right_webview.load_url(url)
        return True

    def destroy(self):
        if self._rotation_timer:
            GLib.source_remove(self._rotation_timer)
            self._rotation_timer = None
        for win in self._windows:
            win.destroy()
        self._windows.clear()
        self._right_webview = None