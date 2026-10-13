"""Common browsing behaviour: load a page, select an item, and open playlists."""
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from widgets.youtube.video_list import VideoList


class BrowseInterface(QWidget):
    def __init__(self, handler, thumbnails, parent=None):
        super().__init__(parent)
        self.handler = handler
        self.context = None
        self.history = []
        self.request_id = ""
        self.appending = False
        self.selected = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)

        toolbar = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        toolbar.addWidget(self.back_button)

        self.title_label = QLabel("Choose a list")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(self.title_label, 1)

        self.reload_button = QPushButton("Reload list")
        self.reload_button.clicked.connect(self.load_page)
        toolbar.addWidget(self.reload_button)
        self.main_layout.addLayout(toolbar)

        self.status_label = QLabel("Connect to the PC to browse YouTube.")
        self.status_label.setStyleSheet("font-size: 14px;")
        self.status_label.setWordWrap(True)
        self.main_layout.addWidget(self.status_label)

        self.video_list = VideoList(thumbnails)
        self.video_list.item_selected.connect(self.select_item)
        self.main_layout.addWidget(self.video_list, 1)

        self.selected_label = QLabel("Select an item to browse its creator or playlist.")
        self.selected_label.setStyleSheet("font-size: 14px;")
        self.selected_label.setWordWrap(True)
        self.selected_label.setMaximumHeight(38)
        self.main_layout.addWidget(self.selected_label)

        actions = QHBoxLayout()
        self.creator_button = QPushButton("Creator playlists")
        self.creator_button.clicked.connect(self.open_creator)
        actions.addWidget(self.creator_button)

        self.playlist_button = QPushButton("Open playlist")
        self.playlist_button.clicked.connect(self.open_playlist)
        actions.addWidget(self.playlist_button)

        self.more_button = QPushButton("Load more")
        self.more_button.clicked.connect(lambda: self.load_page(append=True))
        actions.addWidget(self.more_button)

        self.play_button = QPushButton("Play on PC")
        self.play_button.clicked.connect(self.play_selected_video)
        actions.addWidget(self.play_button)
        self.main_layout.addLayout(actions)

        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.setInterval(5000)
        self.retry_timer.timeout.connect(self.retry_initial_uploads)

        handler.page_received.connect(self.receive_page)
        handler.request_failed.connect(self.receive_error)
        handler.connection_changed.connect(self.connection_changed)
        if handler.playback is not None:
            handler.playback.state_changed.connect(lambda state: self.update_buttons())
            handler.playback.busy_changed.connect(lambda busy: self.update_buttons())
            handler.playback.message_received.connect(self.status_label.setText)
        self.update_buttons()

    def set_context(self, operation, parameters, title, remember=True):
        if remember and self.context is not None:
            self.history.append(dict(self.context))

        self.retry_timer.stop()
        self.context = {
            "operation": operation,
            "parameters": parameters,
            "title": title,
            "items": [],
            "nextPageToken": "",
            "loaded": False,
        }
        self.title_label.setText(title)
        self.title_label.setToolTip(title)
        self.video_list.clear()
        self.selected = None
        self.selected_label.setText("Select an item to browse its creator or playlist.")
        self.load_page()

    def load_page(self, checked=False, append=False):
        if self.context is None or self.request_id:
            return

        if not self.handler.connected:
            self.status_label.setText("PC disconnected. Connect from the home screen's PC Dashboard page.")
            self.update_buttons()
            return

        parameters = dict(self.context["parameters"])
        if append:
            token = self.context["nextPageToken"]
            if not token:
                return
            parameters["pageToken"] = token

        self.appending = append
        self.request_id = self.handler.browse(self.context["operation"], **parameters)
        self.status_label.setText("Loading…")
        self.update_buttons()

    def receive_page(self, request_id, page):
        if request_id != self.request_id or self.context is None:
            return

        self.request_id = ""
        entries = page["items"]
        if self.appending:
            self.context["items"].extend(entries)
        else:
            self.context["items"] = list(entries)
            self.selected = None
            self.selected_label.setText("Select an item to browse its creator or playlist.")

        self.video_list.set_items(entries, append=self.appending)
        self.context["loaded"] = True
        self.context["nextPageToken"] = page.get("nextPageToken", "")
        count = len(self.context["items"])
        status = f"{count} items" if count else "No results found."

        if page.get("ready") is False:
            status = "Uploads are loading on the PC…"
            self.retry_timer.start()

        if page.get("updatedAt"):
            try:
                updated = datetime.fromisoformat(page["updatedAt"].replace("Z", "+00:00"))
                status += " · Updated " + updated.astimezone().strftime("%I:%M %p")
            except ValueError:
                pass

        self.status_label.setText(status)
        self.update_buttons()

    def receive_error(self, request_id, reason):
        if request_id == self.request_id:
            self.request_id = ""
            self.status_label.setText(reason)
            self.update_buttons()

    def select_item(self, entry):
        self.selected = entry
        self.selected_label.setText(entry.get("title", "Untitled"))
        self.update_buttons()

    def open_creator(self):
        if self.selected and self.selected.get("channelId"):
            self.set_context(
                "youtube.playlists",
                {"channelId": self.selected["channelId"]},
                self.selected.get("channelTitle") or self.selected.get("title", "Creator playlists"),
            )

    def open_playlist(self):
        if self.selected and self.selected.get("kind") == "playlist":
            self.set_context(
                "youtube.playlistVideos",
                {"playlistId": self.selected.get("playlistId") or self.selected["id"]},
                self.selected.get("title", "Playlist"),
            )

    def go_back(self):
        if not self.history or self.request_id:
            return

        self.retry_timer.stop()
        self.context = self.history.pop()
        self.title_label.setText(self.context["title"])
        self.title_label.setToolTip(self.context["title"])
        self.video_list.set_items(self.context["items"])
        self.selected = None
        self.selected_label.setText("Select an item to browse its creator or playlist.")
        self.status_label.setText(f"{len(self.context['items'])} items")
        self.update_buttons()

    def play_selected_video(self):
        if self.selected and self.handler.playback is not None:
            self.handler.playback.play_video(self.selected)

    def update_buttons(self):
        available = self.handler.connected and not self.request_id
        self.back_button.setEnabled(bool(self.history) and not self.request_id)
        self.reload_button.setEnabled(available and self.context is not None)
        self.creator_button.setEnabled(available and bool(self.selected and self.selected.get("channelId")))
        self.playlist_button.setEnabled(available and bool(self.selected and self.selected.get("kind") == "playlist"))
        self.more_button.setEnabled(available and bool(self.context and self.context["nextPageToken"]))
        playback = self.handler.playback
        self.play_button.setEnabled(
            available
            and bool(self.selected and self.selected.get("kind", "video") == "video")
            and playback is not None
            and playback.available
            and not playback.busy
        )

    def connection_changed(self, connected):
        if connected and self.isVisible() and self.context and not self.request_id:
            self.load_page()
        elif not connected:
            self.status_label.setText("PC disconnected. Showing the last loaded list.")
        self.update_buttons()

    def retry_initial_uploads(self):
        if self.isVisible() and self.context and self.context["operation"] == "youtube.uploads":
            self.load_page()

    def showEvent(self, event):
        super().showEvent(event)
        if self.context and not self.context["loaded"]:
            self.load_page()
