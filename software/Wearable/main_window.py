"""Main window and page container, following the Legacy application structure."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from widgets.home_interface import HomeInterface
from widgets.dashboard_interface import DashboardInterface
from widgets.youtube_interface import YouTubeInterface
from widgets.roku_interface import RokuInterface
from widgets.settings_interface import SettingsInterface
from widgets.media_interface import MediaInterface
from widgets.microphone_interface import MicrophoneInterface
from models.speech_handler import SpeechHandler
from models.wifi_handler import WifiHandler
from widgets.wifi_interface import WifiInterface


class MainWindow(QMainWindow):
    def __init__(self, enable_shutdown=False, parent=None, dashboard_handler=None, youtube_handler=None, roku_handler=None):
        super().__init__(parent)
        self.setWindowTitle("Pi5 Wearable" if enable_shutdown else "Pi5 Wearable — Preview")
        self.resize(800, 480)
        self.setMinimumSize(400, 240)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.home_page = HomeInterface(enable_shutdown=enable_shutdown)
        self.stack.addWidget(self.home_page)
        self.stack.setCurrentWidget(self.home_page)
        self.settings_page = SettingsInterface(dashboard_handler)
        self.media_page = MediaInterface(
            youtube_enabled=youtube_handler is not None,
            roku_enabled=roku_handler is not None,
        )
        self.speech_handler = SpeechHandler.shared()
        self.speech_handler.dashboard = dashboard_handler
        self.microphone_page = MicrophoneInterface(self.speech_handler)
        self.wifi_handler = WifiHandler(self)
        self.wifi_page = WifiInterface(self.wifi_handler)
        QApplication.instance().aboutToQuit.connect(self.wifi_handler.stop)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.media_page)
        self.stack.addWidget(self.microphone_page)
        self.stack.addWidget(self.wifi_page)
        self.home_page.nav_to_settings.connect(self.open_settings)
        self.home_page.nav_to_media.connect(self.open_media)
        self.settings_page.nav_to_home.connect(self.open_home)
        self.media_page.nav_to_home.connect(self.open_home)
        self.settings_page.nav_to_microphone.connect(
            lambda: self.stack.setCurrentWidget(self.microphone_page)
        )
        self.microphone_page.nav_back.connect(self.open_settings)
        self.settings_page.nav_to_wifi.connect(lambda: self.stack.setCurrentWidget(self.wifi_page))
        self.wifi_page.nav_back.connect(self.open_settings)

        if dashboard_handler is not None:
            self.dashboard_page = DashboardInterface(dashboard_handler)
            self.stack.addWidget(self.dashboard_page)
            self.settings_page.nav_to_dashboard.connect(
                lambda: self.stack.setCurrentWidget(self.dashboard_page)
            )
            self.dashboard_page.nav_back.connect(self.open_settings)

        if youtube_handler is not None:
            self.youtube_page = YouTubeInterface(youtube_handler)
            self.stack.addWidget(self.youtube_page)
            self.media_page.nav_to_youtube.connect(
                lambda: self.stack.setCurrentWidget(self.youtube_page)
            )
            self.youtube_page.nav_back.connect(self.open_media)

        if roku_handler is not None:
            self.roku_page = RokuInterface(roku_handler)
            self.stack.addWidget(self.roku_page)
            self.media_page.nav_to_roku.connect(
                lambda: self.stack.setCurrentWidget(self.roku_page)
            )
            self.roku_page.nav_back.connect(self.open_media)

    def open_home(self):
        self.stack.setCurrentWidget(self.home_page)

    def open_settings(self):
        self.stack.setCurrentWidget(self.settings_page)

    def open_media(self):
        self.stack.setCurrentWidget(self.media_page)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            current = self.stack.currentWidget()
            if current == self.home_page:
                self.close()
            elif current in (getattr(self, "dashboard_page", None), self.microphone_page, self.wifi_page):
                self.open_settings()
            elif current in (getattr(self, "youtube_page", None), getattr(self, "roku_page", None)):
                self.open_media()
            else:
                self.open_home()
        else:
            super().keyPressEvent(event)
