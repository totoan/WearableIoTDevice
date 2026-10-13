"""Power control with safe preview behaviour and touch confirmation dialogs."""
from pathlib import Path
import shutil
import sys

from PySide6.QtCore import QProcess, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class ShutDownButton(QPushButton):
    def __init__(self, parent=None, enable_shutdown=False):
        super().__init__(parent)
        if enable_shutdown and not sys.platform.startswith("linux"):
            raise ValueError("Real shutdown is supported only on Linux.")
        self.enable_shutdown = enable_shutdown
        self.setObjectName("powerButton")
        self.setFixedSize(50, 50)
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "shut_down.png"
        self.setIcon(QIcon(str(icon_path)))
        self.setIconSize(QSize(42, 42))
        self.setToolTip("Shut down device" if enable_shutdown else "Preview shutdown")
        self.setAccessibleName("Power")
        self.clicked.connect(self.confirm_shutdown)
        self.shutdown_process = QProcess(self)
        self.shutdown_process.finished.connect(self.shutdown_finished)
        self.shutdown_process.errorOccurred.connect(self.shutdown_error)

    def dialog(self, title, message, confirm=False):
        dialog = QDialog(self.window())
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.FramelessWindowHint)
        dialog.setWindowTitle(title)
        dialog.setFixedWidth(min(360, self.window().width() - 20))
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 20px; font-weight: bold;")
        text = QLabel(message)
        text.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(text)
        buttons = QHBoxLayout()
        if confirm:
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(dialog.reject)
            buttons.addWidget(cancel)
        accept = QPushButton("Shut down" if confirm else "OK")
        accept.clicked.connect(dialog.accept)
        buttons.addWidget(accept)
        layout.addLayout(buttons)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def confirm_shutdown(self):
        message = "Shut down the Raspberry Pi?" if self.enable_shutdown else "Simulate shutting down? Your PC will stay running."
        if not self.dialog("Power", message, confirm=True):
            return
        if not self.enable_shutdown:
            self.dialog("Preview", "Shutdown confirmed. On the Pi, this will power down the operating system.")
            return
        self.setEnabled(False)
        self.shutdown_process.start("sudo", ["-n", shutil.which("shutdown") or "/usr/sbin/shutdown", "-h", "now"])

    def shutdown_finished(self, exit_code, exit_status):
        self.setEnabled(True)
        if exit_code != 0:
            details = bytes(self.shutdown_process.readAllStandardError()).decode(errors="replace").strip()
            self.dialog("Shutdown failed", details or "The shutdown command did not succeed.")

    def shutdown_error(self, error):
        self.setEnabled(True)
        self.dialog("Shutdown failed", self.shutdown_process.errorString())
