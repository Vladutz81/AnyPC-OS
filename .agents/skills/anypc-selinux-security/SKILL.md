---
name: anypc-selinux-security
description: "Auditeaza SELinux, polkit si privilegiile daemonilor AnyPC OS fara dezactivarea protectiilor Fedora."
---

# anypc-selinux-security

**Domeniu:** Security
**Activează când:** Cand un serviciu AnyPC esueaza din cauza permisiunilor.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Verifica sestatus si ausearch/AVC fara alterarea politicii.
2. Construieste politica minima pentru serviciul identificat si separa actiunile privilegiate de UI.
3. Revizuieste API-uri D-Bus, polkit actions, path traversal si executia comenzilor.
4. Testeaza comportamentul cu SELinux enforcing in VM.

## Verificare de acceptare

- [ ] Nu exista AVC repetate neexplicate; audit pentru fisierele atinse.
- [ ] Asigura ca accesul la serviciile privilegiate necesita autorizare.

## Blocaje / lucruri interzise

- Nu folosi setenforce 0 sau permissive permanent ca solutie.
- Nu permite instalarea arbitrariei codului printr-un theme/skin/plugin.

## Livrabile

- `docs/security/selinux-policy.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/SELinuxProject/selinux
- https://github.com/polkit-org/polkit
