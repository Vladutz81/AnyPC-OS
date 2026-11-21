---
name: anypc-anaconda-installer
description: "Personalizeaza Anaconda si WebUI pentru instalarea AnyPC OS, cu partitionare sigura si first-boot controlat."
---

# anypc-anaconda-installer

**Domeniu:** Installer
**Activează când:** Cand se schimba fluxul instalarii grafice sau automatizarile Kickstart.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Verifica versiunea Anaconda/WebUI potrivita versiunii Fedora si API-urile personalizabile.
2. Proiecteaza ecrane branded pentru limba, disc, criptare, utilizator si confirmare finala.
3. Pastreaza partitia EFI existenta si adauga o verificare vizibila inainte de operatii destructive.
4. Testeaza modurile UEFI si firmware virtualizat, online si offline.

## Verificare de acceptare

- [ ] Testeaza instalarea pe disc gol si disc cu alte partiții in VM; datele existente trebuie identificate corect.
- [ ] Valideaza prezenta installer-logs, Kickstart sanitizat si primul boot.

## Blocaje / lucruri interzise

- Nu formata implicit alt disc si nu ascunde confirmarea stergerii datelor.
- Nu modifica logica de partitionare prin imitarea butoanelor UI; foloseste API-ul instalatorului.

## Livrabile

- `docs/installer/installation-test-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/rhinstaller/anaconda
- https://github.com/rhinstaller/anaconda-webui
