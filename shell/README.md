# AnyPC OS shell

The console interface of AnyPC OS: what you see after boot instead of a desktop.

```
shell/
├── ui/       HTML/CSS/JS interface (no build step, no external requests)
└── daemon/   anypc-shelld, the local service the UI talks to (Python 3, stdlib only)
```

## Try it on any computer

```sh
cd shell/daemon
python3 -m anypc_shelld --demo        # sample games, changes nothing on your system
```

Open http://127.0.0.1:7700/ in Chromium or Chrome (full screen with F11).
Without `--demo` the service lists the games actually installed on your machine
(desktop entries with the `Game` category, Flatpak games and Steam libraries) and
really launches them.

Opening `ui/index.html` straight from disk also works: with no service running the
UI falls back to a built-in demo.

## Controls

| Action         | Gamepad            | Keyboard              | Mouse        |
|----------------|--------------------|-----------------------|--------------|
| Move           | D-pad / left stick | Arrow keys            | Point        |
| Select         | A                  | Enter / Space         | Click        |
| Back           | B                  | Esc / Backspace       | Back button  |
| Control center | Guide / Start      | Home / F1             | Bell icon    |
| Switch tab     | LB / RB            | Page Up / Page Down   | Click tab    |
| Keyboard: delete / space | LB / RB  | Backspace / Space     | Click keys   |

## Service API (localhost only)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/state` | Version, demo flag, running game |
| GET | `/api/games[?refresh]` · `/api/games/<id>/art` | Installed games, cover art |
| POST | `/api/games/<id>/launch` · `/api/running/stop` | Start / quit a game |
| GET/POST | `/api/users` · `/api/users/<id>` · `/api/users/<id>/delete` | Profiles |
| GET/POST | `/api/settings` · `/api/settings/reset` | Shell settings (validated keys only) |
| GET/POST | `/api/audio` | Volume, mute, output device (PipeWire) |
| GET | `/api/network[?rescan]` | Connections, Wi-Fi networks, saved networks |
| POST | `/api/network/wifi` · `/connect` · `/disconnect` · `/forget` | Wi-Fi on/off, join, leave, forget (NetworkManager) |
| GET | `/api/bluetooth` | Adapter and devices (BlueZ) |
| POST | `/api/bluetooth/power` · `/scan` · `/pair` · `/connect` · `/disconnect` · `/remove` | Pairing and connections |
| GET/POST | `/api/displays` | Connected displays, resolution used by the session |
| GET/POST | `/api/timedate` · GET `/api/timezones` | Time zone, automatic time |
| POST | `/api/hostname` | Device name |
| GET | `/api/storage` | Drives and free space |
| GET/POST | `/api/updates` · `/api/updates/check|apply|rollback` | System updates (bootc) |
| GET | `/api/catalog` | Curated applications, available imports and current operation |
| POST | `/api/catalog/action` | Install, open or update a catalog ID, scan USB, or import a detected title |
| GET | `/api/modules` | Availability of the installed AnyPS5 runtime and registered exports |
| GET | `/api/system` | Hardware information |
| POST | `/api/power/<action>` | `suspend`, `reboot`, `poweroff`, `restart-shell` |

Actions that need more rights (time zone, device name, updates) are allowed for
the console user by `session/polkit/50-anypc.rules`; updates run as root in the
`anypc-update*.service` units and report progress in `/run/anypc/update.json`.

The service listens on 127.0.0.1 only, rejects requests for other host names, and
requires an `X-AnyPC: 1` header on every POST so web pages cannot drive it.
State is kept in `~/.config/anypc/state.json`.

For converted Linux applications, see the [AnyPS5 registration guide](../compat/anyps5/README.md).

## Tests

From the repository root, run the same checks as GitHub Actions. Install Node 20
for the JavaScript checks and Playwright with Chromium for the demo UI test.

```sh
python3 -m pip install playwright==1.65.2
python3 -m playwright install chromium
./scripts/check.sh
```
