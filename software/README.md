# Pi5 wearable software

Pi-side application for Raspberry Pi OS 64-bit Lite and a Waveshare touchscreen
used in 800x480 landscape orientation. Camera support is currently inactive.

## Included

- Animated home screen, clock, and confirmed Pi shutdown.
- Direct Roku TV remote, independent of the PC.
- Optional dashboard connection and YouTube browsing/playback client.
- Windows CMD preview and clean SCP deployment scripts.

The PC dashboard backend and Chrome extension are separate dependencies and
are not included here. No pairing keys, Google credentials, local device settings,
virtual environments, logs, or Legacy files are included.

```text
software/
    Wearable/      Pi application: models, widgets, assets, and example settings
    tools/         Clean deployment exporter
    preview.cmd    Windows preview launcher
    deploy.cmd     SCP deployment launcher
```

See [the application guide](Wearable/README.md) for Pi graphics setup, boot
startup, pairing, Roku configuration, and shutdown permissions.

## Windows preview

From CMD in this `software` folder, run:

```bat
preview.cmd
```

The launcher uses Python 3.12 and creates a local `.venv`. Pi shutdown is
simulated during Windows preview; Roku buttons still control your configured TV.

## Deploy

From CMD in this `software` folder:

```bat
deploy.cmd --export-only
deploy.cmd --user YOUR_LOGIN --host YOUR_PI_HOST
```

The first command prepares a clean export for inspection. The second copies it
to `~/Wearable`; install dependencies and restart the app separately on the Pi.
Existing local pairing settings and the Pi's `.venv` are preserved.

The public Roku address is only an example. Set your own using the TV address
keypad. Keep `Wearable/config/dashboard.json` and `Wearable/config/roku.json`
local; both are excluded from Git and deployment exports.
