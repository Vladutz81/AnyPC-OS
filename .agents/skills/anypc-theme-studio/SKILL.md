---
name: anypc-theme-studio
description: "Construieste centrul de personalizare AnyPC OS pentru boot, Plymouth, SDDM, Plasma, sunete si gaming shell."
---

# anypc-theme-studio

**Domeniu:** Desktop
**Activează când:** Cand se implementeaza aplicatia AnyPC Theme Studio.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Defineste format versionat pentru teme cu identificator unic, compatibilitate si licenta.
2. Separat preview de apply; arata ce resurse necesita drepturi de administrator.
3. Aplica atomic si pastreaza configuratia precedenta pentru reversibilitate.
4. Integreaza export/import teme, detectarea resurselor lipsa si resetare la tema implicita.

## Verificare de acceptare

- [ ] Testeaza teme invalide, assets lipsa, fallback si resetare.
- [ ] Verifica accesibilitatea si animatii reduse la cerere.

## Blocaje / lucruri interzise

- Nu acorda drept de root intregii aplicatii QML/Qt.
- Nu accepta teme care ruleaza cod arbitrar in fluxul boot.

## Livrabile

- `docs/themes/theme-format.md si docs/themes/testcases.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/tsujan/Kvantum
- https://github.com/KDE/plasma-sdk
