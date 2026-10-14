"""Settings menu for PC pairing, microphone selection, and Wi-Fi."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class SettingsInterface(QWidget):
    nav_to_home = Signal()
    nav_to_dashboard = Signal()
    nav_to_microphone = Signal()
    nav_to_wifi = Signal()

    def __init__(self, dashboard=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title, 1)
        home = QPushButton("Home")
        home.clicked.connect(self.nav_to_home.emit)
        header.addWidget(home)
        layout.addLayout(header)
        layout.addStretch(1)

        self.dashboard_button = QPushButton("PC Dashboard connection")
        self.dashboard_button.setStyleSheet("min-height: 60px; font-size: 18px;")
        self.dashboard_button.setEnabled(dashboard is not None)
        self.dashboard_button.clicked.connect(self.nav_to_dashboard.emit)
        layout.addWidget(self.dashboard_button)
        self.status_label = QLabel(dashboard.status if dashboard else "PC connection not configured")
        layout.addWidget(self.status_label)
        description = QLabel("Pair with your PC, change its address, and test the connection.")
        description.setWordWrap(True)
        layout.addWidget(description)
        microphone = QPushButton("Microphone")
        microphone.clicked.connect(self.nav_to_microphone.emit)
        layout.addWidget(microphone)
        wifi = QPushButton("Wi-Fi")
        wifi.clicked.connect(self.nav_to_wifi.emit)
        layout.addWidget(wifi)
        layout.addStretch(1)

        if dashboard is not None:
            dashboard.status_changed.connect(self.status_label.setText)
