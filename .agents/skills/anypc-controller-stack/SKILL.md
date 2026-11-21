---
name: anypc-controller-stack
description: "Integreaza gamepaduri Xbox, DualSense, HID, handheld si remapari fara conflicte intre drivere."
---

# anypc-controller-stack

**Domeniu:** Hardware
**Activează când:** La suport controller sau mapping in Gamescope/desktop.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Inventariaza hidraw, evdev, SDL si drivere kernel deja active.
2. Selecteaza InputPlumber sau alt adaptor doar unde este nevoie.
3. Testeaza USB, Bluetooth, deconectare, reconectare, haptics si deadzone.
4. Permite profiluri salvate per joc si revenire la mapping implicit.

## Verificare de acceptare

- [ ] Testeaza meniu complet din gamepad, inclusiv setup initial si shutdown.
- [ ] Asigura ca un driver experimental nu intercepteaza inputul tastaturii.

## Blocaje / lucruri interzise

- Nu instaleaza xone/xpadneo peste dispozitive pentru care driverul nativ functioneaza.
- Nu ridica permisiuni hidraw globale pentru toti utilizatorii.

## Livrabile

- `docs/input/controller-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/ShadowBlip/InputPlumber
- https://github.com/libsdl-org/SDL
