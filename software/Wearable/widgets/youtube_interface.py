"""The three-tab YouTube page; each tab has its own file."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from models.thumbnail_handler import ThumbnailHandler
from widgets.youtube.now_playing_interface import NowPlayingInterface
from widgets.youtube.search_interface import SearchInterface
from widgets.youtube.subscriptions_interface import SubscriptionsInterface


class YouTubeInterface(QWidget):
    nav_back = Signal()

    def __init__(self, handler, parent=None):
        super().__init__(parent)
        self.thumbnails = ThumbnailHandler(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel("YouTube")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self.connection_label = QLabel("PC connected" if handler.connected else "PC disconnected")
        self.connection_label.setStyleSheet("font-size: 14px;")
        handler.connection_changed.connect(self.update_connection)
        header.addWidget(self.connection_label)

        home = QPushButton("Back")
        home.clicked.connect(self.nav_back.emit)
        header.addWidget(home)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.now_playing_page = NowPlayingInterface(handler.playback, self.thumbnails)
        self.subscriptions_page = SubscriptionsInterface(handler, self.thumbnails)
        self.search_page = SearchInterface(handler, self.thumbnails)
        self.tabs.addTab(self.now_playing_page, "Now Playing")
        self.tabs.addTab(self.subscriptions_page, "Subscriptions")
        self.tabs.addTab(self.search_page, "Search")
        self.tabs.setCurrentWidget(self.subscriptions_page)
        handler.playback.video_started.connect(
            lambda: self.tabs.setCurrentWidget(self.now_playing_page)
        )
        layout.addWidget(self.tabs, 1)

    def update_connection(self, connected):
        self.connection_label.setText("PC connected" if connected else "PC disconnected")
