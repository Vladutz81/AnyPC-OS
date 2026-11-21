---
name: anypc-fedora-foundation
description: "Verifica baza Fedora Linux a AnyPC OS si compatibilitatea kernel, rpm, arhitectura si tipul imaginii."
---

# anypc-fedora-foundation

**Domeniu:** Foundation
**Activează când:** La actualizarea distributiei sau proiectarea unei schimbari structurale.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica /etc/os-release, uname -a, rpm -q kernel-core, mount, lsblk -f si managerul de pachete real.
2. Stabileste daca sistemul este Fedora RPM/DNF, ostree/rpm-ostree sau bootc; documenteaza probele.
3. Noteaza versiunea kernelului, arhitectura, filesystem-ul si componenta care produce ISO-ul.
4. Mapeaza sursele Fedora, COPR si eventualele repo-uri externe cu pinning si provenienta.

## Verificare de acceptare

- [ ] Verifica instalarea pe VM de test si rezolvarea dependentelor in modul dry-run.
- [ ] Confirma disponibilitatea versiunilor x86_64 si, unde trebuie, a bibliotecilor i686.

## Blocaje / lucruri interzise

- Nu converti automat Fedora clasic in bootc sau invers.
- Evita actualizari cross-release si inlocuirea kernelului fara plan de rollback.

## Livrabile

- `docs/foundation/fedora-baseline.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://docs.fedoraproject.org/
- https://github.com/rpm-software-management/dnf5
