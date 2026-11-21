---
name: anypc-backup-recovery
description: "Implementeaza backup, snapshot, rollback si mod de recuperare pentru AnyPC OS."
---

# anypc-backup-recovery

**Domeniu:** Storage
**Activează când:** La schimbari de update, recovery menu sau administrarea salvarilor.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Clarifica tipurile de date: sistem, home, save-games, configuratii si chei.
2. Alege snapshot Btrfs/Snapper doar daca filesystemul il suporta; foloseste backup separat pentru date.
3. Realizeaza backup incremental cu retentie, criptare si restaurare testata.
4. Adauga traseu de rescue bootabil pentru driver defect sau update esuat.

## Verificare de acceptare

- [ ] Testeaza restaurarea intr-o VM curata si verificarea integritatii.
- [ ] Verifica rollback pentru fiecare tip de update: RPM versus image-based.

## Blocaje / lucruri interzise

- Nu creeaza snapshoturi pe un filesystem incompatibil.
- Nu sterge ultimele backupuri functionale inainte de validare.

## Livrabile

- `docs/recovery/restore-drill.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/openSUSE/snapper
- https://github.com/restic/restic
