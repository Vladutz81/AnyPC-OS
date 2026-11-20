# AnyPC OS

[![CI](https://github.com/Vladutz81/AnyPC-OS/actions/workflows/ci.yml/badge.svg)](https://github.com/Vladutz81/AnyPC-OS/actions/workflows/ci.yml)

**An open-source, console-style operating system for ordinary PCs.**
Boot a regular computer straight into a controller-first, living-room interface — your games, your emulators, one system.

> Status: **pre-alpha.** The console shell runs (try it in demo mode below); the bootable image is not built yet. See the [roadmap](docs/ROADMAP.md).

## Try the shell

```sh
cd shell/daemon
python3 -m anypc_shelld --demo
```

Then open http://127.0.0.1:7700/ in Chromium or Chrome. Use a gamepad, the arrow keys
and Enter, or the mouse. Details: [shell/README.md](shell/README.md).

## Goals

- Run on as many x86_64 PCs as possible (AMD, Intel, NVIDIA) from a USB installer.
- Boot directly into a console-style interface, fully usable with a gamepad, keyboard or mouse.
- Immutable base system with atomic updates and one-click rollback.
- First-class game support: Steam/Proton, native Linux games, legal emulators.
- Optional compatibility module for [AnyPS5](https://github.com/boykopovar/AnyPS5) (third-party project, see below).
- Everything open source (GPL-3.0-or-later). No proprietary blobs in this repository.

## Architecture (short version)

```
┌──────────────────────────────────────────┐
│ Shell UI — console interface, gamepad,    │
│ keyboard and mouse                        │
│ anypc-shelld — games, audio, network,     │
│ power, users, settings                    │
├──────────────────────────────────────────┤
│ Session: greetd → gamescope → shell       │
├──────────────────────────────────────────┤
│ Base image: Fedora bootc (atomic updates, │
│ rollback), Mesa/Vulkan, PipeWire          │
└──────────────────────────────────────────┘
```

| Folder     | What it is                                  |
|------------|---------------------------------------------|
| `shell/`   | The console interface and its local service |
| `session/` | Scripts that boot into the console session  |
| `build/`   | OS image (Containerfile) and installer notes |
| `compat/`  | Optional compatibility modules              |
| `docs/`    | Architecture, roadmap, legal notes          |

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Legal

AnyPC OS is an independent project. It is **not affiliated with, authorized or endorsed by Sony Interactive Entertainment**, Valve or any other console/platform vendor. This repository contains **no** console firmware, encryption keys, game files or proprietary libraries, and will never accept contributions that include them. Users must bring their own legally obtained files. See [docs/LEGAL.md](docs/LEGAL.md).

## Related projects

- [AnyPS5](https://github.com/boykopovar/AnyPS5) — separate, independent project by its own authors. AnyPC OS may offer it as an optional module with full credit; we are not part of it.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). License: [GPL-3.0-or-later](LICENSE).
