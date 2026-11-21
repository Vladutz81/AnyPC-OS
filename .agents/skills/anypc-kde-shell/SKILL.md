---
name: anypc-kde-shell
description: "Personalizeaza KDE Plasma, SDDM si aplicatiile Qt/QML pentru AnyPC OS fara a distruge Desktop Mode."
---

# anypc-kde-shell

**Domeniu:** Desktop
**Activează când:** Cand se modifica ecranul login, taskbar, setari, desktop sau widgeturi.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica versiunile KDE Plasma si Qt si configuratiile SDDM curente.
2. Pastreaza temele AnyPC intr-un pachet separat, cu instalare si dezinstalare.
3. Respecta XDG base dirs, Wayland, accesibilitate si scale factors.
4. Testeaza dupa update de Plasma si cu user nou.

## Verificare de acceptare

- [ ] Captureaza screenshoturi reale din VM pentru login, desktop si setari.
- [ ] Verifica navigarea cu tastatura, contrast si scalare 125/150/200%.

## Blocaje / lucruri interzise

- Nu modifica direct fisierele upstream KDE in /usr.
- Nu copia teme cu licente incompatibile sau assets fara provenienta.

## Livrabile

- `branding/desktop si docs/ux/kde-review.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/KDE/plasma-workspace
- https://github.com/sddm/sddm
