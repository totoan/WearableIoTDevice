# Pi5 Wearable

A PySide6 application for a Raspberry Pi 5 and an 800x480 touchscreen.
Includes an animated home screen, local-time clock, shutdown confirmation,
and a direct Roku TV remote. No camera or microphone dependencies.

The optional PC dashboard and YouTube features require a compatible
DashboardAppV2 backend and Chrome extension, which are not included in
this Pi-side source export. The home screen and Roku remote run independently.

The YouTube browsing page now reads the dashboard's cached subscription uploads,
searches videos/channels/playlists, and opens creator playlists and their videos.

## File structure

The application separates startup, page layout, models, and widgets. Each control owns its behaviour,
while the home page handles layout and the main window handles pages.

```text
Wearable/
├── main.py                     # Application startup, arguments, and theme
├── main_window.py              # Main window and page container
├── background.py               # Animated paths and button glow
├── theme.qss                   # Colours and control styling
├── widgets/
│   ├── home_interface.py        # Home screen layout
│   ├── clock.py                 # Clock display and timer
│   ├── shut_down_button.py      # Power button, confirmation, and shutdown
│   ├── dashboard_interface.py   # Pairing and two-way test controls
│   ├── touch_keyboard.py        # Search keyboard
│   ├── touch_slider.py          # Tap/drag sliders; send changes on release
│   ├── roku_interface.py        # Direct living-room TV remote page
│   ├── roku_address_dialog.py   # Touch keypad for the TV's IPv4 address
│   ├── youtube_interface.py     # Three-tab YouTube page
│   └── youtube/
│       ├── now_playing_interface.py
│       ├── subscriptions_interface.py
│       ├── search_interface.py
│       ├── browse_interface.py   # Shared list navigation
│       └── video_list.py         # Thumbnail rows and touch scrolling
├── models/
│   ├── dashboard_handler.py     # PC connection, messages, and reconnecting
│   ├── youtube_handler.py       # List requests and response timeouts
│   ├── playback_handler.py      # Chrome state and playback commands
│   ├── roku_handler.py          # Direct Roku HTTP connection and buttons
│   └── thumbnail_handler.py     # Asynchronous thumbnail loading
├── config/
│   ├── dashboard.example.json   # Template exported to the Pi
│   ├── dashboard.json           # Local pairing settings; never exported
│   ├── roku.example.json        # Initial TV address (192.168.1.100)
│   └── roku.json                # Optional saved TV address; never exported
├── utils/
│   └── time_utils.py            # Local time helper
├── assets/
│   └── shut_down.png
├── requirements.txt
└── start-kiosk.sh               # Pi graphical session launcher
```

The folders also contain `__init__.py` files to identify Python packages.
Windows launchers and deployment tools live alongside Wearable in the project
root. Legacy files are not included. When adding a new application file,
add it to the export list in `tools/deploy.py` so CMD deployment includes it.

## PC dashboard connection

Start/restart the DashboardAppV2 backend to create its local pairing settings
in `backend/wearable/local/settings.json`. The dashboard's new **Wearable**
panel and this app's **PC Dashboard** page use the same pairing key.

For a Windows preview, both use `ws://localhost:5186/wearable/socket`. Save
and connect on each side, then press **Test dashboard** or **Test wearable**.
The receiver displays the message and automatically acknowledges it. The
backend and dashboard-page connection states are shown separately on the
wearable connection page. Network activity does not block the UI.

For the Pi, use `ws://YOUR_PC_LAN_ADDRESS:5186/wearable/socket`. Create
`config/dashboard.json` from `config/dashboard.example.json` over SSH and
fill in the address and pairing key before restarting the app. A touch
keyboard for pairing is not included; the YouTube search has its own keyboard.
Update the Pi's requirements for Qt WebSockets:

```sh
cd ~/Wearable
.venv/bin/python -m pip install -r requirements.txt
cp config/dashboard.example.json config/dashboard.json
nano config/dashboard.json
```

Only copy the example when setting up a device for the first time; do not
overwrite an existing pairing file. Deployment preserves this local file.

`localhost` is for the Windows preview only. On the Pi it points to the Pi itself,
so it cannot reach the PC dashboard. A “PC unavailable” message means the app
could not reach the backend; “Pairing rejected” means the backend rejected its key.

Allow private-LAN TCP port 5186 on the PC if necessary. The connection supports
tests, YouTube browsing, and selected-tab playback controls. It does not accept
arbitrary PC commands.
Full PC setup instructions live in DashboardAppV2's `backend/wearable/README.md`.

## YouTube browsing

Restart the dashboard backend to load this stage, then launch `preview.cmd`.
Saved pairing details are reused. Select **YouTube** from the home screen:

- **Subscriptions** reads the same latest 20 uploads shown on the dashboard.
  The dashboard refreshes Google every 15 minutes. While visible, the wearable
  reads the PC's completed cache each minute; **Reload list** reads it immediately
  without forcing another Google refresh. The timestamp is the PC refresh time.
- Select a video, then **Creator playlists**, to browse that creator's playlists.
  Select a playlist, then **Open playlist**, to list its videos. **Back** restores
  the previous list; **Load more** adds the next page where available.
