---
name: anypc-rpm-packaging
description: "Creeaza si auditeaza pachete RPM Fedora pentru servicii si aplicatii AnyPC OS, cu SPEC si depedente reproductibile."
---

# anypc-rpm-packaging

**Domeniu:** Build
**Activează când:** Cand o componenta AnyPC trebuie livrata ca RPM in imagine.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Alege pachete din distro mai intai; creeaza RPM numai daca este justificat.
2. Scrie SPEC complet: Name, Version, Release, License, Source, BuildRequires, Requires, %build, %install, %files, %check.
3. Foloseste build izolat cu mock, utilizator neprivilegiat si versiuni pin-uite.
4. Testeaza upgrade, downgrade permis si uninstall intr-o VM separata.

## Verificare de acceptare

- [ ] rpmlint si rpm -qp --requires pe artefacte.
- [ ] Testeaza instalare/upgrade cu dnf5 --assumeno inainte de operatii privilegiate.

## Blocaje / lucruri interzise

- Nu folosi curl | bash in scriptlet RPM si nu scrie chei/secrete in pachet.
- Nu copia directoare intregi din surse fara verificarea licentelor.

## Livrabile

- `packaging/specs si docs/build/rpm-report.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/rpm-software-management/mock
- https://rpm-software-management.github.io/rpm/
