---
name: anypc-handheld-battery
description: "Adapteaza AnyPC OS la handheld PC, suspend/resume, bateria si controllerele incorporate."
---

# anypc-handheld-battery

**Domeniu:** Performance
**Activează când:** La suport ASUS/Lenovo/handheld ori laptop in Gaming Mode.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Detecteaza device model si suportul din hhd inainte de a activa serviciul.
2. Configureaza profiluri battery/quiet/performance cu politici coerente si o singura sursa.
3. Testeaza suspend/resume, dock/undock, rotatie si periferice interne.
4. Adauga UI pentru stare baterie si TDP numai pentru hardware suportat.

## Verificare de acceptare

- [ ] Testeaza trei cicluri suspend/resume si joc la baterie versus AC.
- [ ] Verifica ca controllerul revine functionar dupa resume.

## Blocaje / lucruri interzise

- Nu permite UI de TDP sa seteze valori in afara limitelor hardware.
- Nu instaleaza TLP si TuneD simultan activ fara justificare si teste.

## Livrabile

- `docs/hardware/handheld-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/hhd-dev/hhd
- https://github.com/redhat-performance/tuned
