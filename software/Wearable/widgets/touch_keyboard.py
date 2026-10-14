"""Reusable touch keyboard with dictation, text review, and masked passwords."""
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QVBoxLayout

from models.speech_handler import SpeechHandler


class TouchKeyboard(QDialog):
    def __init__(self, text="", parent=None, *, title="Enter text", accept_label="Done", max_length=1000, speech_handler=None, secret=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(min(780, parent.window().width() - 20) if parent else 780)
        self.uppercase = False
        self.letter_buttons = []
        self.edit_controls = []
        self.speech = speech_handler or SpeechHandler.shared()
        self.voice_owned = False
        self.secret = secret
        self.symbols = False
        self.key_buttons = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        self.input = QLineEdit(text)
        self.input.setMaxLength(max_length)
        self.input.setAccessibleName(title)
        if secret:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input)

        voice_row = QHBoxLayout()
        self.microphone_button = QPushButton("Speak")
        self.microphone_button.setIcon(QIcon(str(Path(__file__).resolve().parent.parent / "assets/microphone.svg")))
        self.microphone_button.setIconSize(QSize(24, 24))
        self.microphone_button.clicked.connect(self.toggle_voice)
        voice_row.addWidget(self.microphone_button)
        self.voice_status = QLabel("Tap Speak, then Stop. Review the text before submitting.")
        self.voice_status.setStyleSheet("font-size: 12px;")
        self.voice_status.setWordWrap(True)
        self.voice_status.setMaximumHeight(36)
        voice_row.addWidget(self.voice_status, 1)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setTextVisible(False)
        self.level.setFixedSize(90, 10)
        voice_row.addWidget(self.level)
        layout.addLayout(voice_row)
        if secret:
            for index in range(voice_row.count()):
                voice_row.itemAt(index).widget().hide()

        keys = QGridLayout()
        keys.setSpacing(4)
        for row, letters in enumerate(("1234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm")):
            for column, letter in enumerate(letters):
                button = QPushButton(letter)
                button.setMinimumHeight(36)
                button.setStyleSheet("padding: 4px; min-height: 30px;")
                button.clicked.connect(lambda checked=False, key_button=button: self.insert(key_button.text()))
                keys.addWidget(button, row, column)
                self.edit_controls.append(button)
                self.key_buttons.append((button, letter))
                if letter.isalpha():
                    self.letter_buttons.append(button)
        layout.addLayout(keys)
        for column, mark in enumerate((".", ",", "?"), start=7):
            button = QPushButton(mark)
            button.setStyleSheet("padding: 4px; min-height: 30px;")
            button.clicked.connect(lambda checked=False, key_button=button: self.insert(key_button.text()))
            keys.addWidget(button, 3, column)
            self.edit_controls.append(button)
            self.key_buttons.append((button, mark))

        edit_buttons = QHBoxLayout()
        for title, action in (
            ("Shift", self.toggle_shift),
            ("Symbols", self.toggle_symbols),
            ("Space", lambda: self.input.insert(" ")),
            ("Backspace", self.input.backspace),
            ("Clear", self.input.clear),
        ):
            button = QPushButton(title)
            button.clicked.connect(action)
            edit_buttons.addWidget(button)
            self.edit_controls.append(button)
        layout.addLayout(edit_buttons)

        actions = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.submit_button = QPushButton(accept_label)
        self.submit_button.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(self.submit_button)
        layout.addLayout(actions)
        self.input.returnPressed.connect(self.accept)
        self.speech.state_changed.connect(self.update_voice_state)
        self.speech.level_changed.connect(self.update_level)
        self.speech.interim_changed.connect(self.preview_voice)
        self.speech.transcript_ready.connect(self.insert_voice)
        self.speech.error_received.connect(self.voice_error)
        self.speech.notice_received.connect(self.voice_error)
        self.update_voice_state(self.speech.state)

    def toggle_voice(self):
        if self.secret:
            return
        if self.voice_owned and self.speech.busy:
            self.speech.stop_recording()
            return
        self.voice_owned = True
        if not self.speech.start_recording():
            self.voice_owned = False

    def update_voice_state(self, state):
        active = self.voice_owned and state != "idle"
        self.microphone_button.setEnabled(not self.speech.busy or (self.voice_owned and state != "finishing"))
        self.microphone_button.setText("Stop" if active else "Speak")
        self.input.setEnabled(not active)
        self.submit_button.setEnabled(not active)
        for button in self.edit_controls:
            button.setEnabled(not active)
        if active:
            self.voice_status.setText({"starting": "Starting microphone and offline recognition…",
                                       "recording": "Listening… tap Stop when finished.",
                                       "finishing": "Finishing…"}[state])
        if state == "idle":
            if self.voice_owned and self.voice_status.text() in ("Starting microphone and offline recognition…", "Finishing…"):
                self.voice_status.setText("Recording stopped. Tap Speak to try again.")
            self.voice_owned = False

    def update_level(self, level):
        if self.voice_owned:
            self.level.setValue(int(level * 100))
        elif not self.speech.busy:
            self.level.setValue(0)

    def preview_voice(self, text):
        if self.voice_owned:
            self.voice_status.setText("Heard: " + text[-80:])

    def insert_voice(self, text):
        if not self.voice_owned:
            return
        position = self.input.selectionStart()
        if position < 0:
            position = self.input.cursorPosition()
        current = self.input.text()
        if position > 0 and not current[position - 1].isspace():
            text = " " + text
        end = position + len(self.input.selectedText())
        if end < len(current) and not current[end].isspace():
            text += " "
        available = self.input.maxLength() - len(current) + len(self.input.selectedText())
        self.input.insert(text)
        self.voice_status.setText(f"Text inserted ({self.speech.last_engine})—review before submitting." if len(text) <= available else "Text reached this field's length limit. Review before submitting.")

    def voice_error(self, message):
        if self.voice_owned:
            self.voice_status.setText(message)

    def accept(self):
        if not (self.voice_owned and self.speech.busy):
            super().accept()

    def done(self, result):
        if self.voice_owned:
            self.speech.cancel()
            self.voice_owned = False
        super().done(result)

    def insert(self, key):
        self.input.insert(key.upper() if self.uppercase else key)

    def toggle_shift(self):
        self.uppercase = not self.uppercase
        self.update_keys()

    def toggle_symbols(self):
        self.symbols = not self.symbols
        self.update_keys()

    def update_keys(self):
        symbols = "!@#$%^&*()_+-=[]{}\\|;:'\"<>/`~:.?,1234567890"
        for index, (button, original) in enumerate(self.key_buttons):
            text = symbols[index] if self.symbols and index < len(symbols) else original
            button.setText(text.upper() if self.uppercase else text.lower())
