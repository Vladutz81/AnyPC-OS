---
name: anypc-proton-wine
description: "Gestioneaza compatibilitatea jocurilor Windows prin Steam Proton, GE-Proton, UMU, Wine si DXVK."
---

# anypc-proton-wine

**Domeniu:** Gaming
**Activează când:** Cand un joc Windows nu porneste sau cand se integreaza launchere.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Identifica provenienta jocului, arhitectura, runtimeul si configuratia existenta.
2. Selecteaza Steam Proton prin Steam, UMU pentru jocuri non-Steam acolo unde este compatibil.
3. Foloseste prefix separat per joc si loguri cu date sensibile eliminate.
4. Testeaza DXVK/VKD3D si bibliotecile multilib pentru jocul concret.

## Verificare de acceptare

- [ ] Valideaza intrarea in joc si iesirea curata, controller, audio si salvarea.
- [ ] Inregistreaza versiunea Proton si regresiile in compatibility DB.

## Blocaje / lucruri interzise

- Nu promite functionarea anti-cheat sau Microsoft Store PC Game Pass pe Linux.
- Nu suprascrie prefixul sau save-urile la testarea altui Proton.

## Livrabile

- `docs/games/windows-compatibility.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/ValveSoftware/Proton
- https://github.com/Open-Wine-Components/umu-launcher
