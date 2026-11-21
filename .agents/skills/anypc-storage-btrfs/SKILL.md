---
name: anypc-storage-btrfs
description: "Proiecteaza partitii Fedora, EFI, Btrfs, LUKS, mountpoints si protectia datelor la instalare."
---

# anypc-storage-btrfs

**Domeniu:** Storage
**Activează când:** La instalator, upgrade filesystem sau suport multiple discuri.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Inventariaza discuri si mountpoints read-only cu lsblk -f, findmnt si blkid.
2. Defineste schema instalare pentru EFI, /, /home si game library, cu UUID stable.
3. Diferentiaza snapshot de backup si protejeaza datele existente.
4. Testeaza boot cu LUKS, disc secundar si NVMe/SATA.

## Verificare de acceptare

- [ ] Testeaza partial failure si revenirea dupa restart.
- [ ] Verifica ca EFI a fost pastrata si /home nu a fost suprascris.

## Blocaje / lucruri interzise

- Nu rula mkfs, wipefs, dd ori parted destructive pe dispozitive reale fara acord si verificari separate.
- Nu presupune ca Btrfs este prezent doar fiindca exista btrfs-progs.

## Livrabile

- `docs/storage/partitioning-plan.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/kdave/btrfs-progs
- https://github.com/storaged-project/udisks
