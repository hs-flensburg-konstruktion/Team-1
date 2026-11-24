# Digitales Otoskop

**Software und ESP-Firmware: 2.0.0 - Stand 24.11.2026**

- [Desktop-Anwendung und Änderungen in 2.0.0](desktop/README.md)
- [ESP-Firmware für XIAO ESP32-S3 Sense](firmware/Otoskop/)
- [Bedienung, Einrichtung und Entwicklung](docs/BEDIENUNG_2.0.0.md)
- [Ergebnisse des ersten Hardware-Tests und weitere Prüfungen](docs/VERIFIKATION.md)
- [Schaltplan für den ersten Testaufbau](hardware/Otoskop_2.0.0_Erster_Testaufbau.pdf)
- [Vollständige Hardware-Erweiterung einschließlich vorbereiteter Ladeerkennung](hardware/README.md)

Normal einschalten startet den Offline-Modus. Den Auslöser bereits vor dem
Einschalten gedrückt halten, nach dem Einschalten mindestens fünf Sekunden
weiterhalten und loslassen startet den WLAN-Modus. Bei USB-Versorgung dafür
den Auslöser halten, RESET kurz drücken, fünf Sekunden weiterhalten und loslassen.

Offline-Fotos im Akkubetrieb, Moduswechsel und WLAN-Fotoimport wurden am
Testaufbau geprüft. Die externe Ladeanzeige ist in der Firmware vorbereitet,
hardwareseitig noch nicht angeschlossen und noch nicht am Gerät geprüft.

Die fertige App für Apple Silicon (M1 oder neuer) steht unter
[Releases](https://github.com/hs-flensburg-konstruktion/Team-1/releases).
Das Windows-Paket enthält Quellcode und Startskript, keine fertige EXE.
