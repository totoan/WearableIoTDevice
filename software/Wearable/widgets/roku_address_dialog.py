"""A small numeric touchscreen keypad for the Roku's IPv4 address."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout


class RokuAddressDialog(QDialog):
    def __init__(self, address, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TV address")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(340)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Roku TV IP address"))
        self.input = QLineEdit(address)
        self.input.setMaxLength(15)
        self.input.setAccessibleName("Roku TV IP address")
        layout.addWidget(self.input)

        keys = QGridLayout()
        for index, key in enumerate("123456789.0"):
            button = QPushButton(key)
            button.setMinimumHeight(36)
            button.clicked.connect(lambda checked=False, text=key: self.input.insert(text))
            keys.addWidget(button, index // 3, index % 3)
        backspace = QPushButton("Delete")
        backspace.clicked.connect(self.input.backspace)
        keys.addWidget(backspace, 3, 2)
        layout.addLayout(keys)

        actions = QHBoxLayout()
        for text, action in (("Clear", self.input.clear), ("Cancel", self.reject), ("Use address", self.accept)):
            button = QPushButton(text)
            button.clicked.connect(action)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.input.returnPressed.connect(self.accept)
