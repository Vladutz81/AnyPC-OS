---
name: anypc-display-wayland
description: "Integreaza KWin Wayland, Gamescope, HDR, VRR si multi-monitor cu fallback robust."
---

# anypc-display-wayland

**Domeniu:** Graphics
**Activează când:** Cand apare black screen, tearing, refresh gresit sau HDR.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Inventariaza compositorul, sesiunea Wayland, EDID, rezolutii si moduri refresh.
2. Testeaza gamescope separat de desktop Plasma si evita doua compositoare exclusive simultane.
3. Configureaza HDR/VRR numai pentru hardware, monitor si driver compatibile.
4. Pastreaza setare de recuperare pentru 60 Hz si rezolutie safe.

## Verificare de acceptare

- [ ] Testeaza cold boot, hotplug HDMI/DP, suspend/resume si multi-monitor.
- [ ] Verifica output modes si capturi de log din sesiune.

## Blocaje / lucruri interzise

- Nu promite HDR universal, inclusiv pe GPU-uri care nu-l suporta.
- Nu suprascrie configuratiile display existente fara backup.

## Livrabile

- `docs/graphics/display-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/KDE/kwin
- https://github.com/ValveSoftware/gamescope
