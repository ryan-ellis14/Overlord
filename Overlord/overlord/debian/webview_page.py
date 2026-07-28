import logging

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtNetwork import QNetworkProxy
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMenu, QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
)

logger = logging.getLogger("overlord")


class WebViewPage(QWebEnginePage):

    def certificateError(self, certificateError):
        logger.warning("Ignoring SSL certificate error for: %s", certificateError.url().toString())
        return True

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if url.toString().lower().endswith(".pdf"):
            logger.debug("Intercepting PDF navigation to: %s", url.toString())
            self.setUrl(url)
            return False
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)

    def createWindow(self, window_type):
        new_page = WebViewPage(self.profile(), self.view())
        self.view().setPage(new_page)
        return new_page


class WebviewPage(QWidget):

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent(
            profile.httpUserAgent() + " Overlord/1.0"
        )

        page = WebViewPage(profile, self)

        self.web_view = QWebEngineView()
        self.web_view.setPage(page)
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.PdfViewerEnabled, True
        )


        layout.addWidget(self.web_view)

        logger.debug("Loading URL: %s", self._url)
        self.web_view.load(QUrl(self._url))

    def reload(self):
        self.web_view.reload()

    def url(self) -> str:
        return self._url
