---
name: anypc-amd-intel-gpu
description: "Testeaza driverele AMD/Intel Mesa, accelerarea media si GPU hybrid fara configurari fragile."
---

# anypc-amd-intel-gpu

**Domeniu:** Graphics
**Activează când:** Cand AnyPC OS ruleaza pe iGPU AMD/Intel ori dGPU AMD.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Verifica chipset, kerneldriver (amdgpu/i915/xe dupa versiune) si firmware.
2. Valideaza RADV/ANV si VA-API sau alt backend suportat prin mediul Fedora.
3. Testeaza sistemele cu GPU integrat plus dedicat si preferintele per joc.
4. Documenteaza limitari HDR/VRR/codec per generatie si display.

## Verificare de acceptare

- [ ] Testeaza redare hardware video si joc Vulkan fara software rasterizer.
- [ ] Verifica persistenta setarilor dupa suspend/resume.

## Blocaje / lucruri interzise

- Nu forteaza module experimental xe/amdgpu pe hardware necunoscut.
- Nu schimba parametrii kernel global pe baza unui singur laptop.

## Livrabile

- `docs/graphics/amd-intel-test.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://gitlab.freedesktop.org/mesa/mesa
- https://github.com/intel/media-driver
