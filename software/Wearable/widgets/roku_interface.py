"""Touch remote for Roku TV, independent of the PC connection."""
from pathlib import Path

from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QTransform
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from widgets.roku_find_interface import RokuFindInterface


class RokuInterface(QWidget):
    nav_back = Signal()

    def __init__(self, handler, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.remote_buttons = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Roku TV")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title, 1)
        self.find_button = QPushButton("Find TV")
        self.find_button.clicked.connect(self.find_tv)
        header.addWidget(self.find_button)
        home = QPushButton("Back")
        home.clicked.connect(self.nav_back.emit)
        header.addWidget(home)
        layout.addLayout(header)

        connection = QHBoxLayout()
        self.device_label = QLabel(f"Roku · {handler.host}")
        connection.addWidget(self.device_label, 1)
        self.status_label = QLabel(handler.status)
        self.status_label.setStyleSheet("font-size: 13px;")
        connection.addWidget(self.status_label)
        layout.addLayout(connection)
        layout.addStretch(1)

        controls = QHBoxLayout()
        controls.setSpacing(16)
        controls.addStretch()
        navigation = QGridLayout()
        navigation.setSpacing(6)
        for label, key, row, column in (
            ("Back", "Back", 0, 0), ("Up", "Up", 0, 1), ("TV home", "Home", 0, 2),
            ("Left", "Left", 1, 0), ("OK", "Select", 1, 1), ("Right", "Right", 1, 2),
            ("Replay", "InstantReplay", 2, 0), ("Down", "Down", 2, 1), ("Options *", "Info", 2, 2),
        ):
            navigation.addWidget(self.remote_button(label, key), row, column)
        controls.addLayout(navigation)

        audio = QVBoxLayout()
        for label, key in (("Volume +", "VolumeUp"), ("Mute", "VolumeMute"), ("Volume −", "VolumeDown")):
            button = self.remote_button(label, key)
            button.setFixedWidth(140)
            audio.addWidget(button)
        self.power_button = self.remote_button("TV power off", "PowerOff")
        self.power_button.setFixedWidth(140)
        audio.addWidget(self.power_button)
        controls.addLayout(audio)
        controls.addStretch()
        layout.addLayout(controls)

        playback = QHBoxLayout()
        playback.addStretch()
        for label, key in (("Rewind", "Rev"), ("Play / Pause", "Play"), ("Fast forward", "Fwd")):
            button = self.remote_button(label, key)
            button.setFixedWidth(140)
            playback.addWidget(button)
        playback.addStretch()
        layout.addLayout(playback)
        layout.addStretch(1)

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
        button.setFixedSize(92, 48)
        button.setAccessibleName({"Up": "Up", "Down": "Down", "Left": "Left", "Right": "Right"}.get(key, label))
        rotations = {"Up": 0, "Right": 90, "Down": 180, "Left": 270}
        if key in rotations:
            button.setText("")
            path = Path(__file__).resolve().parent.parent / "assets/arrow.svg"
            image = QIcon(str(path)).pixmap(32, 32)
            image = image.transformed(QTransform().rotate(rotations[key]), Qt.TransformationMode.SmoothTransformation)
            button.setIcon(QIcon(image))
            button.setIconSize(QSize(28, 28))
            button.setToolTip(key)
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
        self.find_button.setEnabled(not busy)

    def find_tv(self):
        dialog = RokuFindInterface(self.handler, self)
        dialog.exec()
        dialog.deleteLater()

    def confirm_power_off(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("TV power")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Turn off TV?"))
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
