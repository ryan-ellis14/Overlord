import logging

from ..config import (
    MAX_URLS,
    DEFAULT_URLS,
    GESTURE_TYPES,
    GESTURE_LABELS,
)
from ..pin_manager import PinManager

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GLib

logger = logging.getLogger("overlord")

SETTINGS_CSS = """
    .overlord-settings-title {
        color: #4a90d9;
        font-size: 22px;
        font-weight: bold;
    }
    .overlord-section-title {
        color: #4a90d9;
        font-size: 16px;
        font-weight: bold;
    }
    .overlord-label {
        color: #ddd;
        font-size: 14px;
    }
    .overlord-entry {
        background-color: #3a3a3a;
        color: white;
        border-radius: 6px;
    }
    .overlord-combo {
        background-color: #3a3a3a;
        color: white;
        border-radius: 6px;
    }
    .overlord-btn-primary {
        background-color: #4a90d9;
        color: white;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
    }
    .overlord-btn-primary:hover {
        background-color: #5aa0e9;
    }
    .overlord-btn-cancel {
        background-color: #666;
        color: white;
        border-radius: 8px;
        font-size: 14px;
    }
    .overlord-btn-cancel:hover {
        background-color: #777;
    }
    .overlord-btn-save-pin {
        background-color: #e74c3c;
        color: white;
        border-radius: 6px;
        font-size: 12px;
    }
    .overlord-btn-save-pin:hover {
        background-color: #f05a4a;
    }
    .overlord-btn-add-url {
        background-color: #27ae60;
        color: white;
        border-radius: 6px;
        font-size: 13px;
    }
    .overlord-btn-add-url:hover {
        background-color: #2ecc71;
    }
    .overlord-btn-remove {
        background-color: #e74c3c;
        color: white;
        border-radius: 14px;
        font-size: 12px;
        font-weight: bold;
    }
    .overlord-btn-remove:hover {
        background-color: #f05a4a;
    }
    .overlord-status {
        color: #27ae60;
        font-size: 14px;
    }
    .overlord-error {
        color: #e74c3c;
    }
"""


