"""Touch-scrollable rows used for videos, playlists, and channel results."""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QScroller, QVBoxLayout, QWidget


class VideoList(QListWidget):
    item_selected = Signal(dict)

    def __init__(self, thumbnails, parent=None):
        super().__init__(parent)
        self.thumbnails = thumbnails
        self.setObjectName("youtubeVideoList")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        QScroller.grabGesture(self.viewport(), QScroller.ScrollerGestureType.TouchGesture)
        self.currentItemChanged.connect(self.select_item)

    def set_items(self, entries, append=False):
        if not append:
            self.clear()

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, entry)
            item.setSizeHint(QSize(0, 68))
            self.addItem(item)
            self.setItemWidget(item, self.make_row(entry))

    def make_row(self, entry):
        row = QWidget()
        row.setObjectName("youtubeRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(10)

        thumbnail = QLabel(entry.get("kind", "video").title())
        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail.setFixedSize(96, 54)
        thumbnail.setStyleSheet("background-color: rgb(10, 25, 17); font-size: 12px;")
        layout.addWidget(thumbnail)

        def show_thumbnail(image):
            thumbnail.setPixmap(image.scaled(
                thumbnail.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))

        self.thumbnails.load(entry.get("thumbnailUrl", ""), show_thumbnail)

        text = QVBoxLayout()
        text.setSpacing(2)
        title = QLabel(entry.get("title", "Untitled"))
        title.setWordWrap(True)
        title.setMaximumHeight(36)
        title.setStyleSheet("font-size: 15px;")
        kind = entry.get("kind", "video")
        prefix = kind.title() + " · " if kind != "video" else ""
        creator = QLabel(prefix + entry.get("channelTitle", ""))
        creator.setStyleSheet("font-size: 13px; color: rgb(170, 210, 185);")
        text.addWidget(title)
        text.addWidget(creator)
        layout.addLayout(text, 1)
        return row

    def select_item(self, current, previous):
        if current is not None:
            self.item_selected.emit(current.data(Qt.ItemDataRole.UserRole))
