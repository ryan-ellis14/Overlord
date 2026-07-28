import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

import logging

logger = logging.getLogger("overlord")


BLUE = Gdk.RGBA(0.15, 0.36, 0.69, 1.0)
WHITE = Gdk.RGBA(1, 1, 1, 1.0)
DARK_BLUE = Gdk.RGBA(0.1, 0.25, 0.5, 1.0)
LIGHT_GREY = Gdk.RGBA(0.95, 0.95, 0.95, 1.0)
BTN_BORDER = Gdk.RGBA(0.2, 0.2, 0.2, 1.0)


DIALOG_CSS = """
    .overlord-pin-title {
        color: white;
        font-size: 16px;
        font-weight: bold;
    }
    .overlord-pin-feedback {
        color: #ffcccc;
        font-size: 13px;
    }
    .overlord-numpad-btn {
        min-width: 70px;
        min-height: 60px;
        background-color: #d0d0d0;
        color: black;
        border-radius: 8px;
        font-size: 24px;
        font-weight: bold;
        border: 2px solid #333;
        outline: none;
    }
    .overlord-numpad-btn:hover,
    .overlord-numpad-btn:active,
    .overlord-numpad-btn:focus {
        background-color: #d0d0d0;
        color: black;
    }
    .overlord-action-btn {
        padding: 8px 24px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        color: white;
        background-color: #7ab4f0;
        border: 2px solid white;
    }
"""


