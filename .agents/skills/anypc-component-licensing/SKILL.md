---
name: anypc-component-licensing
description: "Verifica licente, drepturi de redistribuire, sursa firmware, codecuri si dependentele non-free ale AnyPC OS."
---

# anypc-component-licensing

**Domeniu:** Security
**Activează când:** Inainte de integrarea unui ROM, emulator, firmware, codec, driver sau tema.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Citeste LICENSE si NOTICE la commit/tag exact si identifica obligatii pentru binary/source.
2. Separat redistributable FOSS de firmware proprietar, BIOS, jocuri, codecuri si drivere NVIDIA.
3. Documenteaza licenta assets, fonturi, pictograme si obligatia de attribution.
4. Pentru incompatibilitati, integreaza instalare optionala de la utilizator din sursa autorizata.

## Verificare de acceptare

- [ ] Verifica generarea unui third-party notices pentru ISO si toate pachetele.
- [ ] Testeaza distributia imaginii fara chei/jocuri/BIOS protejate.

## Blocaje / lucruri interzise

- Nu presupune ca un repo public confera drepturi de redistribuire.
- Nu ocoli DRM sau extrage chei din jocuri pe care utilizatorul nu le detine.

## Livrabile

- `docs/legal/third-party-notices.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://spdx.org/licenses/
