---
name: anypc-uefi-secure-boot
description: "Auditeaza lantul UEFI Secure Boot, shim, GRUB si semnarea imaginilor fara a compromite pornirea sistemului."
---

# anypc-uefi-secure-boot

**Domeniu:** Boot
**Activează când:** La modificari EFI, bootloader, MOK sau pachete kernel.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Inventariaza EFI, mokutil --sb-state cand exista si efibootmgr -v in regim doar citire.
2. Construieste diagrama boot-chain si lista de artefacte semnate.
3. Verifica semnaturile si compatibilitatea cu modulele GPU, initramfs si firmware.
4. Testeaza boot cu Secure Boot activ si inactiv in VM dedicata.

## Verificare de acceptare

- [ ] Valideaza ca bootloaderul poate reveni la versiunea anterioara.
- [ ] Pastreaza intrarea EFI originala inainte de adaugarea unei noi intrari.

## Blocaje / lucruri interzise

- Nu sterge chei UEFI/MOK, nu face resetare TPM si nu dezactiva Secure Boot implicit.
- Nu aplica comenzi efibootmgr care schimba BootOrder fara acord si plan de recuperare.

## Livrabile

- `docs/boot/uefi-secure-boot.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/rhboot/shim
- https://github.com/rhboot/grub2
