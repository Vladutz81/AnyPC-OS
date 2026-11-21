---
name: anypc-gamescope-session
description: "Configureaza sesiune consola Gamescope + OpenGamepadUI cu fallback sigur spre Desktop Mode."
---

# anypc-gamescope-session

**Domeniu:** Gaming
**Activează când:** La pornirea automata in Gaming Mode ori probleme cu sesiunea full-screen.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Studiaza implementarea in uz pentru Gamescope Session si OpenGamepadUI.
2. Creeaza un target systemd de sesiune cu loguri, signal handling si lifecycle curat.
3. Permite alegerea Gaming/Desktop/Recovery din login; nu bloca utilizatorul in gaming shell.
4. Gestioneaza controller first, window focus, overlay si suspend/resume.

## Verificare de acceptare

- [ ] Testeaza sesiune fara controller, fara GPU performant si cu renderer fallback.
- [ ] Verifica iesirea la Desktop Mode si recuperarea dupa crashul launcherului.

## Blocaje / lucruri interzise

- Nu inlocui managerul SDDM fara testare.
- Nu porni compositor in loop infinit dupa crash repetat.

## Livrabile

- `docs/gaming/session-test.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/ValveSoftware/gamescope
- https://github.com/ChimeraOS/gamescope-session