- **Search** supports video, channel, and playlist results. Enter text with a
  physical keyboard or press **Keyboard** for the touch keyboard. Search runs
  only when submitted, not on each keypress. A channel result opens its creator
  playlists; a playlist result opens its videos using the same bottom controls.
- **Play on PC** sends a selected video to the YouTube tab chosen in the Chrome
  controller. A playlist selection retains its playlist and position. After
  Chrome confirms playback, the app switches to **Now Playing**.
- **Now Playing** shows the real title, creator, thumbnail, progress, and
  playback state. **Play/Pause** controls the selected tab; **Next** follows
  its playlist or YouTube's suggested next video. Unavailable controls are disabled.
  Drag or tap the position slider to choose a time; the command sends when you
  release it, and a paused video stays paused. The volume slider changes the
  YouTube video's volume only, leaving Windows volume unchanged. Adjusting it
  also unmutes YouTube. **Fullscreen** expands the selected video and its Chrome
  window; **Exit fullscreen** restores the window's previous size.

The wearable uses smaller fonts, margins, and 68-pixel video rows so more fits
on the 800x480 screen. Playback buttons remain approximately 40 pixels high.

Google credentials stay on the PC. Search and playlist pages are cached there
for five minutes. Only thumbnails are fetched directly from official YouTube
image hosts by the wearable. Existing subscription limits (50 channels, five
uploads per channel, newest 20 overall) are preserved in this stage. An unavailable
PC leaves the last loaded list visible, and requests are retried by selecting
**Reload list** after reconnecting.

For Pi testing, deploy as usual and reboot after restarting the PC backend.
The saved pairing file is preserved, and this stage adds no further dependencies.

## Chrome playback setup

Restart the updated dashboard backend. In Chrome, open `chrome://extensions`,
enable Developer mode, and use **Load unpacked** to load:

```text
PATH_TO_DashboardAppV2\wearable\chrome-extension
```

Open the extension popup, enter the same existing pairing key and
`ws://localhost:5186/wearable/socket`, and choose **Save and connect**.
Open a YouTube tab, refresh the popup's tab list, choose the desired tab,
and press **Use selected tab**. The extension remembers the key. Tab selection
survives worker restarts, but select the tab again after fully closing Chrome.

Run `preview.cmd`, open YouTube on the wearable, select a video, and press
**Play on PC**. Test play/pause and Next, then make a manual playback change
in Chrome and confirm the wearable updates within a few seconds.

For an existing installation, restart the backend, **Reload** the extension
in `chrome://extensions`, and reload its selected YouTube tab before testing
the new volume, seek, and fullscreen controls. Pairing settings remain saved.
Fullscreen brings the selected Chrome window to the front. Pressing F11 in
Chrome also exits the remotely requested fullscreen mode.

If Chrome blocks starting playback, press Play once directly in the YouTube
tab and retry. The extension's full installation guide is in
DashboardAppV2's `wearable/chrome-extension/README.md`. The extension remains
on the PC; normal Pi deployment includes only the wearable Python files.

## Living Room TV remote

The home screen's **Living Room TV** button opens a direct Roku remote.
Set your TV's IP with **TV address**. It connects on the local network without the PC dashboard,
Chrome extension, or Google credentials. No additional Pi packages are needed.

On the TV, verify **Settings → System → Advanced system settings → Control by
mobile apps → Network access → Enabled**. The Pi and TV must be on the same
home network. These commands use Roku's External Control Protocol:
https://developer.roku.com/dev/docs/external-control-api

To test from CMD, run `preview.cmd` and open **Living Room TV**. The page reads
the TV's device information automatically. Try navigation, OK, Back, TV home,
Options, Play / Pause, Rewind, Fast forward, Replay, Volume +/−, and Mute.
These are real TV commands even in the Windows preview. **TV power off** asks
for confirmation and affects the TV only, independently of the Pi power button.
This stage has no TV power-on or input-selection buttons.

Button behaviour follows the current Roku app. A successful message means the
TV accepted the key, rather than confirming a specific playback change. Network
requests run asynchronously, time out after four seconds, and are never replayed.
Press **Check TV** to reconnect after turning the TV back on or restoring Wi-Fi.
If the TV blocks a button, the page explains the required network-access setting.

**TV address** opens a numeric touch keypad. Saving creates `config/roku.json`,
which is preserved during later deployments. Without that local file, the app
uses `config/roku.example.json`, with the example address `192.168.1.100`. If its IP
changes, use the keypad or edit the local JSON over SSH. A DHCP reservation in
your router can keep this address stable. Only the example file is exported.

After the PC test, deploy from CMD:

```bat
cd /d PATH_TO_REPOSITORY\software
deploy.cmd --user YOUR_LOGIN --host YOUR_PI_HOST
```

Then restart the wearable app or reboot the Pi. No dashboard restart is needed
for this feature. This page provides basic remote buttons; YouTube browsing and
sending videos to the TV are separate future features.

## Test on Windows

From Command Prompt (`cmd.exe`):

