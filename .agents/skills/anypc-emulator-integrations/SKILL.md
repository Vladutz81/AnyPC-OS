---
name: anypc-emulator-integrations
description: "Integreaza emulatoarele PlayStation, Xbox, Nintendo si retro cu profile per joc si BIOS gestionat legal."
---

# anypc-emulator-integrations

**Domeniu:** Gaming
**Activează când:** Cand sunt adaugate emulatoare, scanarea jocurilor ori profiluri de launch.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Citeste lista din inventory si identifica API-ul CLI si suportul OS pentru fiecare emulator.
2. Construieste adaptoare per motor, independent de UI, cu versionare si eroare explicita cand lipseste un firmware.
3. Foloseste paths standardizate XDG, sandbox unde este posibil si metadata de licenta.
4. Salveaza setari si profile per joc fara a corupe folderele ROM.

## Verificare de acceptare

- [ ] Testeaza launch/close cu fisiere de test redistribuibile sau jocuri proprii legal obtinute.
- [ ] Diferentiaza functional, boots, ingame, playable, unsupported in matrice.

## Blocaje / lucruri interzise

- Nu include jocuri comerciale, chei, firmware sau BIOS proprietar in ISO.
- Nu presupune ca orice repo experimental este emulabil pe Linux.

## Livrabile

- `docs/games/emulators-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/libretro/RetroArch
- https://github.com/xemu-project/xemu
