#!/bin/sh
set -eu
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$APP_DIR"

# Apply the landscape orientation confirmed on the Waveshare LCD.
# Touch input already aligns correctly; no extra touch transformation is needed.
xrandr --output HDMI-1 --rotate right

# Run inside X. Window management also places the touch confirmation dialogs.
openbox &
xset s off || true
xset -dpms || true
xset s noblank || true
export QT_QPA_PLATFORM=xcb
exec "$APP_DIR/.venv/bin/python" "$APP_DIR/main.py" --fullscreen --enable-shutdown
