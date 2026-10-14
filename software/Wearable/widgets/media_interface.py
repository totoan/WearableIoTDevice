"""Media menu for PC YouTube playback and the direct living room TV remote."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class MediaInterface(QWidget):
    nav_to_home = Signal()
    nav_to_youtube = Signal()
    nav_to_roku = Signal()

    def __init__(self, youtube_enabled=True, roku_enabled=True, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        header = QHBoxLayout()
        title = QLabel("Media")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title, 1)
        home = QPushButton("Home")
        home.clicked.connect(self.nav_to_home.emit)
        header.addWidget(home)
        layout.addLayout(header)
        layout.addStretch(1)

        choices = QHBoxLayout()
        for name, description, enabled, signal, attribute in (
            ("YouTube", "Browse and control playback on your PC.", youtube_enabled, self.nav_to_youtube, "youtube_button"),
            ("Roku TV", "Control Roku directly, even with the PC off.", roku_enabled, self.nav_to_roku, "roku_button"),
        ):
            column = QVBoxLayout()
            button = QPushButton(name)
            button.setStyleSheet("min-height: 80px; font-size: 18px;")
            button.setEnabled(enabled)
            button.clicked.connect(signal.emit)
            setattr(self, attribute, button)
            column.addWidget(button)
            text = QLabel(description)
            text.setWordWrap(True)
            column.addWidget(text)
            choices.addLayout(column, 1)
        layout.addLayout(choices)
        layout.addStretch(1)
