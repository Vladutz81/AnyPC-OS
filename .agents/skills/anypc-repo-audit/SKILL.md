---
name: anypc-repo-audit
description: "Auditeaza repository-ul AnyPC OS, componentele instalate si inventarul upstream inainte de orice implementare."
---

# anypc-repo-audit

**Domeniu:** Foundation
**Activează când:** Inainte de schimbari ample, integrare repo sau investigarea stadiului proiectului.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Localizeaza sursa OS, manifestele de build, branchul si directorul de artefacte; nu presupune cai din alte conversatii.
2. Ruleaza git status --short, git remote -v, git log -5 --oneline si identifica comenzi de build documentate.
3. Citeste manifestul repository-inventory.json, compara cu pachetele reale si marcheaza fiecare element: source-only, packaged, enabled, tested, unsupported.
4. Construieste o matrice de dependente si conflicte intre alternative (bootc/DNF, TLP/TuneD, GRUB/systemd-boot, Steam/compatibility runtime).

## Verificare de acceptare

- [ ] Pastreaza statusul git initial si final, plus inventarul hardware si pachetele OS inainte de a modifica ceva.
- [ ] Confirma separat existenta fisierelor, compilarea, integrarea in ISO si rularea functionala; acestea nu sunt echivalente.

## Blocaje / lucruri interzise

- Nu presupune ca simpla includere a URL-ului GitHub inseamna instalare sau compatibilitate.
- Nu descarca si nu executa scripturi ale repository-urilor fara revizuire.

## Livrabile

- `docs/audits/anypc-inventory.md, docs/audits/compatibility-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/agentskills/agentskills
