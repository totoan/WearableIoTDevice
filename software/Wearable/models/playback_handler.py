"""Live state and playback requests for the Chrome tab chosen on the PC."""
from PySide6.QtCore import QObject, QTimer, Signal


class PlaybackHandler(QObject):
    state_changed = Signal(dict)
    message_received = Signal(str)
    busy_changed = Signal(bool)
    video_started = Signal()

    def __init__(self, dashboard_handler, parent=None):
        super().__init__(parent)
        self.dashboard = dashboard_handler
        self.state = {
            "playerConnected": False,
            "tabSelected": False,
            "ready": False,
            "paused": True,
            "canNext": False,
            "canSeek": False,
            "volume": 100,
            "muted": False,
            "fullscreen": False,
            "message": "Connect the Chrome controller and select a YouTube tab.",
        }
        self.pending_request = ""
        self.pending_operation = ""

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(23000)
        self.timer.timeout.connect(self.command_timed_out)

        dashboard_handler.playback_state_changed.connect(self.receive_state)
        dashboard_handler.request_completed.connect(self.receive_result)
        dashboard_handler.request_failed.connect(self.receive_error)
        dashboard_handler.peers_changed.connect(self.connection_changed)

    @property
    def available(self):
        return (
            self.dashboard.connected
            and self.state.get("playerConnected", False)
            and self.state.get("tabSelected", False)
        )

    @property
    def busy(self):
        return bool(self.pending_request)

    def play_video(self, video):
        if video.get("kind", "video") != "video":
            return

        parameters = {
            "videoId": video.get("id", ""),
            "playlistId": video.get("playlistId", ""),
        }
        position = video.get("position")
        if type(position) is int:
            parameters["position"] = position

        self.command("youtube.play", **parameters)

    def toggle_pause(self):
        operation = "youtube.resume" if self.state.get("paused", True) else "youtube.pause"
        self.command(operation)

    def next_video(self):
        self.command("youtube.next")

    def set_volume(self, volume):
        self.command("youtube.volume", volume=max(0, min(100, int(volume))))

    def seek(self, seconds):
        if self.state.get("canSeek", False):
            self.command(
                "youtube.seek",
                seekTime=max(0, float(seconds)),
                videoId=self.state.get("videoId", ""),
            )

    def toggle_fullscreen(self):
        self.command("youtube.fullscreen", fullscreen=not self.state.get("fullscreen", False))

    def command(self, operation, **parameters):
        if self.busy:
            return
        if not self.available:
            self.message_received.emit("Connect the Chrome controller and select a YouTube tab first.")
            return

        self.pending_request = self.dashboard.send_request(operation, **parameters)
        if not self.pending_request:
            self.message_received.emit("PC disconnected.")
            return

        self.pending_operation = operation
        self.busy_changed.emit(True)
        self.message_received.emit("Sending command to Chrome…")
        self.timer.start()

    def receive_state(self, state):
        self.state = dict(state)
        self.state_changed.emit(self.state)

    def receive_result(self, request_id, state):
        if request_id != self.pending_request:
            return

        operation = self.pending_operation
        self.finish_command()
        if not isinstance(state, dict):
            self.message_received.emit("Chrome returned an invalid playback response.")
            return

        self.receive_state(state)
        self.message_received.emit("Command confirmed by Chrome.")
        if operation == "youtube.play":
            self.video_started.emit()

    def receive_error(self, request_id, reason):
        if request_id == self.pending_request:
            self.finish_command()
            self.message_received.emit(reason)

    def finish_command(self):
        self.timer.stop()
        self.pending_request = ""
        self.pending_operation = ""
        self.busy_changed.emit(False)

    def command_timed_out(self):
        self.finish_command()
        self.message_received.emit("Chrome did not confirm the command. Check its selected YouTube tab.")

    def connection_changed(self, connected, dashboard_connected):
        if not connected:
            self.finish_command()
            self.receive_state({
                **self.state,
                "playerConnected": False,
                "ready": False,
                "message": "PC disconnected.",
            })
