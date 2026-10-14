"""Microphone selection and a dictation test using the same reusable keyboard."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from utils.setup_speech import model_ready
from widgets.touch_keyboard import TouchKeyboard


class MicrophoneInterface(QWidget):
    nav_back = Signal()

    def __init__(self, speech, parent=None):
        super().__init__(parent)
        self.speech = speech
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        header = QHBoxLayout()
        title = QLabel("Microphone")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title, 1)
        back = QPushButton("Back")
        back.clicked.connect(self.nav_back.emit)
        header.addWidget(back)
        layout.addLayout(header)
        layout.addStretch()
        self.device_list = QComboBox()
        self.device_list.setAccessibleName("Recording microphone")
        layout.addWidget(self.device_list)
        actions = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh microphones")
        self.refresh_button.clicked.connect(self.refresh)
        self.save_button = QPushButton("Save microphone")
        self.save_button.clicked.connect(self.save)
        self.test_button = QPushButton("Test dictation")
        self.test_button.clicked.connect(self.test)
        for button in (self.refresh_button, self.save_button, self.test_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.model_status = QLabel()
        self.model_status.setWordWrap(True)
        layout.addWidget(self.model_status)
        layout.addStretch(2)
        speech.devices_ready.connect(self.show_devices)
        speech.error_received.connect(self.status.setText)
        self.device_list.addItem("System default microphone", {"name": "", "api": ""})

    def refresh(self):
        self.status.setText("Looking for microphones…")
        if not self.speech.refresh_devices():
            self.status.setText("Please finish the current voice operation, then refresh microphones.")

    def show_devices(self, devices):
        self.device_list.clear()
        self.device_list.addItem("System default microphone", {"name": "", "api": ""})
        for device in devices:
            self.device_list.addItem(f"{device['name']} ({device['api']})", device)
            if device["name"] == self.speech.settings["device_name"] and device["api"] == self.speech.settings["host_api"]:
                self.device_list.setCurrentIndex(self.device_list.count() - 1)
        self.status.setText(f"Found {len(devices)} input device(s). Choose one and save.")

    def save(self):
        device = self.device_list.currentData()
        if device and self.speech.save_device(device["name"], device["api"]):
            self.status.setText("Microphone saved. You can change it when swapping microphones.")

    def test(self):
        keyboard = TouchKeyboard(parent=self, title="Microphone test", speech_handler=self.speech)
        keyboard.exec()
        keyboard.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        if model_ready(self.speech.model_path):
            self.model_status.setText(
                "Offline English model ready. Paired PC recognition is preferred when connected."
            )
        else:
            self.model_status.setText(
                "Model missing: run setup-voice.cmd on Windows or utils/setup_speech.py on the Pi."
            )
        self.refresh()
