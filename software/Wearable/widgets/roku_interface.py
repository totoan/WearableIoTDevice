"""Touch remote for the living room TV, independent of the PC connection."""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from widgets.roku_address_dialog import RokuAddressDialog


class RokuInterface(QWidget):
    nav_to_home = Signal()

    def __init__(self, handler, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.remote_buttons = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Living Room TV")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title, 1)
        home = QPushButton("Wearable home")
        home.clicked.connect(self.nav_to_home.emit)
        header.addWidget(home)
        layout.addLayout(header)

        connection = QHBoxLayout()
        self.device_label = QLabel(f"Roku · {handler.host}")
        connection.addWidget(self.device_label, 1)
        self.address_button = QPushButton("TV address")
        self.address_button.clicked.connect(self.edit_address)
        connection.addWidget(self.address_button)
        self.check_button = QPushButton("Check TV")
        self.check_button.clicked.connect(handler.check_connection)
        connection.addWidget(self.check_button)
        layout.addLayout(connection)

        self.status_label = QLabel(handler.status)
        layout.addWidget(self.status_label)

        controls = QHBoxLayout()
        navigation = QGridLayout()
        for label, key, row, column in (
            ("Back", "Back", 0, 0), ("Up", "Up", 0, 1), ("TV home", "Home", 0, 2),
            ("Left", "Left", 1, 0), ("OK", "Select", 1, 1), ("Right", "Right", 1, 2),
            ("Replay", "InstantReplay", 2, 0), ("Down", "Down", 2, 1), ("Options *", "Info", 2, 2),
        ):
            navigation.addWidget(self.remote_button(label, key), row, column)
        controls.addLayout(navigation, 3)

        audio = QVBoxLayout()
        for label, key in (("Volume +", "VolumeUp"), ("Mute", "VolumeMute"), ("Volume −", "VolumeDown")):
            audio.addWidget(self.remote_button(label, key))
        self.power_button = self.remote_button("TV power off", "PowerOff")
        audio.addWidget(self.power_button)
        controls.addLayout(audio, 2)
        layout.addLayout(controls, 1)

        playback = QHBoxLayout()
        for label, key in (("Rewind", "Rev"), ("Play / Pause", "Play"), ("Fast forward", "Fwd")):
            playback.addWidget(self.remote_button(label, key))
        layout.addLayout(playback)

        self.message_label = QLabel("Basic remote controls connect directly to your TV.")
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumHeight(38)
        self.message_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.message_label)

        handler.status_changed.connect(self.status_label.setText)
        handler.message_received.connect(self.message_label.setText)
        handler.device_changed.connect(self.update_device)
        handler.busy_changed.connect(self.update_buttons)
        self.update_buttons(handler.busy)

    def remote_button(self, label, key):
        button = QPushButton(label)
        button.setMinimumHeight(40)
        button.setAccessibleName({"Up": "Up", "Down": "Down", "Left": "Left", "Right": "Right"}.get(key, label))
        action = self.confirm_power_off if key == "PowerOff" else lambda: self.handler.send_key(key)
        button.clicked.connect(action)
        self.remote_buttons[key] = button
        return button

    def update_device(self, device):
        name = device.get("name", "Roku")
        self.device_label.setText(f"{name[:45]} · {self.handler.host}")

    def update_buttons(self, busy):
        available = self.handler.connected and not busy
        for key, button in self.remote_buttons.items():
            tv_only = key in {"VolumeUp", "VolumeDown", "VolumeMute", "PowerOff"}
            button.setEnabled(available and (not tv_only or self.handler.device.get("is_tv", False)))
        self.check_button.setEnabled(not busy)
        self.address_button.setEnabled(not busy)

    def edit_address(self):
        dialog = RokuAddressDialog(self.handler.host, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.handler.save_and_connect(dialog.input.text())

    def confirm_power_off(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("TV power")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Turn off the living room TV?"))
        buttons = QHBoxLayout()
        for text, action in (("Cancel", dialog.reject), ("Turn off TV", dialog.accept)):
            button = QPushButton(text)
            button.clicked.connect(action)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.handler.send_key("PowerOff")

    def showEvent(self, event):
        super().showEvent(event)
        self.handler.check_connection()
