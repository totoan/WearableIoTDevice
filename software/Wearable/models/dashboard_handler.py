"""Pair with the PC backend, reconnect, and exchange acknowledgement tests."""
import json
from pathlib import Path
import time
from urllib.parse import urlparse
import uuid

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtWebSockets import QWebSocket


class DashboardHandler(QObject):
    status_changed = Signal(str)
    peers_changed = Signal(bool, bool)
    message_received = Signal(str)
    test_pending_changed = Signal(bool)
    request_completed = Signal(str, object)
    request_failed = Signal(str, str)
    playback_state_changed = Signal(dict)

    def __init__(self, parent=None, settings_path=None):
        super().__init__(parent)

        # Local pairing details are excluded from Git and deployment exports.
        app_folder = Path(__file__).resolve().parent.parent
        self.settings_path = Path(settings_path) if settings_path else app_folder / "config" / "dashboard.json"
        self.settings = {
            "address": "ws://localhost:5186/wearable/socket",
            "pairing_key": "",
            "device_name": "Pi5 Wearable",
        }

        self.connected = False
        self.dashboard_connected = False
        self.status = "Not paired"
        self.pending_request = ""
        self.stopped = True
        self.last_received = time.monotonic()

        self.socket = QWebSocket()
        # Browsing responses include up to 20 video records and their metadata.
        self.socket.setMaxAllowedIncomingMessageSize(262144)
        self.socket.connected.connect(self.send_pairing)
        self.socket.disconnected.connect(self.handle_disconnect)
        self.socket.textMessageReceived.connect(self.receive_message)
        self.socket.errorOccurred.connect(self.handle_error)

        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.setInterval(3000)
        self.retry_timer.timeout.connect(self.connect_to_dashboard)

        self.connection_timer = QTimer(self)
        self.connection_timer.setSingleShot(True)
        self.connection_timer.setInterval(8000)
        self.connection_timer.timeout.connect(self.connection_timed_out)

        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.setInterval(10000)
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)

        self.test_timer = QTimer(self)
        self.test_timer.setSingleShot(True)
        self.test_timer.setInterval(5000)
        self.test_timer.timeout.connect(self.test_timed_out)

        self.load_settings()

    def load_settings(self):
        if not self.settings_path.exists():
            return

        try:
            settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
            self.validate_settings(settings)
            self.settings.update(settings)
        except (OSError, ValueError, TypeError):
            self.status = "Check config/dashboard.json"

    @staticmethod
    def validate_settings(settings):
        if not isinstance(settings, dict):
            raise ValueError("Settings must be a JSON object.")

        address = settings.get("address", "")
        key = settings.get("pairing_key", "")
        name = settings.get("device_name", "Pi5 Wearable")

        if not all(isinstance(value, str) for value in (address, key, name)):
            raise ValueError("Connection settings must contain text values.")

        url = urlparse(address)
        if url.scheme not in ("ws", "wss") or not url.hostname or url.path != "/wearable/socket":
            raise ValueError("Use ws://PC_ADDRESS:5186/wearable/socket.")
        if url.username or url.password or url.query or url.fragment:
            raise ValueError("Keep the pairing key in its own field.")
        if not 32 <= len(key) <= 256 or not 1 <= len(name) <= 60:
            raise ValueError("Enter the backend pairing key and a device name.")

    def save_settings(self, address, key):
        settings = dict(self.settings)
        settings["address"] = address.strip()
        settings["pairing_key"] = key.strip()

        try:
            self.validate_settings(settings)
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings_path.write_text(json.dumps(settings, indent=4) + "\n", encoding="utf-8")
        except (OSError, ValueError) as error:
            self.message_received.emit(str(error))
            return False

        self.stop()
        self.settings = settings
        self.start()
        return True

    def start(self):
        if not self.settings["pairing_key"]:
            self.set_status(self.status)
            return

        self.stopped = False
        self.connect_to_dashboard()

    def stop(self):
        self.stopped = True
        self.retry_timer.stop()
        self.connection_timer.stop()
        self.heartbeat_timer.stop()
        self.finish_test()
        self.socket.abort()
        self.connected = False
        self.dashboard_connected = False
        self.peers_changed.emit(False, False)

    def connect_to_dashboard(self):
        if self.stopped:
            return

        self.set_status("Connecting to PC…")
        self.connection_timer.start()
        self.socket.open(QUrl(self.settings["address"]))

    def send_pairing(self):
        self.send({
            "type": "pair",
            "role": "wearable",
            "name": self.settings["device_name"],
            "key": self.settings["pairing_key"],
        })

    def receive_message(self, text):
        try:
            message = json.loads(text)
            if not isinstance(message, dict):
                return
        except ValueError:
            return

        self.last_received = time.monotonic()
        message_type = message.get("type")

        if message_type == "welcome":
            self.connection_timer.stop()
            self.connected = True
            self.heartbeat_timer.start()
            self.set_status("PC backend connected")

        elif message_type == "status":
            self.dashboard_connected = bool(message.get("dashboardConnected"))
            self.peers_changed.emit(self.connected, self.dashboard_connected)

        elif message_type == "test":
            self.message_received.emit(message.get("message", "Dashboard test received."))
            self.send({"type": "ack", "requestId": message.get("requestId", "")})

        elif message_type in ("ack", "error"):
            if self.pending_request and message.get("requestId") == self.pending_request:
                self.finish_test()
                self.message_received.emit(message.get("message", message_type))
            elif message_type == "error":
                self.request_failed.emit(
                    message.get("requestId", ""),
                    message.get("message", "Request failed."),
                )

        elif message_type == "result":
            self.request_completed.emit(
                message.get("requestId", ""),
                message.get("data"),
            )

        elif message_type == "playbackState":
            state = message.get("data")
            if isinstance(state, dict):
                self.playback_state_changed.emit(state)

    def send_request(self, operation, **parameters):
        if not self.connected:
            return ""

        request_id = str(uuid.uuid4())
        self.send({
            "type": "request",
            "requestId": request_id,
            "operation": operation,
            **parameters,
        })
        return request_id

    def send_test(self):
        if not self.connected or not self.dashboard_connected or self.pending_request:
            return

        self.pending_request = str(uuid.uuid4())
        self.test_pending_changed.emit(True)
        self.message_received.emit("Waiting for dashboard acknowledgement…")
        self.send({
            "type": "test",
            "requestId": self.pending_request,
            "message": "Hello from the wearable.",
        })
        self.test_timer.start()

    def finish_test(self):
        self.test_timer.stop()
        self.pending_request = ""
        self.test_pending_changed.emit(False)

    def test_timed_out(self):
        self.finish_test()
        self.message_received.emit("No acknowledgement received. Try again.")

    def send_heartbeat(self):
        if time.monotonic() - self.last_received > 30:
            self.socket.abort()
            self.handle_disconnect()
        else:
            self.send({"type": "ping"})

    def connection_timed_out(self):
        self.socket.abort()
        self.handle_disconnect()

    def handle_error(self, error):
        if not self.stopped:
            self.set_status("PC unavailable — retrying…")
            if not self.retry_timer.isActive():
                self.retry_timer.start()

    def handle_disconnect(self):
        self.connection_timer.stop()
        self.heartbeat_timer.stop()
        self.finish_test()
        self.connected = False
        self.dashboard_connected = False
        self.peers_changed.emit(False, False)

        if self.stopped:
            return

        if self.socket.closeCode().value == 1008:
            self.stopped = True
            self.set_status("Pairing rejected. Check the key.")
        else:
            self.set_status("PC disconnected — retrying…")
            if not self.retry_timer.isActive():
                self.retry_timer.start()

    def send(self, message):
        self.socket.sendTextMessage(json.dumps(message))

    def set_status(self, status):
        self.status = status
        self.status_changed.emit(status)
