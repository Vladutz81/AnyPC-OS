---
name: anypc-systemd-reliability
description: "Creeaza servicii systemd fiabile, cu restart controlat, hardening, dependente si jurnalizare."
---

# anypc-systemd-reliability

**Domeniu:** Foundation
**Activează când:** La adaugarea daemonilor AnyPC pentru gaming, driver manager si actualizari.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Defineste unit files cu After/Wants/Requires doar unde sunt justificate.
2. Foloseste DynamicUser sau utilizatori dedicati, protectii ProtectSystem, NoNewPrivileges si RestrictAddressFamilies dupa necesitati.
3. Planifica health checks, backoff, rate limit si shutdown curat.
4. Ruleaza systemd-analyze verify pe fiecare unitate.

## Verificare de acceptare

- [ ] Testeaza pornire, restart, fail recovery si stop intr-o VM.
- [ ] Verifica journalctl -u pentru mesaje fara secrete.

## Blocaje / lucruri interzise

- Nu rula servicii grafice privilegiate ca root daca nu este necesar.
- Nu executa automat scripturi arbitrare din internet prin systemd.

## Livrabile

- `systemd/ si docs/services/reliability.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/systemd/systemd
