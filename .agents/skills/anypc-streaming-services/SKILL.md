---
name: anypc-streaming-services
description: "Integreaza Sunshine, Moonlight si OBS cu permisiuni, network discovery si suport GPU."
---

# anypc-streaming-services

**Domeniu:** Gaming
**Activează când:** Cand este activat streaming-ul sau inregistrarea gameplay-ului.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Detecteaza VAAPI/NVENC/AMF compatibil si fallback CPU limitat.
2. Configureaza codec, bitrate, porturi si authentification doar dupa acord.
3. Testeaza captura Gamescope/Wayland, input controller remote si rezolutie.
4. Adauga dezactivare completa a serviciilor din setari AnyPC.

## Verificare de acceptare

- [ ] Testeaza retea locala, reconectare client si oprire curata a serverului.
- [ ] Masura latency/frametime si consumul GPU la capturare.

## Blocaje / lucruri interzise

- Nu expune Sunshine direct pe internet implicit.
- Nu asculta microfon/captureaza ecranul fara acord.

## Livrabile

- `docs/streaming/streaming-security.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/SunshineStream/Sunshine
- https://github.com/moonlight-stream/moonlight-qt
