"""Scan/connect through NetworkManager; Wi-Fi passwords travel only over stdin."""
import re
import shutil
import sys

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal


def split_fields(line):
    fields = []
    current = ""
    escaped = False
    for character in line:
        if escaped:
            current += character
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == ":":
            fields.append(current)
            current = ""
        else:
            current += character
    fields.append(current)
    return fields


class WifiHandler(QObject):
    networks_changed = Signal(list)
    status_changed = Signal(str)
    busy_changed = Signal(bool)
    password_required = Signal(str)

    def __init__(self, parent=None, command=None):
        super().__init__(parent)
        self.preview = command is None and not sys.platform.startswith("linux")
        self.command = command or [shutil.which("nmcli") or "nmcli"]
        self.networks = []
        self.status = "Wi-Fi not checked"
        self.operation = ""
        self.selected = None
        self.output = ""
        self.asked_password = False
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("LC_ALL", "C")
        self.process.setProcessEnvironment(environment)
        self.process.readyReadStandardOutput.connect(self.receive_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.timeout.connect(self.timed_out)

    @property
    def busy(self):
        return bool(self.operation) or self.process.state() != QProcess.ProcessState.NotRunning

    def set_status(self, text):
        self.status = text
        self.status_changed.emit(text)

    def run(self, operation, arguments):
        if self.busy:
            return
        self.operation = operation
        self.output = ""
        self.asked_password = False
        self.busy_changed.emit(True)
        self.timeout.start(45000 if operation == "connect" else 15000)
        self.process.start(self.command[0], self.command[1:] + arguments)

    def scan(self):
        if self.busy:
            return
        if self.preview:
            self.networks = [
                {"ssid": "Home Wi-Fi (preview)", "signal": 92, "security": "WPA2", "bssid": "", "device": "", "active": True},
                {"ssid": "Guest Wi-Fi (preview)", "signal": 65, "security": "--", "bssid": "", "device": "", "active": False},
            ]
            self.networks_changed.emit(self.networks)
            self.set_status("Windows preview: sample networks; your PC network will not change.")
            return
        self.set_status("Scanning nearby Wi-Fi networks…")
        self.run("scan", ["--terse", "--escape", "yes", "--fields", "IN-USE,SSID,SIGNAL,SECURITY,BSSID,DEVICE",
                          "device", "wifi", "list", "--rescan", "yes"])

    def connect_network(self, network):
        if self.busy or network.get("active"):
            return
        if "802.1X" in network["security"] or "EAP" in network["security"]:
            self.set_status("Enterprise Wi-Fi requires separate NetworkManager setup in this version.")
            return
        self.selected = dict(network)
        if self.preview:
            if network["security"] != "--":
                self.password_required.emit(network["ssid"])
            else:
                self.preview_connected()
            return
        if not re.fullmatch(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", network["bssid"]) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.:-]{0,63}", network["device"]):
            self.set_status("Invalid access point details. Refresh the network list.")
            return
        self.set_status(f"Connecting to {network['ssid']}…")
        self.run("connect", ["--ask", "--wait", "30", "device", "wifi", "connect", network["bssid"], "ifname", network["device"]])

    def submit_password(self, password):
        if not password or "\n" in password or "\r" in password or len(password) > 128:
            self.cancel()
            self.set_status("Enter a valid Wi-Fi password without line breaks.")
            return
        if self.preview:
            self.preview_connected()
        elif self.operation == "connect":
            self.process.write((password + "\n").encode("utf-8"))
            self.set_status("Connecting…")
        # The app does not retain the password or place it in process arguments.

    def preview_connected(self):
        for network in self.networks:
            network["active"] = network is self.selected or network["ssid"] == self.selected["ssid"]
        self.networks_changed.emit(self.networks)
        self.set_status("Preview connection simulated. Your PC network is unchanged.")

    def receive_output(self):
        self.output += bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if len(self.output) > 65536:
            self.cancel()
            self.set_status("NetworkManager returned too much output.")
            return
        if self.operation == "connect" and self.process.state() == QProcess.ProcessState.Running and not self.asked_password and re.search(r"802-11-wireless-security\.(psk|wep-key[0-3])", self.output):
            self.asked_password = True
            self.timeout.stop()
            self.password_required.emit(self.selected["ssid"])
            if self.operation == "connect":
                self.timeout.start(35000)

    def finished(self, exit_code, exit_status):
        self.receive_output()
        operation = self.operation
        self.operation = ""
        self.timeout.stop()
        self.busy_changed.emit(False)
        if not operation:
            self.output = ""
            return
        if exit_code != 0:
            self.set_status("Wi-Fi operation failed. Check the password, signal, and NetworkManager permissions.")
        elif operation == "scan":
            networks = []
            for line in self.output.splitlines():
                fields = split_fields(line)
                if len(fields) != 6 or not fields[1]:
                    continue
                try:
                    signal = max(0, min(100, int(fields[2])))
                except ValueError:
                    continue
                networks.append({"active": fields[0] == "*", "ssid": fields[1], "signal": signal,
                                 "security": fields[3] or "--", "bssid": fields[4], "device": fields[5]})
            self.networks = sorted(networks, key=lambda network: (not network["active"], -network["signal"]))
            self.networks_changed.emit(self.networks)
            current = next((network["ssid"] for network in self.networks if network["active"]), None)
            self.set_status(f"Connected: {current}" if current else "Select a network to connect." if networks else "No Wi-Fi networks found. Check the Wi-Fi adapter and radio.")
        else:
            self.set_status("Connected. Refreshing network status…")
            self.scan()
        self.output = ""

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.operation = ""
            self.timeout.stop()
            self.busy_changed.emit(False)
            self.set_status("NetworkManager's nmcli is unavailable. Check the Pi Wi-Fi setup.")

    def timed_out(self):
        self.cancel()
        self.set_status("Wi-Fi operation timed out. Refresh to check connection status.")

    def cancel(self):
        self.operation = ""
        self.timeout.stop()
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
        self.output = ""
        self.busy_changed.emit(self.busy)

    def stop(self):
        self.cancel()
        self.process.waitForFinished(1000)
