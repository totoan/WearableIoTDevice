"""Actual title, progress, and controls for the selected PC YouTube tab."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from widgets.touch_slider import TouchSlider


class NowPlayingInterface(QWidget):
    def __init__(self, playback, thumbnails, parent=None):
        super().__init__(parent)
        self.playback = playback
        self.thumbnails = thumbnails
        self.thumbnail_address = ""
        self.seek_video_id = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        details = QHBoxLayout()
        self.thumbnail = QLabel("YouTube")
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setFixedSize(160, 90)
        details.addWidget(self.thumbnail)

        text = QVBoxLayout()
        self.title = QLabel("No playback session connected")
        self.title.setWordWrap(True)
        self.title.setMaximumHeight(46)
        self.title.setStyleSheet("font-size: 18px;")
        text.addWidget(self.title)

        self.creator = QLabel()
        self.creator.setStyleSheet("font-size: 14px;")
        text.addWidget(self.creator)
        details.addLayout(text, 1)
        layout.addLayout(details)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        self.status.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.status)

        self.seek_slider = TouchSlider()
        self.seek_slider.setAccessibleName("Video position")
        self.seek_slider.interaction_started.connect(self.begin_seek)
        self.seek_slider.valueChanged.connect(self.preview_seek)
        self.seek_slider.edit_finished.connect(self.commit_seek)
        layout.addWidget(self.seek_slider)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.time_label)

        volume_row = QHBoxLayout()
        self.volume_label = QLabel("Volume 100%")
        self.volume_label.setFixedWidth(125)
        volume_row.addWidget(self.volume_label)
        self.volume_slider = TouchSlider()
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setAccessibleName("YouTube volume")
        self.volume_slider.valueChanged.connect(self.preview_volume)
        self.volume_slider.edit_finished.connect(self.commit_volume)
        volume_row.addWidget(self.volume_slider, 1)
        layout.addLayout(volume_row)
        layout.addStretch()

        controls = QHBoxLayout()
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(playback.toggle_pause)
        controls.addWidget(self.play_pause_button)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(playback.next_video)
        controls.addWidget(self.next_button)
        self.fullscreen_button = QPushButton("Fullscreen")
        self.fullscreen_button.clicked.connect(playback.toggle_fullscreen)
        controls.addWidget(self.fullscreen_button)
        layout.addLayout(controls)

        playback.state_changed.connect(self.update_state)
        playback.busy_changed.connect(self.update_buttons)
        playback.message_received.connect(self.status.setText)
        self.update_state(playback.state)

    def update_state(self, state):
        title = state.get("title") or "No video selected"
        if not state.get("playerConnected", False):
            title = "Chrome controller disconnected"
        self.title.setText(title)
        self.title.setToolTip(title)
        self.creator.setText(state.get("channelTitle", ""))

        message = state.get("message")
        if not message:
            message = "Paused" if state.get("paused", True) else "Playing"
        self.status.setText(message)

        current = state.get("currentTime", 0)
        duration = state.get("duration", 0)
        if self.seek_slider.is_editing and (
            not self.playback.available
            or not state.get("canSeek", False)
            or state.get("videoId", "") != self.seek_video_id
        ):
            self.seek_slider.cancel_edit()
            self.seek_video_id = ""

        # Incoming progress must not pull a slider away from the user's finger.
        if not self.seek_slider.is_editing:
            self.seek_slider.setRange(0, max(1, int(duration)))
            self.seek_slider.setValue(int(current))
            self.time_label.setText(f"{self.format_time(current)} / {self.format_time(duration)}")

        if not self.playback.available:
            self.volume_slider.cancel_edit()
        if not self.volume_slider.is_editing:
            volume = state.get("volume", 100)
            self.volume_slider.setValue(volume)
            label = "Muted" if state.get("muted", False) else "Volume"
            self.volume_label.setText(f"{label} {volume}%")

        address = state.get("thumbnailUrl", "")
        if address != self.thumbnail_address:
            self.thumbnail_address = address
            self.thumbnail.clear()
            self.thumbnail.setText("YouTube")
            if address:
                self.thumbnails.load(address, lambda image, url=address: self.show_thumbnail(url, image))

        self.play_pause_button.setText("Play" if state.get("paused", True) else "Pause")
        self.fullscreen_button.setText("Exit fullscreen" if state.get("fullscreen", False) else "Fullscreen")
        self.update_buttons(self.playback.busy)

    def update_buttons(self, busy):
        available = self.playback.available and self.playback.state.get("ready", False) and not busy
        self.play_pause_button.setEnabled(available)
        self.next_button.setEnabled(available and self.playback.state.get("canNext", False))
        self.fullscreen_button.setEnabled(available)
        self.volume_slider.setEnabled(available)
        self.seek_slider.setEnabled(available and self.playback.state.get("canSeek", False))

    def begin_seek(self):
        self.seek_video_id = self.playback.state.get("videoId", "")

    def preview_seek(self, seconds):
        if self.seek_slider.is_editing:
            duration = self.playback.state.get("duration", 0)
            self.time_label.setText(f"{self.format_time(seconds)} / {self.format_time(duration)}")

    def commit_seek(self, seconds):
        if self.seek_video_id == self.playback.state.get("videoId", ""):
            self.playback.seek(seconds)
        self.seek_video_id = ""

    def preview_volume(self, volume):
        if self.volume_slider.is_editing:
            self.volume_label.setText(f"Volume {volume}%")

    def commit_volume(self, volume):
        self.playback.set_volume(volume)

    def show_thumbnail(self, address, image):
        if address == self.thumbnail_address:
            self.thumbnail.setPixmap(image.scaled(
                self.thumbnail.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))

    @staticmethod
    def format_time(seconds):
        seconds = max(0, int(seconds))
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"
