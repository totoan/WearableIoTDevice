"""Find Roku TVs through SSDP, then verify their device information over HTTP."""
from urllib.parse import urlparse
from xml.etree import ElementTree

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import (
    QAbstractSocket, QHostAddress, QNetworkAccessManager, QNetworkInterface,
    QNetworkProxy, QNetworkReply, QNetworkRequest, QUdpSocket,
)


class RokuDiscovery(QObject):
    tv_found = Signal(dict)
    scanning_changed = Signal(bool)
    message_received = Signal(str)

    SEARCH = (
        'M-SEARCH * HTTP/1.1\r\n'
        'HOST: 239.255.255.250:1900\r\n'
        'MAN: "ssdp:discover"\r\n'
        'MX: 2\r\n'
        'ST: roku:ecp\r\n\r\n'
    ).encode("ascii")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanning = False
        self.sockets = []
        self.replies = set()
        self.seen = set()
        self.televisions = {}
        self.search_count = 0
        self.network = QNetworkAccessManager(self)
        self.network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        self.deadline = QTimer(self)
        self.deadline.setSingleShot(True)
        self.deadline.timeout.connect(self.finish)
        self.repeat = QTimer(self)
        self.repeat.setInterval(700)
        self.repeat.timeout.connect(self.send_search)

    def start(self):
        self.stop()
        self.seen.clear()
        self.televisions.clear()
        self.search_count = 0
        self.scanning = True
        self.scanning_changed.emit(True)
        self.message_received.emit("Looking for Roku TVs on your home network…")

        # A separate socket on each active adapter also works on PCs with Wi-Fi
        # and Ethernet, without depending on the default multicast route.
        for interface in QNetworkInterface.allInterfaces():
            flags = interface.flags()
            if not flags & QNetworkInterface.InterfaceFlag.IsUp or flags & QNetworkInterface.InterfaceFlag.IsLoopBack:
                continue
            for entry in interface.addressEntries():
                address = entry.ip()
                if address.protocol() != QAbstractSocket.NetworkLayerProtocol.IPv4Protocol:
                    continue
                socket = QUdpSocket(self)
                if not socket.bind(address, 0):
                    socket.deleteLater()
                    continue
                socket.setMulticastInterface(interface)
                socket.setSocketOption(QAbstractSocket.SocketOption.MulticastTtlOption, 2)
                socket.readyRead.connect(lambda udp=socket: self.receive_datagrams(udp))
                self.sockets.append(socket)

        if not self.sockets:
            self.stop()
            self.message_received.emit("No network adapter available. You can enter a TV address manually.")
            return
        self.send_search()
        self.repeat.start()
        self.deadline.start(5000)

    def send_search(self):
        for socket in self.sockets:
            socket.writeDatagram(self.SEARCH, QHostAddress("239.255.255.250"), 1900)
        self.search_count += 1
        if self.search_count >= 3:
            self.repeat.stop()

    @staticmethod
    def response_host(data, sender):
        lines = data.decode("utf-8", errors="replace").splitlines()
        if not lines or lines[0].strip().upper() != "HTTP/1.1 200 OK":
            return None
        headers = {}
        for line in lines[1:]:
            name, separator, value = line.partition(":")
            if separator:
                headers[name.strip().lower()] = value.strip()
        if headers.get("st", "").lower() != "roku:ecp":
            return None
        try:
            location = urlparse(headers.get("location", ""))
            if (location.scheme != "http" or location.hostname != sender
                or location.port != 8060 or location.username or location.password
                or location.query or location.fragment or location.path not in ("", "/")):
                return None
        except ValueError:
            return None
        return sender

    def receive_datagrams(self, socket):
        while self.scanning and socket.hasPendingDatagrams():
            datagram = socket.receiveDatagram(8192)
            host = self.response_host(bytes(datagram.data()), datagram.senderAddress().toString())
            if host and host not in self.seen and len(self.seen) < 64:
                self.seen.add(host)
                self.verify_tv(host)

    def verify_tv(self, host):
        request = QNetworkRequest(QUrl(f"http://{host}:8060/query/device-info"))
        request.setTransferTimeout(2000)
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        reply = self.network.get(request)
        self.replies.add(reply)
        reply.downloadProgress.connect(lambda size, total: reply.abort() if size > 65536 else None)
        reply.finished.connect(lambda: self.read_device(host, reply))

    def read_device(self, host, reply):
        self.replies.discard(reply)
        successful = (self.scanning and reply.error() == QNetworkReply.NetworkError.NoError
                      and reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) == 200)
        body = bytes(reply.readAll()) if successful else b""
        reply.deleteLater()
        if not successful:
            return
        try:
            root = ElementTree.fromstring(body)
            if root.tag != "device-info" or root.findtext("is-tv") != "true":
                return
        except ElementTree.ParseError:
            return
        device = {
            "host": host,
            "name": (root.findtext("user-device-name") or root.findtext("friendly-device-name") or "Roku TV")[:80],
            "model": (root.findtext("model-name") or "Roku TV")[:80],
        }
        self.televisions[host] = device
        self.tv_found.emit(device)

    def finish(self):
        count = len(self.televisions)
        self.stop()
        self.message_received.emit(
            f"Found {count} Roku TV(s). Select one below."
            if count else "No Roku TVs found. Turn on the TV, check Wi-Fi, or enter its address manually."
        )

    def stop(self):
        self.scanning = False
        self.deadline.stop()
        self.repeat.stop()
        for socket in self.sockets:
            socket.close()
            socket.deleteLater()
        self.sockets.clear()
        for reply in list(self.replies):
            reply.abort()
        self.replies.clear()
        self.scanning_changed.emit(False)
