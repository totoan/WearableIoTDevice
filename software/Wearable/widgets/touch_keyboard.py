"""Small, reusable keyboard for entering a search on the touchscreen."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout


class TouchKeyboard(QDialog):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search YouTube")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(min(780, parent.window().width() - 20) if parent else 780)
        self.uppercase = False
        self.letter_buttons = []

        layout = QVBoxLayout(self)
        self.input = QLineEdit(text)
        self.input.setMaxLength(100)
        self.input.setAccessibleName("YouTube search")
        layout.addWidget(self.input)

        keys = QGridLayout()
        keys.setSpacing(4)
        for row, letters in enumerate(("1234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm")):
            for column, letter in enumerate(letters):
                button = QPushButton(letter)
                button.setMinimumHeight(36)
                button.setStyleSheet("padding: 4px; min-height: 30px;")
                button.clicked.connect(lambda checked=False, key=letter: self.insert(key))
                keys.addWidget(button, row, column)
                if letter.isalpha():
                    self.letter_buttons.append(button)
        layout.addLayout(keys)

        edit_buttons = QHBoxLayout()
        for title, action in (
            ("Shift", self.toggle_shift),
            ("Space", lambda: self.input.insert(" ")),
            ("Backspace", self.input.backspace),
            ("Clear", self.input.clear),
        ):
            button = QPushButton(title)
            button.clicked.connect(action)
            edit_buttons.addWidget(button)
        layout.addLayout(edit_buttons)

        actions = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        search = QPushButton("Search")
        search.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(search)
        layout.addLayout(actions)
        self.input.returnPressed.connect(self.accept)

    def insert(self, key):
        self.input.insert(key.upper() if self.uppercase else key)

    def toggle_shift(self):
        self.uppercase = not self.uppercase
        for button in self.letter_buttons:
            text = button.text()
            button.setText(text.upper() if self.uppercase else text.lower())
