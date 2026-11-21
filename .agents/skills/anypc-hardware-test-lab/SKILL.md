---
name: anypc-hardware-test-lab
description: "Construieste matrice de test real pentru AMD, NVIDIA, Intel, laptopuri, desktopuri, monitoare si controllere."
---

# anypc-hardware-test-lab

**Domeniu:** QA
**Activează când:** La testare release pe hardware real.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Defineste dispozitive martor cu GPU/vendor ID, UEFI, Secure Boot, stocare si firmware.
2. Testeaza instalare, suspend/resume, BIOS settings, gaming, HDR si audio/video.
3. Capturi de log curate si raport de regresii pentru fiecare build.
4. Marcheaza unsupported/untested separat de passed.

## Verificare de acceptare

- [ ] Cere dovezi reale pentru fiecare afirmatie de compatibilitate.
- [ ] Pastreaza un plan de reimaging si backup la test pe hardware real.

## Blocaje / lucruri interzise

- Nu rula modificari de partiții reale fara acord explicit si verificarea discului.
- Nu face flash de BIOS sau firmware in fluxul obisnuit de QA.

## Livrabile

- `docs/qa/hardware-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/KhronosGroup/Vulkan-Tools
