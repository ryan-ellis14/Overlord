import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2

w = Gtk.Window(title="WebKit Test")
w.set_default_size(800, 600)
w.connect("destroy", Gtk.main_quit)

v = WebKit2.WebView()
v.load_uri("https://www.google.com")
w.add(v)
w.show_all()

Gtk.main()