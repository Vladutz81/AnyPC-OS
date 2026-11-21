---
name: anypc-accessibility-i18n
description: "Asigura accesibilitate, limba romana, traduceri, fonturi si navigare controller in toate ecranele AnyPC OS."
---

# anypc-accessibility-i18n

**Domeniu:** Desktop
**Activează când:** La modificari in Installer, Desktop, Gaming Shell si OOBE.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Strange toate string-urile localizabile, fara concatenari fragile.
2. Testeaza ro_RO si en_US, diacritice, fallback font, navigare tastatura/controller.
3. Adauga contrast ridicat, reducere animatii, marime text scalabila si screen-reader hooks unde sunt posibile.
4. Pastreaza shortcuturi de iesire/recovery vizibile si utilizabile.

## Verificare de acceptare

- [ ] Testeaza 720p, 1080p, 4K si scale 125/150/200%, inclusiv text lung.
- [ ] Verifica lipsa stringurilor hardcodate si iconuri cu alternative text.

## Blocaje / lucruri interzise

- Nu suprascrie preferintele accessibility ale utilizatorului in update.
- Nu lega actiunile critice exclusiv de un controller specific.

## Livrabile

- `docs/ux/accessibility-i18n.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/KDE/plasma-workspace
- https://github.com/qt/qtdeclarative
