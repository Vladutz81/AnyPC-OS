# Roadmap

## M0 — Foundations
- [x] Name, repo, GPL-3.0 license, legal notes
- [x] Logo and boot animation
- [x] Shell design (8 screens)

## M1 — Working shell (in progress)
- [x] Shell service: game discovery (native, Flatpak, Steam), launch, play time,
      audio, network, power, users, settings
- [x] Shell UI: boot animation, who's playing, first-time setup, home, library,
      game hub, control center, settings
- [x] Gamepad, keyboard and mouse navigation; English and Romanian
- [x] Session scripts (greetd → gamescope → shell)
- [x] Containerfile on Fedora bootc
- [x] First successful image build and boot in a VM
- [x] CI: run the shell checks on pushes and pull requests
- [x] CI: build the bootable image

## M2 — Real hardware
- [x] Boot splash (Plymouth theme with the AnyPC mark)
- [x] Wi-Fi connection from Settings (network list + on-screen keyboard)
- [x] Bluetooth pairing from Settings
- [x] Full settings: display, sound output, date & time, device name, storage,
      users, power, updates with rollback, controller test
- [ ] In-game quick menu over the running game (gamescope overlay)
- [ ] NVIDIA image variant
- [ ] Test on several PCs; hardware compatibility list

## M3 — Compatibility modules
- [ ] Emulator integration (legal emulators only, user-supplied files)
- [x] Optional library integration for exported AnyPS5 Linux applications
- [ ] Cover art for non-Steam games

## M4 — Polish
- [ ] Achievements of our own, themes, more languages
- [ ] Remote play / streaming
- [ ] Documentation site

## Console delivery

- [x] Bilingual graphical installer with explicit disk confirmation.
- [x] Curated AnyPC Store, per-user app installation and Steam storefront entry.
- [x] Original startup and navigation sounds with independent switches.
- [x] Offline import of compatible unencrypted homebrew through the AnyPS5 runtime.
- [ ] Validate real GPUs, HDMI audio, wireless controllers and suspend on physical PCs.
