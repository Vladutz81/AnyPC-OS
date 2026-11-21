---
name: anypc-boot-branding
description: "Implementeaza identitatea AnyPC OS pentru GRUB, Plymouth si splash-ul de pornire, cu fallback functional."
---

# anypc-boot-branding

**Domeniu:** Boot
**Activează când:** La modificari de logo, meniu boot, progres si teme grafice.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Confirma tehnologia boot existenta si rezolutia disponibila in etapa pre-GPU.
2. Construieste tema GRUB si tema Plymouth in directoare separate cu licente clare pentru fonturi/assets.
3. Adauga fallback text daca randarea grafica nu porneste.
4. Testeaza teme si tranzitia spre display manager in OVMF/QEMU si pe hardware.

## Verificare de acceptare

- [ ] Verifica vizibilitatea erorilor de boot si accesibilitatea optiunilor de recovery.
- [ ] Masoara degradarea timpului de boot fata de baseline.

## Blocaje / lucruri interzise

- Nu ascunde toate mesajele de eroare fara o cale de diagnostic.
- Nu modifica firmware splash al producatorului prin flash BIOS.

## Livrabile

- `branding/boot si docs/boot/theme-test.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/dracutdevs/dracut
- https://github.com/rhboot/grub2