class SettingsWindow(Gtk.Window):

    __gtype_name__ = "PiSettingsWindow"

    __gsignals__ = {
        "settings-applied": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, pin_manager):
        super().__init__(title="Overlord Settings")
        self._pin_manager = pin_manager
        self._url_entries = []
        self._gesture_combo = None

        self.set_decorated(False)
        self.fullscreen()
        self.set_modal(True)
        self.stick()
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self._provider = Gtk.CssProvider()
        self._provider.load_from_data(SETTINGS_CSS.encode())

        self._setup_ui()

    def _setup_ui(self):
        bg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        bg.set_name("overlord-settings")
        bg.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        inner.set_border_width(24)

        title = Gtk.Label(label="Overlord Settings")
        title.set_name("overlord-settings-title")
        title.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        title.set_halign(Gtk.Align.CENTER)
        inner.pack_start(title, False, False, 0)

        inner.pack_start(self._create_pin_section(), False, False, 0)
        inner.pack_start(self._create_url_section(), False, False, 0)
        inner.pack_start(self._create_gesture_section(), False, False, 0)

        scrolled.add(inner)
        bg.pack_start(scrolled, True, True, 0)

        action_row = Gtk.Box(spacing=12)
        action_row.set_halign(Gtk.Align.CENTER)

        save_btn = Gtk.Button(label="Save & Apply")
        save_btn.set_name("overlord-btn-primary")
        save_btn.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        save_btn.connect("clicked", self._save_and_apply)
        action_row.pack_start(save_btn, False, False, 0)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.set_name("overlord-btn-cancel")
        cancel_btn.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        cancel_btn.connect("clicked", lambda w: self.destroy())
        action_row.pack_start(cancel_btn, False, False, 0)

        bg.pack_start(action_row, False, False, 16)

        self._status_label = Gtk.Label(label="")
        self._status_label.set_name("overlord-status")
        self._status_label.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        self._status_label.set_halign(Gtk.Align.CENTER)
        self._status_label.set_no_show_all(True)
        self._status_label.set_margin_bottom(16)
        bg.pack_start(self._status_label, False, False, 0)

        self.add(bg)

        self.set_default_size(480, 600)
        self.connect("key-press-event", self._on_key_press)

    def _apply_provider(self, widget):
        widget.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        return widget

    def _create_section(self, title_text):
        frame = Gtk.Frame()
        frame.set_name("overlord-section")
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(16)

        title = Gtk.Label(label=title_text)
        title.set_name("overlord-section-title")
        title.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        vbox.pack_start(title, False, False, 0)

        frame.add(vbox)
        return frame, vbox

    def _create_pin_section(self):
        frame, vbox = self._create_section("PIN Management")

        for pin_name, attr_name in [
            ("Exit PIN", "get_exit_pin"),
            ("Device Settings PIN", "get_settings_pin"),
            ("Kiosk Settings PIN", "get_kiosk_settings_pin"),
        ]:
            row = Gtk.Box(spacing=8)

            lbl = self._apply_provider(Gtk.Label(label=pin_name + ":"))
            lbl.set_name("overlord-label")
            row.pack_start(lbl, False, False, 0)

            current_field = Gtk.Entry()
            current_field.set_name("overlord-entry")
            current_field.set_placeholder_text("Current PIN")
            self._apply_provider(current_field)
            row.pack_start(current_field, False, False, 0)

            new_field = Gtk.Entry()
            new_field.set_name("overlord-entry")
            new_field.set_placeholder_text("New 4-digit PIN")
            new_field.set_max_length(4)
            self._apply_provider(new_field)
            row.pack_start(new_field, False, False, 0)

            confirm_field = Gtk.Entry()
            confirm_field.set_name("overlord-entry")
            confirm_field.set_placeholder_text("Confirm")
            confirm_field.set_max_length(4)
            self._apply_provider(confirm_field)
            row.pack_start(confirm_field, False, False, 0)

            current_pin = getattr(self._pin_manager, attr_name)()
            save_btn = Gtk.Button(label="Save")
            save_btn.set_name("overlord-btn-save-pin")
            self._apply_provider(save_btn)
            save_btn.connect(
                "clicked",
                lambda w, pn=pin_name, cf=current_field, nf=new_field,
                cfm=confirm_field, cp=current_pin: self._save_pin(
                    pn, cf, nf, cfm, cp
                ),
            )
            row.pack_start(save_btn, False, False, 0)
            vbox.pack_start(row, False, False, 0)

        return frame

    def _save_pin(self, pin_name, current_field, new_field, confirm_field, current_pin):
        current = current_field.get_text().strip()
        new_pin = new_field.get_text().strip()
        confirm = confirm_field.get_text().strip()

        if current != current_pin:
            self._show_status(f"Current {pin_name} is incorrect.", error=True)
            return
        if len(new_pin) != 4 or not new_pin.isdigit():
            self._show_status("PIN must be exactly 4 digits.", error=True)
            return
        if new_pin != confirm:
            self._show_status("New PINs do not match.", error=True)
            return

        if pin_name == "Exit PIN":
            self._pin_manager.save_exit_pin(new_pin)
        elif pin_name == "Device Settings PIN":
            self._pin_manager.save_settings_pin(new_pin)
        elif pin_name == "Kiosk Settings PIN":
            self._pin_manager.save_kiosk_settings_pin(new_pin)

        self._show_status(f"{pin_name} updated.")
        current_field.set_text("")
        new_field.set_text("")
        confirm_field.set_text("")

    def _create_url_section(self):
        frame, vbox = self._create_section("URL Management")
        urls = self._pin_manager.get_urls()
        self._url_entries = []

        for i, url in enumerate(urls):
            vbox.pack_start(self._create_url_row(i, url), False, False, 0)

        add_btn = Gtk.Button(label="+ Add URL")
        add_btn.set_name("overlord-btn-add-url")
        self._apply_provider(add_btn)
        add_btn.connect("clicked", self._add_url_row)
        add_box = Gtk.Box()
        add_box.pack_end(add_btn, False, False, 0)
        vbox.pack_start(add_box, False, False, 0)

        return frame

    def _create_url_row(self, index, url):
        row = Gtk.Box(spacing=8)

        num = Gtk.Label(label=f"{index + 1}.")
        num.set_size_request(28, -1)
        num.set_name("overlord-label")
        self._apply_provider(num)
        row.pack_start(num, False, False, 0)

        entry = Gtk.Entry()
        entry.set_name("overlord-entry")
        entry.set_placeholder_text("https://example.com")
        entry.set_text(url)
        self._apply_provider(entry)
        row.pack_start(entry, True, True, 0)

        remove_btn = Gtk.Button(label="X")
        remove_btn.set_name("overlord-btn-remove")
        remove_btn.set_size_request(28, 28)
        self._apply_provider(remove_btn)
        remove_btn.connect("clicked", lambda w, e=entry, n=num: self._remove_url(e, n))
        row.pack_start(remove_btn, False, False, 0)

        self._url_entries.append(entry)
        return row

    def _add_url_row(self, widget):
        if len(self._url_entries) >= MAX_URLS:
            self._show_status(f"Maximum {MAX_URLS} URLs allowed.", error=True)
            return
        index = len(self._url_entries)
        row = self._create_url_row(index, "")
        parent = self._url_entries[-1].get_parent().get_parent()
        parent.pack_start(row, False, False, 0)
        parent.reorder_child(row, -2)
        row.show_all()

    def _remove_url(self, entry, num_label):
        parent = entry.get_parent()
        if parent:
            parent.remove(entry)
            self._url_entries.remove(entry)
            self._renumber_urls()

    def _renumber_urls(self):
        for i, entry in enumerate(self._url_entries):
            parent = entry.get_parent()
            if parent:
                for child in parent.get_children():
                    if isinstance(child, Gtk.Label) and child.get_text().endswith("."):
                        child.set_text(f"{i + 1}.")
                        break

    def _create_gesture_section(self):
        frame, vbox = self._create_section("Gesture Type")

        self._gesture_combo = Gtk.ComboBoxText()
        self._gesture_combo.set_name("overlord-combo")
        self._apply_provider(self._gesture_combo)

        for gt in GESTURE_TYPES:
            self._gesture_combo.append(gt, GESTURE_LABELS[gt])

        current = self._pin_manager.get_gesture_type()
        if current in GESTURE_TYPES:
            self._gesture_combo.set_active_id(current)
        else:
            self._gesture_combo.set_active(0)

        vbox.pack_start(self._gesture_combo, False, False, 0)
        return frame

    def _save_and_apply(self, widget):
        urls = []
        for entry in self._url_entries:
            url = entry.get_text().strip()
            if url:
                urls.append(url)

        if not urls:
            self._show_status("At least one URL is required.", error=True)
            return

        self._pin_manager.save_urls(urls)
        gesture = self._gesture_combo.get_active_id()
        if gesture:
            self._pin_manager.save_gesture_type(gesture)

        self.emit("settings-applied")
        self.destroy()
        logger.info("Settings saved: %d URLs, gesture=%s", len(urls), gesture)

    def _show_status(self, msg, error=False):
        self._status_label.set_text(msg)
        ctx = self._status_label.get_style_context()
        if error and "overlord-error" not in ctx.list_classes():
            ctx.add_class("overlord-error")
        elif not error:
            ctx.remove_class("overlord-error")
        self._status_label.show()
        GLib.timeout_add(3000, lambda: (self._status_label.hide(), False)[1])

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False
