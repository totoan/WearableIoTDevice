"""Send a recording to the paired PC; no cloud service or persistent audio file."""
import http.client
import io
import json
import socket
from urllib.parse import urlparse
import wave


class PcSpeechClient:
    def __init__(self, address, key):
        self.address = address
        self.key = key
        self.connection = None

    def transcribe(self, chunks, rate):
        try:
            data = io.BytesIO()
            with wave.open(data, "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(rate)
                output.writeframes(b"".join(chunks))
            body = data.getvalue()
            if len(body) > 24 * 1024 * 1024:
                return None
            target = urlparse(self.address)
            kind = http.client.HTTPSConnection if target.scheme == "wss" else http.client.HTTPConnection
            self.connection = kind(target.hostname, target.port, timeout=3)
            self.connection.connect()
            if self.connection.sock is not None:
                self.connection.sock.settimeout(65)
            self.connection.request("POST", "/wearable/speech", body, {
                "Content-Type": "audio/wav", "Authorization": "Bearer " + self.key,
            })
            response = self.connection.getresponse()
            if response.status != 200:
                return None
            result = json.loads(response.read(32001))
            if not isinstance(result, dict):
                return None
            text = result.get("text")
            return text.strip() if isinstance(text, str) and len(text) <= 6000 else None
        except (OSError, ValueError, http.client.HTTPException):
            return None
        finally:
            self.cancel()

    def cancel(self):
        connection = self.connection
        if connection is not None:
            try:
                if connection.sock is not None:
                    connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