```bat
cd /d PATH_TO_REPOSITORY\software
preview.cmd
```

The launcher uses the installed Python 3.12, creates `.venv` alongside Wearable,
and installs PySide6 when missing. The first launch needs internet access.
No environment activation is needed. Both Windows launchers run from CMD without PowerShell.

The window's content starts at 800x480. Windows display scaling can make its
physical pixel size larger; use 100% display scaling for a literal pixel preview.
Check the orange glow fades in/out and pauses, the clock advances every second,
and the lower-right power button opens a touch-sized confirmation. Cancel should
return to the UI; Shut down should show a simulated shutdown message and keep
Windows running. Escape closes the preview. Resizing should keep the clock centred
and the power button anchored at the bottom right.

Fullscreen preview:

```bat
preview.cmd --fullscreen
```

Fullscreen follows your PC monitor's size. The default window is the target-size
preview. Real shutdown is disabled by default and rejected on Windows even if
`--enable-shutdown` is supplied.

## Export and transfer

Inspect a clean export without contacting the Pi:

```bat
deploy.cmd --export-only
```

This prints a temporary folder containing only the deployment files. You may
delete that export folder after inspecting it.

Copy to the Pi's home directory (replace the login and host):

```bat
deploy.cmd --user YOUR_LOGIN --host YOUR_PI_HOST
```

The CMD launcher uses the installed Python 3.12 to prepare the export and calls
Windows OpenSSH `scp` directly. It does not need the UI `.venv` or PowerShell.
Requires working SSH access. SSH may prompt for a host
key or password. The default destination is `~/Wearable`. Legacy, the Windows
environment, and caches are excluded. Subsequent transfers overwrite app files
without replacing the Pi's `.venv`. The script transfers files only; it does not
install packages, launch the app, or reboot the Pi.

For another destination use `--remote-directory /home/YOUR_LOGIN`; the destination
parent must already exist. Paths containing spaces are not supported.

## First Pi setup (Raspberry Pi OS 64-bit Lite)

This initial deployment uses a small X11/Openbox session rather than a full desktop.
On the Pi, install the runtime and graphics dependencies:

```sh
sudo apt update
sudo apt install python3-venv xserver-xorg xinit openbox x11-xserver-utils fonts-dejavu-core libegl1 libopengl0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0
cd ~/Wearable
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
chmod +x start-kiosk.sh
```

The Pi environment is created locally; never copy the Windows `.venv`.
On the current Pi, X11 exposes the LCD as `HDMI-1` with a native 480x800 mode.
The launcher applies `xrandr --output HDMI-1 --rotate right` before opening the
app, producing the correct 800x480 landscape orientation. This setting was
confirmed on the device; X11's rotation differs from the Linux boot rotation.
The WaveShare WS170120 touchscreen already aligns correctly with this setting,
so the launcher does not apply an additional touch transformation. Verify all
four touch corners after reboot. If the display hardware changes, update the
output name and rotation in `start-kiosk.sh`.

From the Pi's local console (not a regular SSH shell), start the fullscreen UI:

```sh
startx "$HOME/Wearable/start-kiosk.sh" -- :0 -nocursor
```

This launch enables real shutdown. Confirming the power dialog runs
`sudo -n shutdown -h now`. If your user lacks passwordless permission, the UI
reports the error. To grant only this command, find its absolute path using
`command -v shutdown`, then use `sudo visudo -f /etc/sudoers.d/wearable-power`
and add the following, adjusting YOUR_LOGIN and the path:

```text
YOUR_LOGIN ALL=(root) NOPASSWD: /usr/sbin/shutdown -h now
```

For a safe Pi preview in an existing graphical session, omit `--enable-shutdown`:

```sh
~/Wearable/.venv/bin/python ~/Wearable/main.py --fullscreen
```

## Launch at boot after the manual test works

Enable Console Autologin for your user through `sudo raspi-config`. Add the
following to `~/.bash_profile` (preserve any existing content). If you create
that file for the first time, source `~/.profile` before this block to retain
your normal login environment.

```sh
if [ -z "${DISPLAY:-}" ] && [ "$(tty)" = /dev/tty1 ]; then
    startx "$HOME/Wearable/start-kiosk.sh" -- :0 -nocursor >> "$HOME/Wearable/startup.log" 2>&1
fi
```

The X server's `-nocursor` option hides the pointer throughout the graphical
session, while touchscreen and mouse input continue to work. To restore the
pointer for debugging, remove `-nocursor` and restart the graphical session.

Reboot to check startup. The tty1 condition keeps SSH logins usable. Escape exits
the app to the console; it will launch again at the next login/reboot. To disable
boot launch, remove this block through SSH. After deploying updates, exit and
restart the app or reboot. Run `.venv/bin/python -m pip install -r requirements.txt` when dependencies
change. The Qt WebSockets module requires PySide6-Addons; the requirements
file includes it.

References: [Qt Linux graphics dependencies](https://doc.qt.io/qt-6/linux-requirements.html),
[Raspberry Pi configuration](https://www.raspberrypi.com/documentation/computers/configuration.html).
