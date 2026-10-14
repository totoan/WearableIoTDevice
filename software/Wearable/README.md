# Pi5 Wearable

A PySide6 application for a Raspberry Pi 5 and an 800x480 touchscreen.
Includes an animated home screen, local-time clock, shutdown confirmation,
and a direct Roku TV remote. Camera features are inactive; microphone dictation is included.

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
│   ├── home_interface.py        # Clock and three breathing icon buttons
│   ├── glow_icon_button.py      # Shared transparent home icon control
│   ├── settings_interface.py    # PC, microphone, and Wi-Fi settings menu
│   ├── media_interface.py       # YouTube and TV choices
│   ├── clock.py                 # Clock display and timer
│   ├── shut_down_button.py      # Confirmed shutdown/reboot and preview safety
│   ├── power_menu.py            # Reboot, Shut down, and Cancel choices
│   ├── dashboard_interface.py   # Pairing and two-way test controls
│   ├── touch_keyboard.py        # Shared text keyboard and offline dictation
│   ├── microphone_interface.py  # Input selection and voice test
│   ├── wifi_interface.py        # Nearby networks and password entry
│   ├── touch_slider.py          # Tap/drag sliders; send changes on release
│   ├── roku_interface.py        # Compact living-room TV remote
│   ├── roku_find_interface.py   # Discover, select, or manually connect a TV
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
│   ├── speech_handler.py        # Shared voice service and saved microphone
│   ├── speech_worker.py         # Capture/recognition threads
│   ├── pc_speech_client.py      # Paired PC dictation with offline fallback
│   ├── wifi_handler.py          # Asynchronous NetworkManager operations
│   ├── roku_handler.py          # Direct Roku HTTP connection and buttons
│   ├── roku_discovery.py        # Local network search and TV verification
│   └── thumbnail_handler.py     # Asynchronous thumbnail loading
├── config/
│   ├── dashboard.example.json   # Template exported to the Pi
│   ├── dashboard.json           # Local pairing settings; never exported
│   ├── roku.example.json        # Initial TV address (192.168.1.100)
│   └── roku.json                # Optional saved TV address; never exported
├── utils/
│   ├── time_utils.py            # Local time helper
│   ├── audio_devices.py         # Select microphones by name
│   └── setup_speech.py          # One-time offline model download
├── assets/
│   ├── shut_down.png
│   ├── settings.svg
│   ├── media.svg
│   ├── arrow.svg
│   └── microphone.svg
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
panel and this app's **Settings → PC Dashboard connection** page use the same pairing key.

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
Saved pairing details are reused. Select **Media → YouTube** from the home screen:

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

Run `preview.cmd`, open **Media → YouTube** on the wearable, select a video, and press
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

Open **Media → Living Room TV** from the home screen for the direct Roku remote.
Set your TV's IP with **TV address**. It connects on the local network without the PC dashboard,
Chrome extension, or Google credentials. No additional Pi packages are needed.

On the TV, verify **Settings → System → Advanced system settings → Control by
mobile apps → Network access → Enabled**. The Pi and TV must be on the same
home network. These commands use Roku's External Control Protocol:
https://developer.roku.com/dev/docs/external-control-api

To test from CMD, run `preview.cmd` and open **Media → Living Room TV**. The page reads
the TV's device information automatically. Try navigation, OK, Back, TV home,
Options, Play / Pause, Rewind, Fast forward, Replay, Volume +/−, and Mute.
These are real TV commands even in the Windows preview. **TV power off** asks
for confirmation and affects the TV only, independently of the Pi power button.
This stage has no TV power-on or input-selection buttons.

Button behaviour follows the current Roku app. A successful message means the
TV accepted the key, rather than confirming a specific playback change. Network
requests run asynchronously, time out after four seconds, and are never replayed.
Open **Find TV → Connect saved TV** to reconnect after turning the TV back on
or restoring Wi-Fi.
If the TV blocks a button, the page explains the required network-access setting.

**TV address** opens a numeric touch keypad. Saving creates `config/roku.json`,
which is preserved during later deployments. Without that local file, the app
uses `config/roku.example.json`, with the example address `192.168.1.100`. If its IP
changes, search again, use the keypad, or edit the local JSON over SSH. A DHCP reservation in
your router can keep this address stable. Only the example file is exported.

After the PC test, deploy from CMD:

```bat
cd /d PATH_TO_REPOSITORY\software
deploy.cmd --user YOUR_LOGIN --host YOUR_PI_HOST
```

Then restart the wearable app or reboot the Pi. No dashboard restart is needed
for this feature. This page provides basic remote buttons; YouTube browsing and
sending videos to the TV are separate future features.

## Finding a Roku TV

In the controller, open **Find TV**. A five-second local network search lists
responding Roku televisions by name, model, and IP address. Select one and press
**Connect selected TV**. The successful selection is saved for later sessions.

**Search again** repeats discovery; **Connect saved TV** retries your saved TV.
**Enter address** provides the manual touch keypad. Leaving this menu stops the
search. Roku streaming players are filtered out of the results.

The remote uses compact buttons and vector arrow icons for the four directions.
Connection setup stays in Find TV. Discovery uses SSDP multicast and direct
HTTP device checks, independently of the PC dashboard. A sleeping TV, guest
network isolation, or blocked multicast can prevent discovery; turn the TV on
or use its known IP address. No extra Python dependencies are needed.

## Wi-Fi settings

