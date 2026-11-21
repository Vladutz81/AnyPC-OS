---
name: anypc-game-library
description: "Creeaza biblioteca unica de jocuri cu scanare non-distructiva, metadata cache si profiluri de lansare."
---

# anypc-game-library

**Domeniu:** Gaming
**Activează când:** La schimbarea UI library, autodetectie jocuri ori covers.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Defineste schema joc/platforma/provenienta/versiune/adaptor/compatibilitate.
2. Indexeaza incremental si nu muta automat ROM-urile sau instalarile Steam.
3. Evita identificarea jocurilor dupa nume de fisier numai; foloseste hash si provider metadata cu acord.
4. Asigura deduplicare, import/export si migrare de schema sigura.

## Verificare de acceptare

- [ ] Testeaza path-uri Unicode, disc detasat, biblioteci mari si duplicate.
- [ ] Verifica ca lipsa internetului nu blocheaza jocurile deja instalate.

## Blocaje / lucruri interzise

- Nu descarca artwork nesigur sau copyrighted pentru redistribuire fara licenta.
- Nu sterge jocuri cand discul extern nu este montat.

## Livrabile

- `docs/library/indexer-contract.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/libretro/libretro-database
