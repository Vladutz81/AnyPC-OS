---
name: anypc-network-stack
description: "Configureaza NetworkManager, Wi-Fi, Ethernet si firewall fara deschiderea inutila a porturilor."
---

# anypc-network-stack

**Domeniu:** Hardware
**Activează când:** Cand instalatorul ori Gaming Mode necesita retea.

## Condiții obligatorii

- Confirmă mai întâi structura REALĂ și versiunea existentă AnyPC OS; nu presupune că un URL din inventar este un pachet instalat.
- Înainte de modificări: `git status --short`, branch separat, raport baseline și backup pentru orice fișier sensibil.
- Dacă o operație poate afecta boot, partiții, chei, drivere active sau date: testează întâi într-o VM ori pe o imagine duplicată; solicită aprobare explicită pentru aplicarea pe hardware real.

## Workflow

1. Detecteaza chipset si firmware Wi-Fi, versiunea NetworkManager si profilele active.
2. Testeaza wifi WPA2/WPA3, Ethernet, reconnect si schimbarea retelei fara reboot.
3. Permite setare offline si diagnostic DNS/DHCP/TLS.
4. Restrange Sunshine, remote play si alte servicii la permisiuni explicite.

## Verificare de acceptare

- [ ] Testeaza conectare fara internet si instalare cu mirror indisponibil.
- [ ] Verifica nftables/firewalld si conexiuni inbound.

## Blocaje / lucruri interzise

- Nu modifica firewall global pentru un singur joc.
- Nu inscrie parole Wi-Fi in loguri, rapoarte sau scripturi.

## Livrabile

- `docs/network/connectivity-matrix.md` sau, dacă aceste căi nu există în proiect, o locație echivalentă stabilită din audit.
- Raport cu: comenzi executate, fișiere modificate, rezultate reale, teste neexecutate și rollback. Nu afirma «funcționează» fără probe.

## Referințe

- https://github.com/NetworkManager/NetworkManager
- https://github.com/firewalld/firewalld
