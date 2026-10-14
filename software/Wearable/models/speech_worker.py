"""Audio capture with paired PC recognition and an offline fallback."""
from array import array
import json
import math
from queue import Empty, Full, Queue
from threading import Event
import time

from PySide6.QtCore import QThread, Signal

from utils.audio_devices import input_devices, resolve_input
from models.pc_speech_client import PcSpeechClient


class DeviceWorker(QThread):
    devices_ready = Signal(list)
    failed = Signal(str)

    def run(self):
        try:
            self.devices_ready.emit(input_devices())
        except Exception:
            self.failed.emit("Could not list microphones. Check the audio dependencies and device permissions.")


class SpeechWorker(QThread):
    recording_started = Signal()
    level_changed = Signal(float)
    interim_changed = Signal(str)
    transcript_ready = Signal(str)
    model_loaded = Signal(object)
    failed = Signal(str)
    notice_received = Signal(str)
    engine_used = Signal(str)

    def __init__(self, model_path, device_name="", host_api="", model=None, parent=None, pc=None):
        super().__init__(parent)
        self.model_path = model_path
        self.device_name = device_name
        self.host_api = host_api
        self.model = model
        self.stop_requested = Event()
        self.cancelled = Event()
        self.audio_problem = Event()
        self.audio_queue = Queue(maxsize=40)
        self.channels = 1
        self.pc = PcSpeechClient(pc["address"], pc["key"]) if pc else None

    def stop_recording(self):
        self.stop_requested.set()

    def cancel(self):
        self.cancelled.set()
        self.stop_requested.set()
        if self.pc is not None:
            self.pc.cancel()

    def capture_audio(self, data, frames, timing, status):
        if self.stop_requested.is_set():
            return
        if status:
            self.audio_problem.set()
        samples = array("h", bytes(data))
        if self.channels == 2:
            samples = array("h", ((samples[index] + samples[index + 1]) // 2 for index in range(0, len(samples), 2)))
        chunk = samples.tobytes()
        try:
            self.audio_queue.put_nowait(chunk)
        except Full:
            self.audio_problem.set()
        rms = math.sqrt(sum(sample * sample for sample in samples) / max(1, len(samples))) / 32768
        self.level_changed.emit(min(1.0, rms * 5))

    def run(self):
        try:
            import sounddevice as audio
            import vosk

            device = resolve_input(self.device_name, self.host_api)
            info = audio.query_devices(device, "input")
            native_rate = int(info["default_samplerate"])
            formats = [(16000, 1), (native_rate, 1)]
            if info["max_input_channels"] >= 2:
                formats.append((native_rate, 2))
            for rate, channels in formats:
                try:
                    audio.check_input_settings(device=device, channels=channels, dtype="int16", samplerate=rate)
                    self.channels = channels
                    break
                except audio.PortAudioError:
                    continue
            else:
                raise ValueError("This microphone has no supported mono/stereo input format. Select another microphone.")

            vosk.SetLogLevel(-1)
            if self.model is None:
                self.model = vosk.Model(str(self.model_path))
                self.model_loaded.emit(self.model)
            if self.stop_requested.is_set():
                return
            recognizer = vosk.KaldiRecognizer(self.model, rate)
            segments = []
            chunks = []
            with audio.RawInputStream(device=device, samplerate=rate, channels=self.channels, dtype="int16",
                                      blocksize=max(400, rate // 20), callback=self.capture_audio):
                self.recording_started.emit()
                started = time.monotonic()
                while not self.stop_requested.is_set():
                    if self.audio_problem.is_set():
                        raise ValueError("Audio was interrupted. Try again with another microphone or input setting.")
                    if time.monotonic() - started >= 120:
                        self.stop_requested.set()
                        break
                    try:
                        chunk = self.audio_queue.get(timeout=0.1)
                    except Empty:
                        continue
                    if self.pc is not None:
                        chunks.append(chunk)
                    if recognizer.AcceptWaveform(chunk):
                        text = json.loads(recognizer.Result()).get("text", "")
                        if text:
                            segments.append(text)
                        self.interim_changed.emit(" ".join(segments))
                    else:
                        partial = json.loads(recognizer.PartialResult()).get("partial", "")
                        self.interim_changed.emit(" ".join(segments + [partial]).strip())

            if self.cancelled.is_set():
                return
            if self.audio_problem.is_set():
                raise ValueError("Audio was interrupted. Please try again.")
            while not self.audio_queue.empty():
                chunk = self.audio_queue.get_nowait()
                if self.pc is not None:
                    chunks.append(chunk)
                if recognizer.AcceptWaveform(chunk):
                    segments.append(json.loads(recognizer.Result()).get("text", ""))
            segments.append(json.loads(recognizer.FinalResult()).get("text", ""))
            text = " ".join(part for part in segments if part).strip()
            engine = "offline"
            if self.pc is not None and not self.cancelled.is_set():
                self.notice_received.emit("Recognizing on the paired PC…")
                improved = self.pc.transcribe(chunks, rate)
                if improved:
                    text = improved
                    engine = "PC Whisper"
                else:
                    self.notice_received.emit("PC speech unavailable; using offline recognition.")
            if self.cancelled.is_set():
                return
            self.engine_used.emit(engine)
            if text:
                self.transcript_ready.emit(text)
            else:
                self.failed.emit("No speech heard. Check the microphone level and try again.")
        except ImportError:
            self.failed.emit("Voice dependencies are missing. Install the updated requirements first.")
        except ValueError as error:
            self.failed.emit(str(error))
        except Exception:
            self.failed.emit("Could not start dictation. Check your microphone and offline model in Settings.")
