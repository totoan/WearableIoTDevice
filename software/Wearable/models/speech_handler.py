"""Shared voice input service used by every reusable touch keyboard."""
import json
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from models.speech_worker import DeviceWorker, SpeechWorker
from utils.setup_speech import MODEL_NAME, model_ready


class SpeechHandler(QObject):
    state_changed = Signal(str)
    level_changed = Signal(float)
    interim_changed = Signal(str)
    transcript_ready = Signal(str)
    error_received = Signal(str)
    devices_ready = Signal(list)
    notice_received = Signal(str)

    @classmethod
    def shared(cls):
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if not hasattr(app, "speech_handler"):
            app.speech_handler = cls(app)
            app.aboutToQuit.connect(app.speech_handler.shutdown)
        return app.speech_handler

    def __init__(self, parent=None, settings_path=None, model_path=None):
        super().__init__(parent)
        folder = Path(__file__).resolve().parent.parent
        self.settings_path = Path(settings_path) if settings_path else folder / "config/speech.json"
        self.model_path = Path(model_path) if model_path else folder / "speech_models" / MODEL_NAME
        self.settings = {"device_name": "", "host_api": ""}
        self.state = "idle"
        self.worker = None
        self.device_worker = None
        self.model = None
        self.cancelled = False
        self.dashboard = None
        self.last_engine = "offline"
        if self.settings_path.exists():
            try:
                settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
                if not isinstance(settings, dict) or not all(isinstance(settings.get(key), str) for key in self.settings):
                    raise ValueError()
                self.settings.update({key: settings[key] for key in self.settings})
            except (OSError, ValueError):
                pass

    @property
    def busy(self):
        return self.state != "idle"

    def set_state(self, state):
        self.state = state
        self.state_changed.emit(state)

    def save_device(self, name, api):
        if self.busy:
            return False
        try:
            settings = {"device_name": name, "host_api": api}
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.settings_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(settings, indent=4) + "\n", encoding="utf-8")
            temporary.replace(self.settings_path)
            self.settings = settings
            return True
        except OSError:
            self.error_received.emit("Could not save microphone settings.")
            return False

    def refresh_devices(self):
        if self.busy or self.device_worker is not None:
            return False
        self.device_worker = DeviceWorker(self)
        self.device_worker.devices_ready.connect(self.devices_ready.emit)
        self.device_worker.failed.connect(self.error_received.emit)
        self.device_worker.finished.connect(self.devices_finished)
        self.device_worker.start()
        return True

    def devices_finished(self):
        self.device_worker.deleteLater()
        self.device_worker = None

    def start_recording(self):
        if self.busy:
            return False
        if self.device_worker is not None:
            self.error_received.emit("Microphone list is still refreshing. Try again in a moment.")
            return False
        if not model_ready(self.model_path):
            self.error_received.emit("Offline model missing. Run setup-voice.cmd on Windows or utils/setup_speech.py on the Pi.")
            return False
        self.cancelled = False
        pc = None
        if self.dashboard is not None and self.dashboard.connected:
            pc = {"address": self.dashboard.settings["address"], "key": self.dashboard.settings["pairing_key"]}
        self.worker = SpeechWorker(self.model_path, self.settings["device_name"], self.settings["host_api"], self.model, self, pc=pc)
        self.worker.recording_started.connect(self.recording_started)
        self.worker.model_loaded.connect(self.cache_model)
        self.worker.level_changed.connect(self.level_changed.emit)
        self.worker.interim_changed.connect(self.receive_interim)
        self.worker.transcript_ready.connect(self.receive_transcript)
        self.worker.failed.connect(self.receive_error)
        self.worker.notice_received.connect(self.receive_notice)
        self.worker.engine_used.connect(self.record_engine)
        self.worker.finished.connect(self.recording_finished)
        self.set_state("starting")
        self.worker.start()
        return True

    def recording_started(self):
        if not self.cancelled and self.state != "finishing":
            self.set_state("recording")

    def cache_model(self, model):
        self.model = model

    def receive_notice(self, message):
        if not self.cancelled:
            self.notice_received.emit(message)

    def record_engine(self, engine):
        self.last_engine = engine

    def receive_interim(self, text):
        if not self.cancelled:
            self.interim_changed.emit(text)

    def receive_transcript(self, text):
        if not self.cancelled:
            self.transcript_ready.emit(text)

    def receive_error(self, message):
        if not self.cancelled:
            self.error_received.emit(message)

    def stop_recording(self):
        if self.worker is not None:
            self.set_state("finishing")
            self.worker.stop_recording()

    def cancel(self):
        self.cancelled = True
        if self.worker is not None:
            self.set_state("finishing")
            self.worker.cancel()

    def recording_finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.level_changed.emit(0)
        self.set_state("idle")

    def shutdown(self):
        self.cancel()
        if self.worker is not None:
            self.worker.wait()
        if self.device_worker is not None:
            self.device_worker.wait()
