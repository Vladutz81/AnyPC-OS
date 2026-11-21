---
name: anypc-initramfs
description: "Construieste si testeaza initramfs Dracut pentru suport GPU, disc, criptare si pornire fiabila."
---

# anypc-initramfs

**Domeniu:** Boot
**Activează când:** La schimbari de kernel, module, drivere sau device discovery in early boot.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica hostonly/generic si sistemele de fisiere necesare ISO-ului.
2. Verifica modulele rootfs, LUKS, NVMe, USB, DRM simpledrm si instrumentele rescue.
3. Creeaza initramfs pentru noua versiune fara a sterge imaginea precedenta.
4. Valideaza includerea modulelor prin lsinitrd, apoi pornirea in VM.

## Verificare de acceptare

- [ ] Testeaza boot fara placa NVIDIA si cu root criptat unde este suportat.
- [ ] Pastreaza boot entry pentru kernelul anterior.

## Blocaje / lucruri interzise

- Nu rula dracut --force pe singura imagine bootabila fara snapshot si recovery.
- Nu include secrete LUKS sau chei de decriptare in imagini publice.

## Livrabile

- `docs/boot/initramfs-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/dracutdevs/dracut
