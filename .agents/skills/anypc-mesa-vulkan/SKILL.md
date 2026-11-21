---
name: anypc-mesa-vulkan
description: "Verifica Mesa, Vulkan, OpenGL, RADV/ANV si bibliotecile multilib pentru compatibilitatea jocurilor."
---

# anypc-mesa-vulkan

**Domeniu:** Graphics
**Activează când:** Cand jocurile nu au accelerare 3D sau necesita API-uri grafice.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica GPU si driverul in uz prin lspci -k si instrumente grafice.
2. Verifica versiunea Vulkan cu vulkaninfo --summary, OpenGL si disponibilitatea ICD-urilor.
3. Testeaza x86_64 plus i686 pentru Wine/Proton, fara instalare de drivere conflictuale.
4. Documenteaza rendererul Gamescope/Mesa ales pentru fiecare GPU.

## Verificare de acceptare

- [ ] Testeaza jocul sample/benchmark si capturi de log Vulkan ICD.
- [ ] Compara FPS si frametime cu baseline pe acelasi GPU si setari.

## Blocaje / lucruri interzise

- Nu copia biblioteci grafice manual in /usr/lib* din builduri necunoscute.
- Nu confunda vulkan-tools cu implementarea driverului GPU.

## Livrabile

- `docs/graphics/vulkan-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://gitlab.freedesktop.org/mesa/mesa
- https://github.com/KhronosGroup/Vulkan-Tools
