"""Clock display and its one-second refresh timer."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel

from utils.time_utils import get_local_time


class Clock(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(300, 50)
        self.setStyleSheet("""
            color: rgb(100,255,170);
            font-size: 32px;
            font-weight: bold;
            background: transparent;
        """)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

    def update_clock(self):
        self.setText(get_local_time().toString("h:mm:ss AP"))
