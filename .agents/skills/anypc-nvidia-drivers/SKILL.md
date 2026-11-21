---
name: anypc-nvidia-drivers
description: "Integreaza NVIDIA in Fedora cu kernel modules, Wayland, Secure Boot si recovery pentru GPU-uri suportate."
---

# anypc-nvidia-drivers

**Domeniu:** Graphics
**Activează când:** Cand se lucreaza cu GPU NVIDIA sau cu regresii dupa actualizare.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Determina modelul GPU, versiunile kernelului si suportul driverului inclusiv legacy.
2. Alege pachetele oficiale/distributie pentru driver plus biblioteci user-space si multilib.
3. Valideaza potrivirea dintre module kernel si user-space si semnarea MOK daca este ceruta.
4. Testeaza Wayland, suspend/restart, video decoding si joc Vulkan.

## Verificare de acceptare

- [ ] Rapoarte nvidia-smi doar daca driverul suporta; pentru altfel jurnal kernel.
- [ ] Testeaza revenirea la driverul anterior daca modulul nou nu porneste.

## Blocaje / lucruri interzise

- Nu instala open-gpu-kernel-modules pe placi nesuportate si nu considera modulele un driver complet.
- Nu dezactiva Secure Boot pentru a masca semnaturi lipsa.

## Livrabile

- `docs/graphics/nvidia-compat.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/NVIDIA/open-gpu-kernel-modules
- https://github.com/NVIDIA/nvidia-settings
