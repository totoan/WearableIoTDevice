"""Search videos, creators, and playlists with a physical or touch keyboard."""
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLineEdit, QPushButton

from widgets.touch_keyboard import TouchKeyboard
from widgets.youtube.browse_interface import BrowseInterface


class SearchInterface(BrowseInterface):
    def __init__(self, handler, thumbnails, parent=None):
        super().__init__(handler, thumbnails, parent)
        self.title_label.setText("Search YouTube")
        self.status_label.setText("Enter a search, then press Search.")

        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search videos, creators, or playlists")
        self.search_input.setMaxLength(100)
        self.search_input.returnPressed.connect(self.search)
        search_bar.addWidget(self.search_input, 1)

        keyboard_button = QPushButton("Keyboard")
        keyboard_button.clicked.connect(self.open_keyboard)
        search_bar.addWidget(keyboard_button)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search)
        search_bar.addWidget(self.search_button)
        self.main_layout.insertLayout(0, search_bar)

    def search(self):
        query = self.search_input.text().strip()
        if not query:
            self.status_label.setText("Enter something to search for.")
            return
        if self.request_id:
            self.status_label.setText("The current list is still loading.")
            return

        self.history.clear()
        self.set_context("youtube.search", {"query": query}, f"Results for: {query}", remember=False)

    def open_keyboard(self):
        keyboard = TouchKeyboard(self.search_input.text(), self, title="Search YouTube", accept_label="Search", max_length=100)
        if keyboard.exec() == QDialog.DialogCode.Accepted:
            self.search_input.setText(keyboard.input.text())
            self.search()
        keyboard.deleteLater()
