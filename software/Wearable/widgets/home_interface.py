"""Clean home screen: clock, Media, Settings, and the Pi power button."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from background import AnimatedBackground
from widgets.clock import Clock
from widgets.glow_icon_button import GlowIconButton
from widgets.shut_down_button import ShutDownButton


class HomeInterface(QWidget):
    nav_to_settings = Signal()
    nav_to_media = Signal()

    def __init__(self, parent=None, enable_shutdown=False):
        super().__init__(parent)
        self.background = AnimatedBackground(self)
        self.background.lower()
        self.clock = Clock(self)
        self.shut_down_button = ShutDownButton(self, enable_shutdown=enable_shutdown)
        self.settings_button = GlowIconButton("settings.svg", "Settings", self)
        self.settings_button.clicked.connect(self.nav_to_settings.emit)
        self.media_button = GlowIconButton("media.svg", "Media", self)
        self.media_button.clicked.connect(self.nav_to_media.emit)

        self.icon_buttons = (
            self.settings_button,
            self.media_button,
            self.shut_down_button,
        )
        for button in self.icon_buttons:
            button.emphasis_changed.connect(self.background.update)

    def resizeEvent(self, event):
        self.background.setGeometry(self.rect())
        self.clock.move((self.width() - self.clock.width()) // 2, 20)
        self.settings_button.move(self.width() - 80, 20)
        self.media_button.move(30, self.height() - 80)
        self.shut_down_button.move(self.width() - 80, self.height() - 80)
        self.background.set_button_glows(self.icon_buttons)
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        for button in self.icon_buttons:
            button.reset_emphasis()
