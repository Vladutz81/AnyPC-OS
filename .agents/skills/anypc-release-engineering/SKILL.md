---
name: anypc-release-engineering
description: "Publica versiuni AnyPC OS cu versionare, semnaturi, checksum, changelog si rollout controlat."
---

# anypc-release-engineering

**Domeniu:** Release
**Activează când:** Inainte de alpha, beta, stable sau hotfix.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Defineste tag git, semver/versiune OS si manifest de artefacte.
2. Pin-uieste commit SHA-uri upstream, produce ISO si SBOM din build reproductibil.
3. Ruleaza security scan, iso VM test, smoke test GPU si rollout pe canale.
4. Publica release notes cu limitari si ce componente experimentale raman dezactivate.

## Verificare de acceptare

- [ ] Rebuild produce aceleasi manifest si versiuni, iar checksum-urile sunt publicate.
- [ ] Rollback testat si linkuri de recuperare in release notes.

## Blocaje / lucruri interzise

- Nu publica in stable daca instalarea sau reboot esueaza.
- Nu semna si publica builduri cu secrete in git.

## Livrabile

- `docs/releases/release-checklist.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/sigstore/cosign
- https://github.com/anchore/syft
