"""Power control with safe preview behaviour and touch confirmation dialogs."""
import shutil
import sys

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from widgets.glow_icon_button import GlowIconButton
from widgets.power_menu import PowerMenu


class ShutDownButton(GlowIconButton):
    def __init__(self, parent=None, enable_shutdown=False):
        super().__init__("shut_down.png", "Power", parent)
        if enable_shutdown and not sys.platform.startswith("linux"):
            raise ValueError("Real shutdown is supported only on Linux.")
        self.enable_shutdown = enable_shutdown
        self.setObjectName("powerButton")
        self.setToolTip("Power options" if enable_shutdown else "Preview power options")
        self.setAccessibleName("Power")
        self.clicked.connect(self.open_power_menu)
        self.pending_action = "shutdown"
        self.shutdown_process = QProcess(self)
        self.shutdown_process.finished.connect(self.shutdown_finished)
        self.shutdown_process.errorOccurred.connect(self.shutdown_error)

    def dialog(self, title, message, confirm=False, confirm_label="Shut down"):
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
        accept = QPushButton(confirm_label if confirm else "OK")
        accept.clicked.connect(dialog.accept)
        buttons.addWidget(accept)
        layout.addLayout(buttons)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def open_power_menu(self):
        menu = PowerMenu(self.window(), preview=not self.enable_shutdown)
        if menu.exec() == QDialog.DialogCode.Accepted:
            self.confirm_action(menu.action)
        self.reset_emphasis()

    def confirm_action(self, action):
        if action not in {"shutdown", "reboot"}:
            return
        label = "Reboot" if action == "reboot" else "Shut down"
        message = f"{label} the Raspberry Pi?"
        if not self.enable_shutdown:
            message = f"Simulate {label.lower()}? Your PC will stay running."
        if not self.dialog(label, message, confirm=True, confirm_label=label):
            return
        self.pending_action = action
        if not self.enable_shutdown:
            self.dialog("Preview", f"{label} confirmed. On the Pi, this will {'restart' if action == 'reboot' else 'power down'} the operating system.")
            return
        self.setEnabled(False)
        option = "-r" if action == "reboot" else "-h"
        self.shutdown_process.start("sudo", ["-n", shutil.which("shutdown") or "/usr/sbin/shutdown", option, "now"])

    def failure_title(self):
        return "Reboot failed" if self.pending_action == "reboot" else "Shutdown failed"

    def shutdown_finished(self, exit_code, exit_status):
        self.setEnabled(True)
        if exit_code != 0:
            details = bytes(self.shutdown_process.readAllStandardError()).decode(errors="replace").strip()
            self.dialog(self.failure_title(), details or "The power command did not succeed.")

    def shutdown_error(self, error):
        self.setEnabled(True)
        self.dialog(self.failure_title(), self.shutdown_process.errorString())
