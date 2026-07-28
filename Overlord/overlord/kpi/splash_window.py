import logging

from .kpi_config import KpiConfig, DEFAULT_ROTATION_INTERVAL

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

logger = logging.getLogger("overlord-kpi")

SPLASH_CSS = """
    .kpi-splash-title {
        color: #4a90d9;
        font-size: 36px;
        font-weight: bold;
    }
    .kpi-splash-subtitle {
        color: #888;
        font-size: 14px;
    }
    .kpi-section-title {
        color: #4a90d9;
        font-size: 15px;
        font-weight: bold;
    }
    .kpi-label {
        color: #ccc;
        font-size: 13px;
    }
    .kpi-hint {
        color: #666;
        font-size: 11px;
    }
    .kpi-entry {
        background-color: #2a2a2a;
        color: white;
        border-radius: 4px;
    }
    .kpi-btn-launch {
        background-color: #4a90d9;
        color: white;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
    }
    .kpi-btn-launch:hover {
        background-color: #5aa0e9;
    }
    .kpi-btn-exit {
        background-color: #3a3a3a;
        color: #aaa;
        border-radius: 6px;
        font-size: 14px;
    }
    .kpi-btn-exit:hover {
        background-color: #4a4a4a;
        color: white;
    }
    .kpi-btn-add {
        background-color: #27ae60;
        color: white;
        border-radius: 4px;
        font-size: 12px;
    }
    .kpi-btn-add:hover {
        background-color: #2ecc71;
    }
    .kpi-btn-remove {
        background-color: #e74c3c;
        color: white;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
    }
    .kpi-btn-remove:hover {
        background-color: #f05a4a;
    }
    .kpi-status {
        color: #27ae60;
        font-size: 13px;
    }
    .kpi-error {
        color: #e74c3c;
        font-size: 13px;
    }
    .kpi-keys-hint {
        color: #555;
        font-size: 11px;
    }
"""


