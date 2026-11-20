# AnyPC OS

**An open-source, console-style operating system for ordinary PCs.**
Boot a regular computer straight into a controller-first, living-room interface — your games, your emulators, one system.

> Status: **pre-alpha / planning.** Nothing here is usable yet. See the [roadmap](docs/ROADMAP.md).

## Goals

- Run on as many x86_64 PCs as possible (AMD, Intel, NVIDIA) from a USB installer.
- Boot directly into a console-style launcher, fully usable with a gamepad.
- Immutable base system with atomic updates and one-click rollback.
- First-class game support: Steam/Proton, native Linux games, legal emulators.
- Optional compatibility module for [AnyPS5](https://github.com/boykopovar/AnyPS5) (third-party project, see below).
- Everything open source (GPL-3.0-or-later). No proprietary blobs in this repository.

## Architecture (short version)

```
┌──────────────────────────────────────────┐
│ AnyPC Launcher  (controller-first UI)     │
├──────────────────────────────────────────┤
│ Game runtimes: Steam/Proton · emulators · │
│ AnyPS5 compat layer (optional module)     │
├──────────────────────────────────────────┤
│ Base image: Linux (Fedora Atomic-style),  │
│ Mesa/Vulkan, PipeWire, gamescope          │
└──────────────────────────────────────────┘
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Legal

AnyPC OS is an independent project. It is **not affiliated with, authorized or endorsed by Sony Interactive Entertainment**, Valve or any other console/platform vendor. This repository contains **no** console firmware, encryption keys, game files or proprietary libraries, and will never accept contributions that include them. Users must bring their own legally obtained files. See [docs/LEGAL.md](docs/LEGAL.md).

## Related projects

- [AnyPS5](https://github.com/boykopovar/AnyPS5) — separate, independent project by its own authors. AnyPC OS may offer it as an optional module with full credit; we are not part of it.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). License: [GPL-3.0-or-later](LICENSE).
