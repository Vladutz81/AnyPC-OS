---
name: anypc-iso-qemu-testing
description: "Testeaza instalarea ISO AnyPC OS in QEMU+OVMF cu matrice UEFI, stocare, retea si boot."
---

# anypc-iso-qemu-testing

**Domeniu:** QA
**Activează când:** Inainte de orice release sau schimbare boot/installer.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Creeaza VM cu OVMF si disc qcow2 neimportant, izolat de stocarea host.
2. Testeaza Live mode, instalare grafica, reboot, user nou si Game/Desktop Mode.
3. Ruleaza scenarii Secure Boot off/on in configuratii separate si salvare rapoarte.
4. Automatizeaza fluxul cu openQA sau test harness existent, fara a simula succes.

## Verificare de acceptare

- [ ] Salveaza loguri, capturi reale, checksum ISO si versiuni testate.
- [ ] Testeaza recovery boot si downgrade dupa update invalid.

## Blocaje / lucruri interzise

- Nu monta niciodata un block device real ca target VM in testele automate.
- Nu confunda boot in VM cu validarea driverelor fizice.

## Livrabile

- `tests/iso/ si docs/qa/qemu-results.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/qemu/qemu
- https://github.com/tianocore/edk2
- https://github.com/os-autoinst/openQA
