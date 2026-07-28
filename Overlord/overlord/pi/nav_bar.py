import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

import logging

logger = logging.getLogger("overlord")


BAR_STYLE = """
    .overlord-nav-bar {
        background-color: #1a3a6e;
        border-top: 2px solid #2a5a9e;
    }
    .overlord-indicator {
        color: #c8c8c8;
        font-size: 14px;
        font-weight: bold;
    }
"""


class PillButton(Gtk.Button):

    __gtype_name__ = "PillButton"

    def __init__(self, direction="left"):
        super().__init__()
        self._direction = direction
        self.set_size_request(60, 36)
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.get_style_context().add_class("overlord-pill")

    def do_draw(self, cr):
        Gtk.Button.do_draw(self, cr)
        w = self.get_allocated_width()
        h = self.get_allocated_height()
        ctx = self.get_style_context()

        cr.set_source_rgba(0.9, 0.94, 1.0, 0.94)
        cx, cy = w / 2, h / 2
        s = 8
        if self._direction == "left":
            cr.move_to(cx + s, cy - s)
            cr.line_to(cx - s, cy)
            cr.line_to(cx + s, cy + s)
        else:
            cr.move_to(cx - s, cy - s)
            cr.line_to(cx + s, cy)
            cr.line_to(cx - s, cy + s)
        cr.close_path()
        cr.fill()


class SecretPillButton(PillButton):

    __gtype_name__ = "SecretPillButton"

    __gsignals__ = {
        "secret-activated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, direction="right"):
        super().__init__(direction)
        self._tap_count = 0
        self._last_tap_time = 0
        self._tap_interval = 1500

    def do_button_press_event(self, event):
        import time
        now = time.time() * 1000
        if now - self._last_tap_time < self._tap_interval and self._last_tap_time > 0:
            self._tap_count += 1
            if self._tap_count >= 5:
                self._tap_count = 0
                self.emit("secret-activated")
                return True
        else:
            self._tap_count = 1
        self._last_tap_time = now
        self.emit("clicked")
        return True


class NavBar(Gtk.Box):

    __gtype_name__ = "NavBar"

    __gsignals__ = {
        "prev-clicked": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "next-clicked": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "secret-activated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, current, total):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_name("overlord-nav-bar")
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.END)

        self._provider = Gtk.CssProvider()
        self._provider.load_from_data(BAR_STYLE.encode())
        self.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self._btn_prev = PillButton("left")
        self._btn_prev.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0.27, 0.51, 0.82, 0.79)
        )
        self._btn_prev.connect("clicked", lambda w: self.emit("prev-clicked"))

        self._label = Gtk.Label(label=f"{current + 1} / {total}")
        self._label.set_name("overlord-indicator")
        self._label.set_margin_left(12)
        self._label.set_margin_right(12)
        self._label.override_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0.78, 0.78, 0.78, 0.78)
        )

        self._btn_next = SecretPillButton("right")
        self._btn_next.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0.27, 0.51, 0.82, 0.79)
        )
        self._btn_next.connect("clicked", lambda w: self.emit("next-clicked"))
        self._btn_next.connect("secret-activated", lambda w: self.emit("secret-activated"))

        self.pack_start(self._btn_prev, False, False, 16)
        self.set_center_widget(self._label)
        self.pack_end(self._btn_next, False, False, 16)
        self.show_all()

    def set_page(self, current, total):
        self._label.set_text(f"{current + 1} / {total}")
