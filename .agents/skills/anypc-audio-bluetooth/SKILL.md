---
name: anypc-audio-bluetooth
description: "Stabilizeaza audio PipeWire, WirePlumber, ALSA si Bluetooth pentru Gaming Mode si Desktop Mode."
---

# anypc-audio-bluetooth

**Domeniu:** Hardware
**Activează când:** La lipsa sunet, microfon, Bluetooth sau schimbari HDMI.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica sink/source, session manager si dispozitivele enumerate de wpctl, pactl si bluetoothctl.
2. Test HDMI, USB, Bluetooth, mute si routing per aplicatie.
3. Configureaza politici de revenire la dispozitivul anterior dupa suspend/hotplug.
4. Asigura nivele de volum sigure si persistenta per utilizator.

## Verificare de acceptare

- [ ] Testeaza redare + microfon, schimbare HDMI si reconnect Bluetooth.
- [ ] Verifica logurile PipeWire/WirePlumber si restartul neintruziv al sesiunii.

## Blocaje / lucruri interzise

- Nu inlocui daemonul audio existent cu altul paralel fara migratie.
- Nu activa pairing permanent discoverable implicit.

## Livrabile

- `docs/audio/device-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/PipeWire/pipewire
- https://github.com/PipeWire/wireplumber
