---
name: anypc-hardware-discovery
description: "Detecteaza in siguranta CPU, GPU, stocare, audio si controllerele si alege profilurile AnyPC OS."
---

# anypc-hardware-discovery

**Domeniu:** Hardware
**Activează când:** In instalator, la prima pornire si cand se schimba hardware-ul.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Colecteaza lspci -nnk, lsusb, lsblk -o NAME,TYPE,MODEL,SIZE,FSTYPE, uname -r si modinfo numai citire.
2. Coreleaza PCI ID, firmware necesar si driverul in uz cu o baza versionata.
3. Genereaza recomandari dependente de versiunea kernelului si distro, nu de brand singur.
4. Pastreaza un fallback care porneste desktopul cu driverul generic.

## Verificare de acceptare

- [ ] Testeaza configuratii AMD/Intel/NVIDIA si hardware necunoscut.
- [ ] Nu afirma suport fara validarea combinatiei GPU + kernel + sesiune Wayland.

## Blocaje / lucruri interzise

- Nu expune seriale, MAC-uri sau identificatori personali in raport public.
- Nu schimba automat driverul daca sesiunea curenta functioneaza.

## Livrabile

- `docs/hardware/detection-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/KhronosGroup/Vulkan-Tools
