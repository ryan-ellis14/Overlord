import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2

import logging

logger = logging.getLogger("overlord-kpi")

OVERLAY_JS = """
(function() {
    if (document.getElementById('overlord-hide-scroll')) return;
    var style = document.createElement('style');
    style.id = 'overlord-hide-scroll';
    style.textContent = 'html::-webkit-scrollbar{display:none}body::-webkit-scrollbar{display:none}';
    document.head.appendChild(style);
})();
"""


class KpiWebview(Gtk.Bin):

    def __init__(self, url):
        super().__init__()
        self._url = url

        self._webview = WebKit2.WebView()
        self._setup_user_agent()
        self._setup_content_manager()
        self._setup_settings()

        self._webview.load_uri(url)
        self._webview.connect("load-changed", self._on_load_changed)

        self.add(self._webview)
        self.show_all()
        logger.debug("KpiWebview created for: %s", url)

    def _setup_user_agent(self):
        settings = self._webview.get_settings()
        ua = settings.get_user_agent()
        if ua and "Overlord" not in ua:
            settings.set_user_agent(ua + " Overlord/KPI")

    def _setup_content_manager(self):
        manager = self._webview.get_user_content_manager()
        script = WebKit2.UserScript.new(
            OVERLAY_JS,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserScriptInjectionTime.END,
            None, None,
        )
        manager.add_script(script)

    def _setup_settings(self):
        settings = self._webview.get_settings()
        settings.set_enable_javascript(True)
        settings.set_enable_plugins(False)
        settings.set_auto_load_images(True)

    def _on_load_changed(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            logger.debug("KpiWebview loaded: %s", self._url)

    def reload(self):
        self._webview.reload()

    def load_url(self, url):
        self._url = url
        self._webview.load_uri(url)