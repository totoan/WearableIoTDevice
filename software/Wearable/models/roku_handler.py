"""Send basic remote buttons directly to a Roku over the local network."""
import ipaddress
import json
from pathlib import Path
from xml.etree import ElementTree

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkReply, QNetworkRequest


class RokuHandler(QObject):
    status_changed = Signal(str)
    busy_changed = Signal(bool)
    device_changed = Signal(dict)
    message_received = Signal(str)

    # These are Roku remote key names, rather than arbitrary HTTP paths.
    KEYS = {
        "Home", "Back", "Up", "Down", "Left", "Right", "Select", "Info",
        "Play", "Rev", "Fwd", "InstantReplay", "VolumeUp", "VolumeDown",
        "VolumeMute", "PowerOff",
    }

    def __init__(self, parent=None, settings_path=None, port=8060):
        super().__init__(parent)
        app_folder = Path(__file__).resolve().parent.parent
        self.settings_path = Path(settings_path) if settings_path else app_folder / "config/roku.json"
        self.host = "192.168.1.100"
        self.port = port
        self.connected = False
        self.device = {}
        self.status = "TV not checked"
        self.reply = None
        self.stopped = False

        self.network = QNetworkAccessManager(self)
        self.network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        self.load_settings()

    @property
    def busy(self):
        return self.reply is not None

    @staticmethod
    def validate_host(host):
        address = ipaddress.IPv4Address(host.strip())
        if address.is_unspecified or address.is_multicast or str(address) == "255.255.255.255":
            raise ValueError("Enter the TV's IPv4 address, for example 192.168.1.100.")
        return str(address)

    def load_settings(self):
        source = self.settings_path
        if not source.exists():
            source = Path(__file__).resolve().parent.parent / "config/roku.example.json"
        if not source.exists():
            return
        try:
            settings = json.loads(source.read_text(encoding="utf-8"))
            self.host = self.validate_host(settings["host"])
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            self.status = "Check config/roku.json"

    def save_and_connect(self, host):
        if self.busy:
            return
        try:
            host = self.validate_host(host)
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.settings_path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"host": host}, indent=4) + "\n", encoding="utf-8")
            temporary.replace(self.settings_path)
        except (OSError, ValueError, AttributeError) as error:
            self.message_received.emit(f"Could not save TV address: {error}")
            return

        self.host = host
        self.connected = False
        self.device = {}
        self.device_changed.emit(self.device)
        self.check_connection()

    def set_status(self, text):
        self.status = text
        self.status_changed.emit(text)

    def check_connection(self):
        if not self.busy and not self.stopped:
            self.set_status("Checking TV…")
            self.request("query/device-info")

    def send_key(self, key):
        if key not in self.KEYS:
            self.message_received.emit("Unsupported Roku remote button.")
            return
        if not self.connected:
            self.message_received.emit("Check the TV connection first.")
            return
        if self.busy or self.stopped:
            return
        self.request(f"keypress/{key}", key)

    def request(self, path, key=None):
        request = QNetworkRequest(QUrl(f"http://{self.host}:{self.port}/{path}"))
        request.setTransferTimeout(4000)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )
        reply = self.network.post(request, b"") if key else self.network.get(request)
        self.reply = reply
        self.busy_changed.emit(True)
        reply.downloadProgress.connect(lambda received, total: reply.abort() if received > 65536 else None)
        reply.finished.connect(lambda: self.receive(reply, key))

    def receive(self, reply, key):
        if self.stopped:
            reply.deleteLater()
            return

        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        successful = reply.error() == QNetworkReply.NetworkError.NoError and status == 200
        body = bytes(reply.readAll()) if successful else b""
        reply.deleteLater()
        self.reply = None

        if status in (401, 403):
            self.connected = False
            self.set_status("TV blocked network control")
            self.message_received.emit("On the TV, set Control by mobile apps → Network access to Enabled.")
        elif not successful:
            self.connected = False
            self.set_status("TV unavailable")
            self.message_received.emit("Check TV power, its IP address, and that the Pi and TV share your home network. Commands are not retried.")
        elif key:
            self.set_status("TV reachable")
            self.message_received.emit(f"TV accepted {key}. The current app decides how it responds.")
            if key == "PowerOff":
                self.connected = False
                self.set_status("Power off sent")
        else:
            self.read_device(body)

        self.busy_changed.emit(False)

    def read_device(self, body):
        try:
            root = ElementTree.fromstring(body)
            if root.tag != "device-info":
                raise ValueError("Not a Roku device-info response")
            self.device = {
                "name": root.findtext("user-device-name") or root.findtext("friendly-device-name") or "Roku TV",
                "model": root.findtext("model-name") or "Roku",
                "is_tv": root.findtext("is-tv") == "true",
            }
        except (ElementTree.ParseError, ValueError):
            self.connected = False
            self.set_status("Invalid TV response")
            self.message_received.emit("This address did not return Roku device information.")
            return

        self.connected = True
        self.set_status("TV reachable")
        self.device_changed.emit(self.device)
        self.message_received.emit("Connected directly to Roku. Your PC is not required.")

    def stop(self):
        self.stopped = True
        if self.reply is not None:
            self.reply.abort()
            self.reply = None
