"""Touch-friendly choice of shutdown or reboot; confirmation happens afterward."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class PowerMenu(QDialog):
    def __init__(self, parent=None, preview=False):
        super().__init__(parent)
        self.action = ""
        self.setWindowTitle("Power")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(min(360, parent.width() - 20) if parent else 360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        heading = QLabel("Power")
        heading.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(heading)
        message = QLabel("Choose an action." if not preview else "Preview: your PC will stay running.")
        message.setWordWrap(True)
        layout.addWidget(message)
        for text, action in (("Reboot", "reboot"), ("Shut down", "shutdown")):
            button = QPushButton(text)
            button.setStyleSheet("min-height: 36px;")
            button.clicked.connect(lambda checked=False, selected=action: self.select_action(selected))
            layout.addWidget(button)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)

    def select_action(self, action):
        self.action = action
        self.accept()
