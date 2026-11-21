---
name: anypc-supply-chain
description: "Verifica provenienta surselor, licentele, semnaturile, SBOM si vulnerabilitatile tuturor componentelor OS."
---

# anypc-supply-chain

**Domeniu:** Security
**Activează când:** La integrarea unui nou proiect GitHub sau pregatirea unei versiuni stable.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Inregistreaza URL upstream, commit SHA/tag, licenta, autor, build system si dependente.
2. Evita HEAD nepinuit in buildurile release, verifica semnaturi si checksums unde exista.
3. Genereaza SBOM cu syft; scaneaza dependentele cu grype/trivy si revizuieste manual rezultatele.
4. Semneaza artefactele/release manifest cu cosign sau mecanismul de semnare ales.

## Verificare de acceptare

- [ ] Reproduce lista exacta de componente si versiuni dintr-un ISO.
- [ ] Blocheaza buildul in caz de dependente critice nejustificate sau integritate incerta.

## Blocaje / lucruri interzise

- Nu executa scripturi de instalare din skills ale tertilor fara audit.
- Nu include credențiale sau secrete in SBOM si loguri.

## Livrabile

- `docs/security/sbom-and-provenance.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/anchore/syft
- https://github.com/sigstore/cosign
