---
name: anypc-diagnostics-debugging
description: "Depaneaza erori de boot, drivere, gaming, retea si servicii prin dovezi reproductibile."
---

# anypc-diagnostics-debugging

**Domeniu:** QA
**Activează când:** La crash, black screen, instalare esuata, audio lipsa sau launcher blocat.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Colecteaza simptome, pasii de reproducere, nivelul hardware si commitul.
2. Foloseste journalctl -b -p warning..alert, systemctl --failed, dmesg -T si logs ale aplicatiei doar citire.
3. Diferentiaza eroare kernel, driver, bootloader, Wayland, gamescope, runtime si game.
4. Propune patch minim cu test de regresie si posibilitate de revert.

## Verificare de acceptare

- [ ] Demonstreaza eroarea inainte si disparitia dupa fix.
- [ ] Ataseaza loguri anonimizate, comenzi si versiuni relevante.

## Blocaje / lucruri interzise

- Nu sterge loguri pentru a ascunde erori si nu raporta succes fara retestare.
- Nu executa debug direct pe sistem production fara backup daca necesita root.

## Livrabile

- `docs/bugs/issue-reproduction.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/systemd/systemd