class PinDialog(Gtk.Window):

    __gtype_name__ = "PinDialog"

    __gsignals__ = {
        "exit-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "settings-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "kiosk-settings-requested": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, exit_pin, settings_pin, kiosk_settings_pin):
        super().__init__(type=Gtk.WindowType.POPUP)
        self._exit_pin = exit_pin
        self._settings_pin = settings_pin
        self._kiosk_settings_pin = kiosk_settings_pin
        self._current_entry = ""

        self.set_decorated(False)
        self.set_modal(True)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_default_size(300, 400)
        self.set_accept_focus(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.stick()

        self._provider = Gtk.CssProvider()
        self._provider.load_from_data(DIALOG_CSS.encode())

        self._setup_ui()
        self.connect("key-press-event", self._on_key_press)

    def _apply_style(self, widget, name=None):
        if name:
            widget.set_name(name)
        widget.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        return widget

    def _setup_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.override_background_color(Gtk.StateFlags.NORMAL, BLUE)
        outer.set_border_width(0)
        self.add(outer)

        title = self._apply_style(Gtk.Label(label="Enter 4-digit PIN"), "overlord-pin-title")
        title.set_halign(Gtk.Align.CENTER)
        title.set_margin_top(16)
        outer.pack_start(title, False, False, 0)

        dots_box = Gtk.Box(spacing=12)
        dots_box.set_halign(Gtk.Align.CENTER)
        dots_box.set_margin_top(8)
        self._pin_dots = []
        for _ in range(4):
            dot = Gtk.DrawingArea()
            dot.set_size_request(22, 22)
            dots_box.pack_start(dot, False, False, 0)
            self._pin_dots.append(dot)
        outer.pack_start(dots_box, False, False, 0)

        self._feedback_label = self._apply_style(
            Gtk.Label(label=""), "overlord-pin-feedback"
        )
        self._feedback_label.set_halign(Gtk.Align.CENTER)
        self._feedback_label.set_no_show_all(True)
        self._feedback_label.hide()
        self._feedback_label.set_margin_top(4)
        outer.pack_start(self._feedback_label, False, False, 0)

        numpad_area = Gtk.Box()
        numpad_area.override_background_color(Gtk.StateFlags.NORMAL, WHITE)

        numpad_grid = Gtk.Grid()
        numpad_grid.set_column_spacing(6)
        numpad_grid.set_row_spacing(6)
        numpad_grid.set_halign(Gtk.Align.CENTER)
        numpad_grid.set_margin_top(10)
        numpad_grid.set_margin_bottom(10)
        numpad_grid.set_margin_left(20)
        numpad_grid.set_margin_right(20)

        buttons = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", ""]
        for i, label in enumerate(buttons):
            col = i % 3
            row = i // 3
            if label == "":
                spacer = Gtk.Label(label="")
                spacer.set_size_request(70, 60)
                numpad_grid.attach(spacer, col, row, 1, 1)
                continue
            btn = self._apply_style(Gtk.Button(label=label), "overlord-numpad-btn")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.connect("clicked", lambda w, d=label: self._add_digit(d))
            numpad_grid.attach(btn, col, row, 1, 1)

        numpad_area.pack_start(numpad_grid, True, True, 0)
        outer.pack_start(numpad_area, True, True, 0)

        footer = Gtk.Box()
        footer.override_background_color(Gtk.StateFlags.NORMAL, BLUE)
        footer.set_margin_top(0)

        action_row = Gtk.Box(spacing=16)
        action_row.set_halign(Gtk.Align.CENTER)
        action_row.set_margin_top(8)
        action_row.set_margin_bottom(12)

        cancel_btn = self._apply_style(Gtk.Button(label="Cancel"), "overlord-action-btn")
        cancel_btn.set_relief(Gtk.ReliefStyle.NONE)
        cancel_btn.connect("clicked", self._on_cancel)

        clear_btn = self._apply_style(Gtk.Button(label="Clear"), "overlord-action-btn")
        clear_btn.set_relief(Gtk.ReliefStyle.NONE)
        clear_btn.connect("clicked", self._clear_entry)

        action_row.pack_start(cancel_btn, False, False, 0)
        action_row.pack_start(clear_btn, False, False, 0)
        footer.pack_start(action_row, False, False, 0)
        outer.pack_start(footer, False, False, 0)

        self.show_all()
        self._current_entry = ""
        self._update_dots()
        self._feedback_label.hide()

    def _add_digit(self, digit):
        if len(self._current_entry) >= 4:
            return
        self._current_entry += digit
        self._update_dots()
        self._feedback_label.hide()
        if len(self._current_entry) == 4:
            self._check_pin()

    def _clear_entry(self):
        self._current_entry = ""
        self._update_dots()
        self._feedback_label.hide()

    def _update_dots(self):
        for i, dot in enumerate(self._pin_dots):
            if i < len(self._current_entry):
                dot.override_background_color(Gtk.StateFlags.NORMAL, WHITE)
            else:
                dot.override_background_color(Gtk.StateFlags.NORMAL, DARK_BLUE)

    def _check_pin(self):
        pin = self._current_entry
        if pin == self._exit_pin:
            logger.debug("Exit PIN correct")
            self.emit("exit-requested")
            self.destroy()
        elif pin == self._settings_pin:
            logger.debug("Settings PIN correct")
            self.emit("settings-requested")
            self.destroy()
        elif pin == self._kiosk_settings_pin:
            logger.debug("Kiosk Settings PIN correct")
            self.emit("kiosk-settings-requested")
            self.destroy()
        else:
            self._feedback_label.set_text("Incorrect PIN")
            self._feedback_label.show()
            self._current_entry = ""
            self._update_dots()

    def _on_cancel(self, widget):
        self.destroy()

    def _on_key_press(self, widget, event):
        key = event.keyval
        if key == Gdk.KEY_Escape:
            self.destroy()
            return True
        elif key == Gdk.KEY_BackSpace:
            if self._current_entry:
                self._current_entry = self._current_entry[:-1]
                self._update_dots()
            return True
        elif Gdk.KEY_0 <= key <= Gdk.KEY_9:
            self._add_digit(chr(key))
            return True
        elif Gdk.KEY_KP_0 <= key <= Gdk.KEY_KP_9:
            self._add_digit(chr(key - Gdk.KEY_KP_0 + ord('0')))
            return True
        return False
