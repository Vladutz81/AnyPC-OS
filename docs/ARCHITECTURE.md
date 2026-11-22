# Architecture

AnyPC OS is a Linux distribution whose session is a console shell instead of a
desktop.

```
┌──────────────────────────────────────────────┐
│ Shell UI (shell/ui) — full-screen, gamepad   │
│   ⇅ JSON over 127.0.0.1                      │
│ anypc-shelld (shell/daemon) — games, audio,  │
│   network, power, users, settings            │
├──────────────────────────────────────────────┤
│ Session: greetd → anypc-session → gamescope  │
├──────────────────────────────────────────────┤
│ Base image: Fedora bootc (atomic updates,    │
│ rollback), Mesa/Vulkan, PipeWire, NM, BlueZ  │
└──────────────────────────────────────────────┘
```

## 1. Base image (`build/`)
- Bootable container on `quay.io/fedora/fedora-bootc`. The whole OS is one image:
  updates are atomic and `bootc rollback` returns to the previous version.
- Installer ISO and VM images are produced with bootc-image-builder.

## 2. Session (`session/`)
- greetd logs the `player` account straight into `anypc-session`.
- `anypc-session` runs gamescope; inside it `anypc-session-inner` starts the
  service and the UI (Chromium in kiosk mode).
- Games inherit the gamescope display, so they open on top of the shell and the
  shell comes back when they exit.
- "Switch to desktop" leaves a flag that makes the session start a desktop
  environment instead, if one is installed.

## 3. Shell UI (`shell/ui`)
- Plain HTML/CSS/JS modules, no build step, no network access (fonts bundled).
- One input layer for gamepad (standard mapping), keyboard and mouse with
  spatial navigation.
- Sized in rem units tied to the screen, so the layout is identical from a
  handheld to a 4K TV.
- Strings in `js/i18n.js` (English, Romanian).

## 4. Shell service (`shell/daemon`)
- Python 3 standard library only.
- Discovers games: desktop entries with the `Game` category (native and Flatpak)
  and Steam libraries (`appmanifest_*.acf`, including extra library folders).
- Launches one game at a time and records play time.
- Wraps system tools: `wpctl` (audio), `nmcli` (network), `systemctl` (power).
- Local-only HTTP API; see `shell/README.md`.

## 5. Compatibility modules
- Steam/Proton, native and Flatpak games are supported by the service today.
- The curated catalog installs optional emulators. AnyPS5 imports compatible
  unencrypted local exports and remains an independent upstream project.
- Leonida is an independent experimental module. Its fixed native CPU checks run
  asynchronously without privileges; the UI reports diagnostics, not game or GPU
  compatibility. See compat/leonida/README.md.

## 6. Hardware targets
- Tier 1: x86_64 PCs with AMD or Intel GPUs, UEFI.
- Tier 2: NVIDIA GPUs, older BIOS machines.
- Later: handhelds, ARM.
