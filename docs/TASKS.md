# Task backlog

Ordered by priority. Each task lists what "done" means. Tick the box in the pull
request that completes it. Rules for all tasks: see `AGENTS.md`.

## Current state (Nov 2026)

Working in demo mode and covered by tests: boot animation, profiles, first-time
setup, home, library, game hub, control center, full settings (display, sound,
network, Bluetooth, controllers, storage, users, compatibility, date & time, power,
system updates, accessibility, language), on-screen keyboard, gamepad / keyboard /
mouse navigation, English + Romanian. Session scripts, polkit rule, update units and
a Fedora bootc Containerfile exist but **the OS image has never been built or
booted**. Nothing has been tested on real hardware yet.

---

## 1. Continuous integration
- [ ] `.github/workflows/ci.yml`: on every push and PR run `./scripts/check.sh`
      (Python 3.11+, Node 20 for syntax checks, Playwright Chromium for the e2e test).
- [ ] Badge in `README.md`.

Done when: CI is green on the PR that adds it, and a deliberately broken test makes it fail.

## 2. Build the OS image in CI
- [ ] `.github/workflows/image.yml`: build `build/Containerfile` with Podman/Buildah
      and push to `ghcr.io/vladutz81/anypc-os` (tags: branch name and `latest` for `main`).
- [ ] Fix whatever the first real build breaks (package names, paths, `bootc container lint`).
- [ ] Job that produces a `qcow2` and an `anaconda-iso` with bootc-image-builder and
      uploads them as workflow artifacts (manual trigger is enough).
- [ ] `build/README.md` updated with the exact commands that worked.

Done when: an ISO artifact can be downloaded from a workflow run.

## 3. First boot in a virtual machine
- [ ] Script `build/run-vm.sh` that boots the qcow2 in QEMU with virtio-gpu.
- [ ] Verify: greetd autologin → gamescope → boot animation → setup → home.
- [ ] Verify real (non-demo) settings in the VM: audio volume, network status,
      time zone, device name, update check (bootc), restart shell, power off.
- [ ] Record problems found as new tasks below; fix the blocking ones.

Done when: a screen recording or screenshots of the shell running in the VM are in the PR.

## 4. Boot splash
- [ ] Plymouth theme `anypc` (logo mark + subtle pulse, dark navy background) in
      `session/plymouth/`, installed and selected in the Containerfile.

Done when: the VM shows the AnyPC mark from power-on until the shell's own boot animation.

## 5. In-game quick menu
- [ ] Pressing the guide/Home button while a game runs shows the shell's quick menu
      over the game (gamescope overlay/focus switching), with Resume, Quit game,
      Screenshot, volume. Design reference: the "Meniu în joc" artboard.
- [ ] Screenshot saving to `~/Pictures/AnyPC/` (via gamescope or the compositor).

Done when: works in the VM with at least one native game.

## 6. Cover art for non-Steam games
- [ ] Use icons from the desktop entry today; add optional local covers in
      `~/.local/share/anypc/covers/<game-id>.(png|jpg|webp)` picked up by `/api/games/<id>/art`.
- [ ] Settings or game hub action "Choose cover" from files in that folder.

## 7. Emulators (legal only)
- [ ] Detect RetroArch / standalone emulators (already flagged as `source: "emulator"`).
- [ ] Optional ROM folders the user adds (`~/Games/ROMs/<system>/`), listed as games that
      launch through the matching emulator. User supplies their own files; nothing is bundled.

## 8. AnyPS5 module
- [ ] When the separate AnyPS5 project ships a release with a CLI, detect it
      (`/api/modules`) and list titles it can run, launched through it.
- [ ] Clear disclaimer in the UI; no firmware, keys or game files handled by AnyPC OS.

## 9. NVIDIA image variant
- [ ] Second Containerfile stage/tag with the NVIDIA driver from RPM Fusion (or the
      negativo17 repo), built in CI.

## 10. Polish
- [ ] Startup sound (short, original, CC0 or our own) with the existing setting.
- [ ] More languages (add to `i18n.js`; keep keys identical).
- [ ] Achievements of our own (per game play milestones) shown in the game hub.
- [ ] Hardware compatibility list in `docs/HARDWARE.md` from real tests.
