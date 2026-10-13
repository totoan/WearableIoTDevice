"""Connection settings and the first two-way dashboard test."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class DashboardInterface(QWidget):
    nav_to_home = Signal()

    def __init__(self, handler, parent=None):
        super().__init__(parent)
        self.handler = handler

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title = QLabel("PC Dashboard")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self.status_label = QLabel(handler.status)
        self.peer_label = QLabel("Dashboard page disconnected")
        layout.addWidget(self.status_label)
        layout.addWidget(self.peer_label)

        self.address_input = QLineEdit(handler.settings["address"])
        self.address_input.setPlaceholderText("ws://PC_ADDRESS:5186/wearable/socket")
        self.address_input.setAccessibleName("PC backend address")
        layout.addWidget(self.address_input)

        self.key_input = QLineEdit(handler.settings["pairing_key"])
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Pairing key from the dashboard backend")
        self.key_input.setAccessibleName("Pairing key")
        layout.addWidget(self.key_input)

        buttons = QHBoxLayout()
        self.connect_button = QPushButton("Save and connect")
        self.connect_button.clicked.connect(self.save_and_connect)
        buttons.addWidget(self.connect_button)

        self.test_button = QPushButton("Test dashboard")
        self.test_button.setEnabled(False)
        self.test_button.clicked.connect(handler.send_test)
        buttons.addWidget(self.test_button)
        layout.addLayout(buttons)

        self.message_label = QLabel("Pair both sides, then test the connection.")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        layout.addStretch()

        close_button = QPushButton("Home")
        close_button.clicked.connect(self.nav_to_home.emit)
        layout.addWidget(close_button)

        handler.status_changed.connect(self.status_label.setText)
        handler.peers_changed.connect(self.update_peers)
        handler.message_received.connect(self.message_label.setText)
        handler.test_pending_changed.connect(self.update_test_button)

    def save_and_connect(self):
        self.handler.save_settings(self.address_input.text(), self.key_input.text())

    def update_peers(self, connected, dashboard_connected):
        self.peer_label.setText("Dashboard page connected" if dashboard_connected else "Dashboard page disconnected")
        self.update_test_button(bool(self.handler.pending_request))

    def update_test_button(self, pending):
        self.test_button.setText("Waiting…" if pending else "Test dashboard")
        self.test_button.setEnabled(self.handler.connected and self.handler.dashboard_connected and not pending)
