"""Use the machine's configured local time, including daylight saving."""
from PySide6.QtCore import QDateTime


def get_local_time():
    return QDateTime.currentDateTime()
