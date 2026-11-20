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

## Service API (localhost only)

| Method | Path                         | Purpose                         |
|--------|------------------------------|---------------------------------|
| GET    | `/api/state`                 | Version, demo flag, running game |
| GET    | `/api/games[?refresh]`       | Installed games                 |
| GET    | `/api/games/<id>/art`        | Cover art or icon, if any       |
| POST   | `/api/games/<id>/launch`     | Start a game                    |
| GET    | `/api/running`               | Game currently running          |
| POST   | `/api/running/stop`          | Quit the running game           |
| GET/POST | `/api/users`               | Profiles                        |
| GET/POST | `/api/settings`            | Settings (validated keys only)  |
| GET    | `/api/system`                | Hardware information            |
| GET/POST | `/api/audio`               | Volume and mute (PipeWire)      |
| GET    | `/api/network`               | Connections (NetworkManager)    |
| POST   | `/api/power/<action>`        | `suspend`, `reboot`, `poweroff`, `desktop` |

The service listens on 127.0.0.1 only, rejects requests for other host names, and
requires an `X-AnyPC: 1` header on every POST so web pages cannot drive it.
State is kept in `~/.config/anypc/state.json`.

## Tests

```sh
cd shell/daemon && python3 -m unittest discover -s tests
```
