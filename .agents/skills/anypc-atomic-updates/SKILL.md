---
name: anypc-atomic-updates
description: "Planifica si testeaza actualizari atomice bootc sau rpm-ostree, inclusiv rollback verificat."
---

# anypc-atomic-updates

**Domeniu:** Build
**Activează când:** Doar pentru variantele AnyPC image-based deja confirmate.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica mecanismul existent; nu combina bootc si rpm-ostree fara un design explicit.
2. Defineste canalele stable/beta, semnarea imaginilor, reproducerea versiunilor si pastrarea datelor utilizatorului.
3. Construieste update intr-un mediu de test cu versiune anterioara disponibila.
4. Valideaza upgrade plus rollback la imaginea anterior functionala.

## Verificare de acceptare

- [ ] Demonstreaza restart curat dupa upgrade, apoi rollback complet in VM.
- [ ] Verifica persistenta profilurilor, jocurilor si a salvarilor.

## Blocaje / lucruri interzise

- Nu converti instalatii in productie fara migrare si backup testat.
- Nu stoca date de utilizator in straturi read-only ale imaginii.

## Livrabile

- `docs/updates/atomic-update-test.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/bootc-dev/bootc
- https://github.com/coreos/rpm-ostree
