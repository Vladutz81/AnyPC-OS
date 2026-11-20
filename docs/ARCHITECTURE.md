# Architecture

## 1. Base image
- Start from an existing distribution instead of writing an OS from scratch. Default candidate: **Fedora Atomic (ostree / bootc)**, the approach used by Bazzite. Alternatives: Arch, Debian.
- Immutable root, atomic updates, rollback to the previous image.
- Kernel with broad hardware support; Mesa (AMD/Intel) and NVIDIA proprietary driver variant installed from vendor packages, not redistributed by us in-tree.
- PipeWire audio, Bluetooth, controller drivers (xpad, hid-playstation, hid-nintendo, Steam Input).

## 2. Session
- Boot straight into a **gamescope** session running the launcher.
- Optional "desktop mode" (KDE/GNOME) reachable from the launcher.

## 3. Launcher (`launcher/`)
- Controller-first UI: library, store links, settings (network, display, audio, accounts), power menu.
- Candidate stack: Qt/QML or Rust + a GPU UI toolkit. Decision pending (see ROADMAP M1).
- Game sources are plugins: Steam, native Linux, emulators, AnyPS5 module.

## 4. Compatibility modules (`compat/`)
- Each module is optional, separately packaged, and clearly labelled with its upstream and license.
- `compat/anyps5/`: integration glue only (detect module, launch, map controller). The AnyPS5 code itself stays upstream.

## 5. Build & release (`build/`)
- Container-based image build (`Containerfile`), CI producing an ISO and an update image.
- Reproducible builds as a goal.

## 6. Hardware targets
- Tier 1: x86_64 PCs with AMD or Intel GPUs, UEFI.
- Tier 2: NVIDIA GPUs, older BIOS machines.
- Later: handhelds, ARM.
