---
name: anypc-firstboot-oobe
description: "Proiecteaza experienta de prima pornire AnyPC OS: cont local, wifi, controller, limba si profil de gaming."
---

# anypc-firstboot-oobe

**Domeniu:** Installer
**Activează când:** La schimbarea onboarding-ului dupa instalare.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica daca exista firstboot Fedora, Plasma Welcome sau serviciu AnyPC.
2. Proiecteaza OOBE idempotent si salvarea starii per utilizator.
3. Configureaza optional reteaua, controllerul, profilul GPU si setarile regionale.
4. Permite skip si mod offline fara blocarea accesului la desktop.

## Verificare de acceptare

- [ ] Testeaza OOBE la user nou, la rerulare si dupa update.
- [ ] Verifica ca parolele si tokenurile nu sunt salvate in loguri.

## Blocaje / lucruri interzise

- Nu forta autentificare online pentru pornirea OS-ului.
- Nu porni servicii de telemetrie fara acord explicit.

## Livrabile

- `docs/oobe/firstboot-flow.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/KDE/plasma-welcome
