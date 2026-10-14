"""Separate Find TV menu: network discovery, saved TV, and manual address entry."""
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QScroller, QVBoxLayout

from models.roku_discovery import RokuDiscovery
from widgets.roku_address_dialog import RokuAddressDialog


class RokuFindInterface(QDialog):
    def __init__(self, handler, parent=None, discovery=None):
        super().__init__(parent)
        self.handler = handler
        self.discovery = discovery or RokuDiscovery(self)
        self.setWindowTitle("Find TV")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(min(760, parent.window().width() - 20), min(440, parent.window().height() - 20))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        header = QHBoxLayout()
        title = QLabel("Find TV")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title, 1)
        back = QPushButton("Back")
        back.clicked.connect(self.reject)
        header.addWidget(back)
        layout.addLayout(header)
        self.status = QLabel("Search for TVs or enter an address.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.list = QListWidget()
        self.list.setObjectName("rokuTvList")
        self.list.setSpacing(3)
        self.list.currentItemChanged.connect(self.update_buttons)
        QScroller.grabGesture(self.list.viewport(), QScroller.ScrollerGestureType.TouchGesture)
        layout.addWidget(self.list, 1)
        self.saved = QLabel(f"Saved TV: {handler.host}")
        layout.addWidget(self.saved)

        actions = QHBoxLayout()
        self.scan_button = QPushButton("Search again")
        self.scan_button.clicked.connect(self.search)
        self.manual_button = QPushButton("Enter address")
        self.manual_button.clicked.connect(self.enter_address)
        self.saved_button = QPushButton("Connect saved TV")
        self.saved_button.clicked.connect(self.connect_saved)
        self.connect_button = QPushButton("Connect selected TV")
        self.connect_button.clicked.connect(self.connect_selected)
        for button in (self.scan_button, self.manual_button, self.saved_button, self.connect_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.discovery.tv_found.connect(self.add_tv)
        self.discovery.message_received.connect(self.status.setText)
        self.discovery.scanning_changed.connect(self.update_buttons)
        handler.busy_changed.connect(self.update_buttons)
        handler.message_received.connect(self.status.setText)
        handler.device_changed.connect(self.connection_changed)
        self.update_buttons()

    def search(self):
        self.list.clear()
        self.discovery.start()

    def add_tv(self, device):
        item = QListWidgetItem(f"{device['name']}  ·  {device['model']}\n{device['host']}")
        item.setData(Qt.ItemDataRole.UserRole, device['host'])
        item.setSizeHint(QSize(0, 60))
        self.list.addItem(item)
        if self.list.count() == 1:
            self.list.setCurrentItem(item)

    def update_buttons(self, *args):
        busy = self.handler.busy
        self.scan_button.setEnabled(not busy and not self.discovery.scanning)
        self.manual_button.setEnabled(not busy)
        self.saved_button.setEnabled(not busy)
        self.connect_button.setEnabled(not busy and self.list.currentItem() is not None)
        self.list.setEnabled(not busy)

    def connect_selected(self):
        item = self.list.currentItem()
        if item is not None:
            self.discovery.stop()
            self.handler.save_and_connect(item.data(Qt.ItemDataRole.UserRole))

    def connect_saved(self):
        self.discovery.stop()
        self.handler.check_connection()

    def enter_address(self):
        self.discovery.stop()
        dialog = RokuAddressDialog(self.handler.host, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.handler.save_and_connect(dialog.input.text())

    def connection_changed(self, device):
        self.saved.setText(f"Saved TV: {self.handler.host}")
        if self.handler.connected:
            self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, lambda: self.search() if self.isVisible() else None)

    def done(self, result):
        self.discovery.stop()
        super().done(result)
