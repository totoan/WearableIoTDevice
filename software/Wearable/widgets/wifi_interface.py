"""Wi-Fi selection; NetworkManager owns the saved connection credentials."""
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QScroller, QVBoxLayout, QWidget

from widgets.touch_keyboard import TouchKeyboard


class WifiInterface(QWidget):
    nav_back = Signal()

    def __init__(self, handler, parent=None):
        super().__init__(parent)
        self.handler = handler
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        header = QHBoxLayout()
        title = QLabel("Wi-Fi")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title, 1)
        back = QPushButton("Back")
        back.clicked.connect(self.nav_back.emit)
        header.addWidget(back)
        layout.addLayout(header)
        self.status = QLabel(handler.status)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.list = QListWidget()
        self.list.setObjectName("rokuTvList")
        self.list.currentItemChanged.connect(self.update_buttons)
        QScroller.grabGesture(self.list.viewport(), QScroller.ScrollerGestureType.TouchGesture)
        layout.addWidget(self.list, 1)
        actions = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh networks")
        self.refresh_button.clicked.connect(handler.scan)
        self.connect_button = QPushButton("Connect selected network")
        self.connect_button.clicked.connect(self.connect_selected)
        actions.addWidget(self.refresh_button)
        actions.addWidget(self.connect_button)
        layout.addLayout(actions)
        handler.networks_changed.connect(self.show_networks)
        handler.status_changed.connect(self.status.setText)
        handler.busy_changed.connect(self.update_buttons)
        handler.password_required.connect(self.enter_password)
        self.update_buttons()

    def show_networks(self, networks):
        self.list.clear()
        for network in networks:
            label = f"{network['ssid']}  {'[connected]' if network['active'] else ''}\nSignal {network['signal']}%  ·  {network['security']}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, network)
            item.setSizeHint(QSize(0, 64))
            self.list.addItem(item)

    def update_buttons(self, *args):
        item = self.list.currentItem()
        self.refresh_button.setEnabled(not self.handler.busy)
        self.connect_button.setEnabled(not self.handler.busy and item is not None and not item.data(Qt.ItemDataRole.UserRole)["active"])
        self.list.setEnabled(not self.handler.busy)

    def connect_selected(self):
        item = self.list.currentItem()
        if item:
            self.handler.connect_network(item.data(Qt.ItemDataRole.UserRole))

    def enter_password(self, ssid):
        keyboard = TouchKeyboard(parent=self, title=f"Wi-Fi password: {ssid}", accept_label="Connect", max_length=128, secret=True)
        if keyboard.exec() == QDialog.DialogCode.Accepted:
            self.handler.submit_password(keyboard.input.text())
        else:
            self.handler.cancel()
            self.handler.set_status("Connection cancelled.")
        keyboard.input.clear()
        keyboard.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self.handler.scan()
