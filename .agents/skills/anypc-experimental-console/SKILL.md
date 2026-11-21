---
name: anypc-experimental-console
description: "Evalueaza experimental AnyPS5, shadPS4, WinDurango, GDKScarlett si limitari Linux vs Windows."
---

# anypc-experimental-console

**Domeniu:** Gaming
**Activează când:** Cand se cerceteaza compatibilitatea PS4/PS5 sau Xbox One/Series.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Citeste compatibilitatea upstream si cerintele platformei pentru versiunea exacta.
2. Clasifica fiecare proiect ca emulator, recompiler, relinker sau translation layer.
3. Pune proiectele Windows-only intr-un laborator Windows separat; nu le proclama compatibile Proton fara teste.
4. Scrie fisa de maturitate si afiseaza avertisment experimental in UI AnyPC.

## Verificare de acceptare

- [ ] Documenteaza exemplar testat, versiunea jocului, rezultatul si logurile.
- [ ] Nu marca proiectul suportat numai fiindca se compileaza.

## Blocaje / lucruri interzise

- Nu extrage chei, nu ocoli DRM si nu distribui executabile de joc protejate fara drept.
- Nu activa pluginurile experimentale by default in build stable.

## Livrabile

- `docs/games/experimental-console-research.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/boykopovar/AnyPS5
- https://github.com/WinDurango/WinDurango
- https://github.com/Ender-0001/GDKScarlett