class SplashWindow(Gtk.Window):

    def __init__(self, config, on_launch, on_exit):
        super().__init__(title="Overlord - KPI")
        self._config = config
        self._on_launch = on_launch
        self._on_exit = on_exit
        self._url_entries = []

        self.set_decorated(False)
        self.set_default_size(560, 520)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.stick()

        self._provider = Gtk.CssProvider()
        self._provider.load_from_data(SPLASH_CSS.encode())

        self._setup_ui()
        self._load_config()

    def _apply(self, widget):
        widget.get_style_context().add_provider(
            self._provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        return widget

    def _setup_ui(self):
        bg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        bg.set_name("kpi-splash")
        bg.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.08, 0.08, 0.12, 1.0))

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.set_border_width(20)

        title = Gtk.Label(label="Overlord - KPI")
        title.set_name("kpi-splash-title")
        self._apply(title)
        title.set_halign(Gtk.Align.CENTER)
        header.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Dual-Screen KPI Display")
        subtitle.set_name("kpi-splash-subtitle")
        self._apply(subtitle)
        subtitle.set_halign(Gtk.Align.CENTER)
        header.pack_start(subtitle, False, False, 0)

        bg.pack_start(header, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        inner.set_border_width(16)

        inner.pack_start(self._create_left_section(), False, False, 0)
        inner.pack_start(self._create_right_section(), False, False, 0)
        inner.pack_start(self._create_interval_section(), False, False, 0)

        scrolled.add(inner)
        bg.pack_start(scrolled, True, True, 0)

        btn_box = Gtk.Box(spacing=12)
        btn_box.set_border_width(12)
        btn_box.set_halign(Gtk.Align.CENTER)

        launch_btn = Gtk.Button(label="  Launch  ")
        launch_btn.set_name("kpi-btn-launch")
        self._apply(launch_btn)
        launch_btn.connect("clicked", self._do_launch)
        btn_box.pack_start(launch_btn, False, False, 0)

        exit_btn = Gtk.Button(label="  Exit  ")
        exit_btn.set_name("kpi-btn-exit")
        self._apply(exit_btn)
        exit_btn.connect("clicked", self._do_exit)
        btn_box.pack_start(exit_btn, False, False, 0)

        bg.pack_start(btn_box, False, False, 0)

        self._status_label = Gtk.Label(label="")
        self._status_label.set_halign(Gtk.Align.CENTER)
        self._status_label.set_no_show_all(True)
        self._status_label.set_margin_bottom(8)
        bg.pack_start(self._status_label, False, False, 0)

        keys_hint = Gtk.Label(label="Exit KPI display: Ctrl+Shift+X")
        keys_hint.set_name("kpi-keys-hint")
        self._apply(keys_hint)
        keys_hint.set_halign(Gtk.Align.CENTER)
        keys_hint.set_margin_bottom(10)
        bg.pack_start(keys_hint, False, False, 0)

        self.add(bg)
        self.connect("key-press-event", self._on_key_press)

    def _create_section(self, title_text):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.12, 0.12, 0.16, 1.0))

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_border_width(12)

        title = Gtk.Label(label=title_text)
        title.set_name("kpi-section-title")
        self._apply(title)
        title.set_halign(Gtk.Align.START)
        vbox.pack_start(title, False, False, 0)

        frame.add(vbox)
        return frame, vbox

    def _create_left_section(self):
        frame, vbox = self._create_section("Left Screen (Static)")

        hint = Gtk.Label(label="Leave blank to disable this screen")
        hint.set_name("kpi-hint")
        self._apply(hint)
        hint.set_halign(Gtk.Align.START)
        vbox.pack_start(hint, False, False, 0)

        self._left_url_entry = Gtk.Entry()
        self._left_url_entry.set_name("kpi-entry")
        self._apply(self._left_url_entry)
        self._left_url_entry.set_placeholder_text("https://example.com/left-page")
        vbox.pack_start(self._left_url_entry, False, False, 0)

        return frame

    def _create_right_section(self):
        frame, vbox = self._create_section("Right Screen (Rotating)")

        self._url_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        add_btn = Gtk.Button(label="+ Add URL")
        add_btn.set_name("kpi-btn-add")
        self._apply(add_btn)
        add_btn.connect("clicked", self._add_url_row)

        add_box = Gtk.Box()
        add_box.pack_end(add_btn, False, False, 0)
        self._url_container.pack_start(add_box, False, False, 0)

        vbox.pack_start(self._url_container, False, False, 0)

        return frame

    def _create_interval_section(self):
        frame, vbox = self._create_section("Rotation Interval")

        row = Gtk.Box(spacing=8)

        self._interval_spin = Gtk.SpinButton.new_with_range(5, 3600, 5)
        self._interval_spin.set_value(DEFAULT_ROTATION_INTERVAL)
        self._interval_spin.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0.17, 0.17, 0.17, 1.0)
        )
        self._interval_spin.override_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1)
        )
        row.pack_start(self._interval_spin, False, False, 0)

        label = Gtk.Label(label="seconds")
        label.set_name("kpi-label")
        self._apply(label)
        row.pack_start(label, False, False, 0)

        vbox.pack_start(row, False, False, 0)

        return frame

    def _load_config(self):
        self._left_url_entry.set_text(self._config.get_left_screen_url())

        for url in self._config.get_rotation_urls():
            self._add_url_row(url_value=url)

        if not self._url_entries:
            self._add_url_row()

        self._interval_spin.set_value(self._config.get_rotation_interval())

    def _add_url_row(self, widget=None, url_value=""):
        row = Gtk.Box(spacing=6)

        index = len(self._url_entries) + 1
        num = Gtk.Label(label=f"{index}.")
        num.set_size_request(24, -1)
        num.set_name("kpi-label")
        self._apply(num)
        row.pack_start(num, False, False, 0)

        entry = Gtk.Entry()
        entry.set_name("kpi-entry")
        self._apply(entry)
        entry.set_placeholder_text("https://example.com/kpi-page")
        entry.set_text(url_value)
        row.pack_start(entry, True, True, 0)

        remove_btn = Gtk.Button(label="X")
        remove_btn.set_name("kpi-btn-remove")
        remove_btn.set_size_request(24, 24)
        self._apply(remove_btn)
        remove_btn.connect("clicked", lambda w, e=entry, n=num, r=row: self._remove_url(e, n, r))
        row.pack_start(remove_btn, False, False, 0)

        self._url_entries.append(entry)
        parent = self._url_container
        parent.reorder_child(row, -2)
        parent.pack_start(row, False, False, 0)
        row.show_all()

    def _remove_url(self, entry, num_label, row):
        if len(self._url_entries) <= 1:
            self._show_status("At least one URL is required.", error=True)
            return
        self._url_entries.remove(entry)
        self._url_container.remove(row)
        self._renumber()

    def _renumber(self):
        children = self._url_container.get_children()
        url_idx = 0
        for child in children:
            if isinstance(child, Gtk.Box):
                sub_children = child.get_children()
                for sc in sub_children:
                    if isinstance(sc, Gtk.Label) and sc.get_text().endswith("."):
                        url_idx += 1
                        sc.set_text(f"{url_idx}.")
                        break

    def _do_launch(self, widget):
        left_url = self._left_url_entry.get_text().strip()
        rotation_urls = [
            e.get_text().strip() for e in self._url_entries if e.get_text().strip()
        ]
        interval = self._interval_spin.get_value_as_int()

        if not rotation_urls:
            self._show_status("At least one rotation URL is required.", error=True)
            return

        self._config.save_config(left_url, rotation_urls, interval)
        self.destroy()
        self._on_launch(left_url, rotation_urls, interval)

    def _do_exit(self, widget):
        self.destroy()
        self._on_exit()

    def _show_status(self, msg, error=False):
        self._status_label.set_text(msg)
        self._status_label.set_name("kpi-error" if error else "kpi-status")
        self._apply(self._status_label)
        self._status_label.show()
        GLib.timeout_add(3000, lambda: (self._status_label.hide(), False)[1])

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self._do_exit(None)
            return True
        return False