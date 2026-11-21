---
name: anypc-performance-thermal
description: "Optimizeaza FPS, frametime, CPU/GPU si politici termice pe profile hardware reproductibile."
---

# anypc-performance-thermal

**Domeniu:** Performance
**Activează când:** Cand exista stutter, latenta, throttling sau regresii de performanta.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Masoara baseline cu aceeasi scena, rezolutie, driver si profil de energie.
2. Foloseste MangoHud si instrumente de senzori inregistrand min/median/p95 frametime.
3. Compara GameMode si TuneD fara a lansa manageri energetici conflictuali.
4. Testeaza cooler, alimentare AC/baterie, noise si temperaturi in sarcina.

## Verificare de acceptare

- [ ] Raporteaza median/p95 frametime si temperaturi pentru fiecare profil.
- [ ] Revine la profil sigur daca monitorizarea detecteaza degradare.

## Blocaje / lucruri interzise

- Nu face overclock/undervolt automat pe hardware necunoscut.
- Nu ascunde throttling prin grafice FPS medii numai.

## Livrabile

- `docs/performance/benchmark-report.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/flightlessmango/MangoHud
- https://github.com/FeralInteractive/gamemode
