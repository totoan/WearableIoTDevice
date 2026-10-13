"""Arrange the animated background, clock, and power button on the home page."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

from background import AnimatedBackground
from widgets.clock import Clock
from widgets.shut_down_button import ShutDownButton


class HomeInterface(QWidget):
    nav_to_dashboard = Signal()
    nav_to_youtube = Signal()
    nav_to_roku = Signal()

    def __init__(self, parent=None, enable_shutdown=False):
        super().__init__(parent)
        self.background = AnimatedBackground(self)
        self.background.lower()
        self.clock = Clock(self)
        self.shut_down_button = ShutDownButton(self, enable_shutdown=enable_shutdown)
        self.dashboard_button = QPushButton("PC Dashboard", self)
        self.dashboard_button.setFixedSize(140, 40)
        self.dashboard_button.clicked.connect(self.nav_to_dashboard.emit)
        self.youtube_button = QPushButton("YouTube", self)
        self.youtube_button.setFixedSize(120, 40)
        self.youtube_button.clicked.connect(self.nav_to_youtube.emit)
        self.roku_button = QPushButton("Living Room TV", self)
        self.roku_button.setFixedSize(150, 40)
        self.roku_button.clicked.connect(self.nav_to_roku.emit)
        self.connection_label = QLabel("PC: not paired", self)
        self.connection_label.setFixedSize(350, 30)

    def resizeEvent(self, event):
        self.background.setGeometry(self.rect())
        self.clock.move((self.width() - self.clock.width()) // 2, 20)
        self.shut_down_button.move(self.width() - 80, self.height() - 60)
        self.dashboard_button.move(20, self.height() - 60)
        self.youtube_button.move(200, self.height() - 60)
        self.roku_button.move(350, self.height() - 60)
        self.connection_label.move(20, self.height() - 100)
        self.background.set_button_glows([self.shut_down_button.geometry().center()])
        super().resizeEvent(event)
