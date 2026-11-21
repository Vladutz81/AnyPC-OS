---
name: anypc-iso-builder
description: "Construieste imaginea Live/Install ISO AnyPC OS reproductibil cu branding si metadate verificabile."
---

# anypc-iso-builder

**Domeniu:** Installer
**Activează când:** Cand se modifica instalatorul, imaginea ISO sau manifestele.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica pipeline-ul real Lorax/Anaconda/OSBuild; nu suprapune trei generatoare.
2. Noteaza build dependencies, surse de pachete, arhitectura, tag git si checksum.
3. Construieste ISO dintr-un branch curat, in container/VM izolata.
4. Creeaza manifest pachete, SHA256 si raportul SBOM in acelasi build.

## Verificare de acceptare

- [ ] Verifica sha256sum pentru ISO si demararea lui in OVMF/QEMU.
- [ ] Testeaza mod Live, instalare, boot dupa instalare si imaginea semnata cand este cazul.

## Blocaje / lucruri interzise

- Nu suprascrie ISO-ul stable inainte de testare.
- Nu incorpora ROM-uri, BIOS-uri sau firmware proprietar fara drepturi de redistribuire.

## Livrabile

- `dist/ISO, dist/SHA256SUMS, docs/releases/iso-validation.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/weldr/lorax
- https://github.com/osbuild/osbuild
