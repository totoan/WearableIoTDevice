"""Main window and page container, following the Legacy application structure."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from widgets.home_interface import HomeInterface
from widgets.dashboard_interface import DashboardInterface
from widgets.youtube_interface import YouTubeInterface
from widgets.roku_interface import RokuInterface


class MainWindow(QMainWindow):
    def __init__(self, enable_shutdown=False, parent=None, dashboard_handler=None, youtube_handler=None, roku_handler=None):
        super().__init__(parent)
        self.setWindowTitle("Pi5 Wearable" if enable_shutdown else "Pi5 Wearable — Preview")
        self.resize(800, 480)
        self.setMinimumSize(400, 240)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.home_page = HomeInterface(enable_shutdown=enable_shutdown)
        self.stack.addWidget(self.home_page)
        self.stack.setCurrentWidget(self.home_page)
        self.home_page.roku_button.setVisible(roku_handler is not None)

        if dashboard_handler is not None:
            self.home_page.connection_label.setText(dashboard_handler.status)
            dashboard_handler.status_changed.connect(
                self.home_page.connection_label.setText
            )
            self.dashboard_page = DashboardInterface(dashboard_handler)
            self.stack.addWidget(self.dashboard_page)
            self.home_page.nav_to_dashboard.connect(
                lambda: self.stack.setCurrentWidget(self.dashboard_page)
            )
            self.dashboard_page.nav_to_home.connect(self.open_home)

        if youtube_handler is not None:
            self.youtube_page = YouTubeInterface(youtube_handler)
            self.stack.addWidget(self.youtube_page)
            self.home_page.nav_to_youtube.connect(
                lambda: self.stack.setCurrentWidget(self.youtube_page)
            )
            self.youtube_page.nav_to_home.connect(self.open_home)

        if roku_handler is not None:
            self.roku_page = RokuInterface(roku_handler)
            self.stack.addWidget(self.roku_page)
            self.home_page.nav_to_roku.connect(
                lambda: self.stack.setCurrentWidget(self.roku_page)
            )
            self.roku_page.nav_to_home.connect(self.open_home)

    def open_home(self):
        self.stack.setCurrentWidget(self.home_page)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.stack.currentWidget() == self.home_page:
                self.close()
            else:
                self.open_home()
        else:
            super().keyPressEvent(event)
