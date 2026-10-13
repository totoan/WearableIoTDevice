"""Prepare a clean application export and optionally copy it with OpenSSH scp."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

FILES = (
    "main.py", "main_window.py", "background.py", "theme.qss",
    "requirements.txt", "start-kiosk.sh", "README.md", "assets/shut_down.png",
    "widgets/__init__.py", "widgets/home_interface.py", "widgets/clock.py",
    "widgets/shut_down_button.py", "utils/__init__.py", "utils/time_utils.py",
    "widgets/dashboard_interface.py", "models/__init__.py",
    "models/dashboard_handler.py", "config/dashboard.example.json",
    "models/youtube_handler.py", "models/thumbnail_handler.py",
    "models/playback_handler.py",
    "models/roku_handler.py", "config/roku.example.json",
    "widgets/roku_interface.py", "widgets/roku_address_dialog.py",
    "widgets/touch_slider.py",
    "widgets/touch_keyboard.py", "widgets/youtube_interface.py",
    "widgets/youtube/__init__.py", "widgets/youtube/video_list.py",
    "widgets/youtube/browse_interface.py", "widgets/youtube/subscriptions_interface.py",
    "widgets/youtube/search_interface.py", "widgets/youtube/now_playing_interface.py",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-only", action="store_true", help="Keep a clean local export; do not connect to the Pi.")
    parser.add_argument("--user", help="Pi SSH login")
    parser.add_argument("--host", help="Pi hostname or IPv4 address")
    parser.add_argument("--remote-directory", default=".", help="Existing remote parent directory; default: login home")
    args = parser.parse_args()
    if not args.export_only:
        if not args.user or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", args.user):
            parser.error("Supply --user with your Pi login.")
        if not args.host or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", args.host):
            parser.error("Supply --host with your Pi hostname or IPv4 address.")
        if not re.fullmatch(r"\.|/?[A-Za-z0-9_][A-Za-z0-9_./-]*", args.remote_directory) or ".." in args.remote_directory:
            parser.error("Use a remote directory without spaces or parent traversal.")
        scp = shutil.which("scp")
        if not scp:
            parser.error("OpenSSH scp was not found on PATH. Install the Windows OpenSSH Client.")
    source = Path(__file__).resolve().parents[1] / "Wearable"
    for name in FILES:
        if not (source / name).is_file():
            parser.error(f"Missing deployment file: {source / name}")

    temp_parent = Path(tempfile.gettempdir()).resolve()
    stage_root = Path(tempfile.mkdtemp(prefix="PiWearable-", dir=temp_parent)).resolve()
    # Verify the generated export remains directly inside the chosen temporary directory.
    if stage_root.parent != temp_parent or not stage_root.name.startswith("PiWearable-"):
        raise RuntimeError("Unexpected export location")
    stage_app = stage_root / "Wearable"
    try:
        for name in FILES:
            destination = stage_app / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, destination)
        if args.export_only:
            print(f"Clean export created at: {stage_app}")
            return 0
        target = f"{args.user}@{args.host}:{args.remote_directory.rstrip('/')}/"
        result = subprocess.run([scp, "-r", str(stage_app), target], check=False)
        if result.returncode:
            print(f"scp failed with code {result.returncode}.", file=sys.stderr)
            return result.returncode
        print("Application copied. Follow Wearable/README.md to set up or restart it on the Pi.")
        return 0
    finally:
        if not args.export_only:
            # Only remove the unique temporary export created by this invocation.
            if stage_root.parent == temp_parent and stage_root.name.startswith("PiWearable-"):
                shutil.rmtree(stage_root)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as exc:
        print(f"Deployment failed: {exc}", file=sys.stderr)
        sys.exit(1)
