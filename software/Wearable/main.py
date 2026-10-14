"""Start the wearable app. Without arguments, launch a safe desktop preview."""
import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from models.dashboard_handler import DashboardHandler
from models.youtube_handler import YouTubeHandler
from models.playback_handler import PlaybackHandler
from models.roku_handler import RokuHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--enable-shutdown", action="store_true", help="Enable real shutdown and reboot on Linux; disabled by default.")
    args = parser.parse_args()
    if args.enable_shutdown and not sys.platform.startswith("linux"):
        parser.error("Real shutdown is supported only on Linux. Omit --enable-shutdown for a preview.")
    app = QApplication(sys.argv[:1])
    app.setStyleSheet((Path(__file__).parent / "theme.qss").read_text(encoding="utf-8"))
    dashboard_handler = DashboardHandler()
    playback_handler = PlaybackHandler(dashboard_handler)
    youtube_handler = YouTubeHandler(dashboard_handler, playback=playback_handler)
    roku_handler = RokuHandler()
    window = MainWindow(
        enable_shutdown=args.enable_shutdown,
        dashboard_handler=dashboard_handler,
        youtube_handler=youtube_handler,
        roku_handler=roku_handler,
    )
    app.aboutToQuit.connect(dashboard_handler.stop)
    app.aboutToQuit.connect(roku_handler.stop)
    dashboard_handler.start()
    window.showFullScreen() if args.fullscreen else window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