Open Settings → Wi-Fi to scan nearby wireless networks. Select a network and
press Connect selected network. New protected networks prompt for a masked
password using the touch keyboard; Symbols and Shift provide punctuation and
capital letters. Previously saved passwords are reused by NetworkManager.
The app passes passwords over process stdin, never command arguments, logs,
or app configuration. NetworkManager stores its own connection credentials
outside this project. Password fields disable microphone dictation.

Windows preview shows sample networks and simulates connection without changing
your PC networking. Real scanning and connection need the Pi's NetworkManager:

```sh
nmcli general status
nmcli general permissions
```

If nmcli is missing, install `network-manager`. The normal Raspberry Pi OS
local, active console session should have permission. If connection reports
an authorization failure, configure a narrowly scoped Polkit rule over SSH:

```sh
sudo nano /etc/polkit-1/rules.d/49-wearable-wifi.rules
```

Add this, replacing YOUR_LOGIN with the Pi login:

```javascript
polkit.addRule(function(action, subject) {
    var allowed = [
        "org.freedesktop.NetworkManager.network-control",
        "org.freedesktop.NetworkManager.settings.modify.system",
        "org.freedesktop.NetworkManager.wifi.scan"
    ];
    if (subject.user == "YOUR_LOGIN" && subject.local && subject.active &&
        allowed.indexOf(action.id) >= 0) {
        return polkit.Result.YES;
    }
});
```

Save in nano, then set ordinary root-owned permissions and restart the app:

```sh
sudo chown root:root /etc/polkit-1/rules.d/49-wearable-wifi.rules
sudo chmod 644 /etc/polkit-1/rules.d/49-wearable-wifi.rules
```

Polkit reloads its rules automatically. No sudo permission for arbitrary nmcli
commands is needed. The rule applies to the local active wearable session,
not an SSH session. Enterprise networks requiring identities/certificates and
hidden networks need separate NetworkManager configuration in this version.
Switching networks can disconnect SSH and change the Pi's address.

Reference: [NetworkManager nmcli manual](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nmcli.html).

## Voice input

The reusable text keyboard includes Speak, Stop, an input-level meter, and a
live speech preview. Stop inserts recognized text at the cursor; it remains
editable until you explicitly submit. Recording never submits a search or sends
a message. Cancel discards unfinished dictation. Each recording is limited to
two minutes. Titles, submit labels, and text limits can vary so future message
screens can use the same keyboard and voice service.

Recognition prefers the paired PC when its backend is connected. The PC uses
the larger English Whisper small.en model locally on its CPU. If unavailable,
the Pi keeps the Vosk offline result from the same recording. No cloud account
or subscription is required. The keyboard indicates PC Whisper or offline
after insertion; accuracy still varies, so review text before submitting.

Audio stays in memory on the Pi. When using PC recognition, it is sent to the
paired backend, briefly written inside its ignored wearable/local/speech/requests
folder, and deleted after completion or cancellation. Audio and transcripts
are not saved to app preferences or exported. Initial model downloads need
internet; recognition afterward does not. This uses the existing paired LAN
connection and pairing key.

Install the companion PC speech service and restart the dashboard backend
to load the speech endpoint. To prepare the PC speech model,
run this from DashboardAppV2 in CMD:

```bat
backend\wearable\speech\setup.cmd
```

It creates an isolated Python environment and downloads the approximately
500 MB model into ignored backend/wearable/local/speech storage. Python 3.12
is required. Then restart the dashboard backend. Keep the Pi offline model
installed even when PC speech is available.

On Windows, run this once from the project folder in CMD:

```bat
setup-voice.cmd
preview.cmd
```

Open Settings → Microphone, choose an input, and press Save microphone. Test
dictation opens the same keyboard. The system default is used until you select
a microphone. Device names and audio APIs are saved rather than USB device
numbers. Mono/stereo inputs and common native sample rates are supported.

After deployment, set up voice on the Pi over SSH:

```sh
sudo apt update
sudo apt install libportaudio2 alsa-utils
cd "$HOME/Wearable"
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python utils/setup_speech.py
sudo reboot
```

The model lives in `speech_models/vosk-model-small-en-us-0.15` and is downloaded
separately on PC and Pi. Normal deployment preserves it and excludes it from
transfers. Saved microphone settings in `config/speech.json` are also preserved
and excluded from Git/export. If the model or microphone is unavailable, the
keyboard shows guidance and ordinary typing remains available.

For Linux microphone troubleshooting, run `arecord -l`. If access is denied,
check the login user's audio permissions. References:
[Vosk model](https://alphacephei.com/vosk/models) and
[audio input formats](https://python-sounddevice.readthedocs.io/en/latest/api/checking-hardware.html).

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
and all three home icon glows breathe with the background. Settings is in the
upper right; Media is in the lower left; Power remains in the lower right.
Check Settings opens the PC connection menu, and Media offers YouTube and the
TV remote. Back returns to the containing menu; Home returns to the clock.
The power button opens Reboot, Shut down, and Cancel choices. Each action
requires confirmation. Windows previews simulate both actions and keep the PC
running. Cancelling either dialog returns to the UI. Escape closes the preview. Resizing should keep the clock centred
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
reports the error. To grant only these two actions, find the command's absolute path using
`command -v shutdown`, then use `sudo visudo -f /etc/sudoers.d/wearable-power`
and add the following, adjusting YOUR_LOGIN and the path:

```text
YOUR_LOGIN ALL=(root) NOPASSWD: /usr/sbin/shutdown -h now, /usr/sbin/shutdown -r now
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
