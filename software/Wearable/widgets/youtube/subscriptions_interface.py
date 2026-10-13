"""Read the same cached uploads that the PC dashboard displays."""
from PySide6.QtCore import QTimer

from widgets.youtube.browse_interface import BrowseInterface


class SubscriptionsInterface(BrowseInterface):
    def __init__(self, handler, thumbnails, parent=None):
        super().__init__(handler, thumbnails, parent)
        self.context = {
            "operation": "youtube.uploads",
            "parameters": {},
            "title": "Recent subscription uploads",
            "items": [],
            "nextPageToken": "",
            "loaded": False,
        }
        self.title_label.setText(self.context["title"])

        # This reads the PC cache only. Google's 15-minute refresh stays on the PC.
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(60000)
        self.refresh_timer.timeout.connect(self.refresh_uploads)
        self.refresh_timer.start()

    def refresh_uploads(self):
        if self.isVisible() and self.context["operation"] == "youtube.uploads":
            self.load_page()
