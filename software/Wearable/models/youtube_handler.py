"""Request YouTube lists through the paired PC; Google credentials stay there."""
from PySide6.QtCore import QObject, QTimer, Signal
from models.playback_handler import PlaybackHandler


class YouTubeHandler(QObject):
    page_received = Signal(str, dict)
    request_failed = Signal(str, str)
    connection_changed = Signal(bool)

    def __init__(self, dashboard_handler, parent=None, playback=None):
        super().__init__(parent)
        self.dashboard = dashboard_handler
        self.pending = {}
        self.playback = playback or PlaybackHandler(dashboard_handler, self)

        dashboard_handler.request_completed.connect(self.receive_page)
        dashboard_handler.request_failed.connect(self.fail_request)
        dashboard_handler.peers_changed.connect(self.update_connection)

    @property
    def connected(self):
        return self.dashboard.connected

    def browse(self, operation, **parameters):
        request_id = self.dashboard.send_request(operation, **parameters)
        if not request_id:
            return ""

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(30000)
        timer.timeout.connect(
            lambda: self.fail_request(request_id, "The list took too long to load. Please retry.")
        )
        self.pending[request_id] = timer
        timer.start()
        return request_id

    def receive_page(self, request_id, page):
        if request_id not in self.pending:
            return

        if not isinstance(page, dict) or not isinstance(page.get("items"), list):
            self.fail_request(request_id, "The PC returned an invalid list.")
            return

        self.finish_request(request_id)
        self.page_received.emit(request_id, page)

    def fail_request(self, request_id, reason):
        if request_id not in self.pending:
            return

        self.finish_request(request_id)
        self.request_failed.emit(request_id, reason)

    def finish_request(self, request_id):
        timer = self.pending.pop(request_id, None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()

    def update_connection(self, connected, dashboard_connected):
        if not connected:
            for request_id in list(self.pending):
                self.fail_request(request_id, "PC disconnected. The last loaded list is still available.")

        self.connection_changed.emit(connected)
