# AGENTS.md — instructions for coding agents (Codex and others)

Read this file fully before changing anything. It is the source of truth for how
work is done in this repository.

## Who you work for

- Owner: Vladutz81. He writes in **Romanian** and is not a professional developer.
  Answer him in Romanian, in plain words, and explain what changed and how to try it.
- Code, comments, commit messages, docs and UI string keys are in **English**.
  UI text exists in English and Romanian (`shell/ui/js/i18n.js`); add every new
  string to **both** languages.

## What AnyPC OS is

An open-source Linux distribution that turns an ordinary PC into a games console:
the PC boots straight into a full-screen, gamepad-first interface (the "shell")
instead of a desktop. Keyboard and mouse work everywhere too.

```
shell/ui/        Shell UI — plain HTML/CSS/JS modules, no build step, no network
shell/daemon/    anypc-shelld — local HTTP service (Python 3, standard library only)
session/         Boot into the shell: greetd → anypc-session → gamescope → UI
session/polkit/  Rule letting the console user change settings without a password
session/systemd/ Units (bootc updates run as root, report to /run/anypc/update.json)
build/           Containerfile (Fedora bootc image) + installer instructions
docs/            ARCHITECTURE.md, ROADMAP.md, LEGAL.md
compat/anyps5/   Integration notes for the optional, separate AnyPS5 project
```

Read `docs/ARCHITECTURE.md` and `shell/README.md` (API table, controls) next.

## Non-negotiable rules

1. **Legal** (`docs/LEGAL.md`): never add console firmware, BIOS files, encryption
   keys, game files, leaked code or tools to bypass DRM/console security. Never use
   "PlayStation", "PS5" or Sony marks in names, logos or UI. AnyPS5 is a separate
   upstream project; we only integrate with it and credit it.
2. **No runtime network access from the UI.** Fonts and assets are bundled.
   No CDNs, no analytics, no telemetry.
3. **The daemon stays standard-library Python** (no pip dependencies) and listens on
   127.0.0.1 only. Keep its protections: Host header check, `X-AnyPC: 1` required on
   every POST, strict validation of every input, commands run as argv lists (never a
   shell string), no user-supplied paths. Never pass user input to a shell.
4. **Privileged actions** go through polkit rules or root systemd units with a fixed
   command — never sudo, never setuid, never a generic "run command" endpoint.
5. **Everything must work with a gamepad alone**, and also with keyboard and with
   mouse. Every focusable element is a real `<button>`, `<a href>` or `<input>`.
   Text entry for gamepad users goes through the on-screen keyboard
   (`keyboard()` in `shell/ui/js/layers.js`).
6. **Escape all dynamic text** in the UI with `esc()` (game names come from files on
   disk). No inline event handlers (the CSP blocks them).
7. **Keep the visual style** (see "Design language" below). Do not introduce new
   fonts, colour schemes or UI frameworks.
8. **Demo parity**: every API feature needs a working fake in `DemoBackend`
   (`shell/daemon/anypc_shelld/system.py`) **and** in the UI's offline demo
   (`shell/ui/js/api.js`), so the shell can be tried without touching the system.
9. Do not merge to `main` or force-push. Work on a branch and open a pull request.

## How to run and check

```sh
# Run the shell in demo mode (sample games, changes nothing on the machine)
cd shell/daemon && python3 -m anypc_shelld --demo
# open http://127.0.0.1:7700/  (add ?noboot to skip the boot animation)

# Run all checks — must pass before every commit
./scripts/check.sh
```

`scripts/check.sh` runs the daemon unit tests, syntax-checks every UI module and the
shell scripts, checks that every UI string exists in every language, and runs the
end-to-end UI test (`tests/e2e/test_shell.py`, headless Chromium with a simulated
gamepad) when Playwright is installed:

```sh
pip install playwright && python3 -m playwright install chromium
```

Real-system behaviour (Wi-Fi, Bluetooth, bootc, gamescope) cannot be tested in CI;
cover the parsing and validation with unit tests and keep the demo backends honest.

## Code conventions

### Daemon (`shell/daemon/anypc_shelld/`)
- `server.py`: routes. GET returns state; POST performs actions and returns the new
  state. Errors: `ValueError` → 400 (bad input), `KeyError` → 404,
  `SystemError_` → 422 (the action failed; message is shown to the user),
  `RuntimeError` → 409.
- `system.py`: `Backend` wraps system tools (`wpctl`, `nmcli`, `bluetoothctl`,
  `timedatectl`, `hostnamectl`, `systemctl`, `/sys`, `/proc`). Put parsing in small
  pure functions (`parse_*`) and unit-test them with captured real output.
- `store.py`: settings are whitelisted with types (`SETTING_TYPES`) and allowed
  values (`SETTING_CHOICES`). New settings go there with a default.
- `games.py`: game discovery (desktop entries, Flatpak, Steam libraries, emulators).
- Tests live in `shell/daemon/tests/` (unittest, no extra packages).

### UI (`shell/ui/js/`)
- `app.js`: screen stack + layers (control center, dialogs, keyboard), data loading,
  launching games, clock, idle rest.
- `input.js`: gamepad (standard mapping), keyboard and mouse → move / activate / back /
  menu / tab. Spatial navigation; containers can use `data-group` + `data-entry`
  (landing element), `data-vtrap` (up/down stay inside), `data-rows` (left/right stay
  in the row), `data-scroll` (keep the focused element visible).
- `layers.js`: `dialog()`, `choose()`, `keyboard()` — all return Promises.
- `screens/*.js`: one class per screen with `el`, `act(action, button)`, optional
  `onBack`, `onTab`, `onShow`, `on(event)`, `dispose`. Clicks are delegated through
  `data-act` attributes.
- `css/shell.css`: sizes in `rem`; 1rem = 16px on a 1280×720 screen and scales with
  the display, so layouts are identical from handhelds to 4K TVs.

### Design language
Deep navy background with a soft blue radial glow (`--ground #020718`,
`--navy #0D2C78`, `--glow #2A62D6`), white text, accent `#4C7DFF`, font Exo 2
(bundled, OFL). Focus = white ring + soft blue glow and a slight scale. Light
particles and slow ribbons in the background. Wide letter-spaced uppercase for
titles like the boot screen. Glass cards: translucent navy with a thin light border.
The logo is a power ring with an "A" rising through the gap (`mark()` in `icons.js`).

## Git and pull requests

- Branch from the latest `shell-m1` (until PR #1 is merged), later from `main`.
  Name branches `codex/<short-topic>`.
- Small, focused commits with clear English messages. Run `./scripts/check.sh` first.
- In the PR description: what changed, how it was tested, what could not be tested
  on real hardware, screenshots of UI changes.
- Update `docs/ROADMAP.md` checkboxes and `shell/README.md` (API table) when you add
  or finish something.

## What to work on next

The prioritized backlog with acceptance criteria is in **`docs/TASKS.md`**. Take the
first unchecked task unless the owner asks for something else. When a task is done,
tick it there in the same pull request.
