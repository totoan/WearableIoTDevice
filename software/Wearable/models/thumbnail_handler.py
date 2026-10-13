"""Load official YouTube thumbnails asynchronously and keep a small memory cache."""
from collections import OrderedDict
from urllib.parse import urlparse

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class ThumbnailHandler(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.network = QNetworkAccessManager(self)
        self.cache = OrderedDict()
        self.waiting = {}

    def load(self, address, callback):
        if not isinstance(address, str):
            return

        try:
            url = urlparse(address)
        except ValueError:
            return
        allowed_hosts = {"i.ytimg.com", "yt3.ggpht.com", "yt3.googleusercontent.com"}
        if url.scheme != "https" or url.hostname not in allowed_hosts:
            return

        if address in self.cache:
            self.cache.move_to_end(address)
            self.deliver(callback, self.cache[address])
            return

        if address in self.waiting:
            self.waiting[address].append(callback)
            return

        self.waiting[address] = [callback]
        request = QNetworkRequest(QUrl(address))
        request.setTransferTimeout(15000)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.ManualRedirectPolicy,
        )

        reply = self.network.get(request)
        reply.downloadProgress.connect(
            lambda received, total: reply.abort() if received > 2_000_000 else None
        )
        reply.finished.connect(lambda: self.receive(address, reply))

    def receive(self, address, reply):
        callbacks = self.waiting.pop(address, [])
        image = QPixmap()

        if reply.error() == QNetworkReply.NetworkError.NoError:
            image.loadFromData(reply.readAll())

        reply.deleteLater()
        if image.isNull():
            return

        self.cache[address] = image
        self.cache.move_to_end(address)
        while len(self.cache) > 100:
            self.cache.popitem(last=False)

        for callback in callbacks:
            self.deliver(callback, image)

    @staticmethod
    def deliver(callback, image):
        try:
            callback(image)
        except RuntimeError:
            # A row may have been removed while its image was downloading.
            pass
