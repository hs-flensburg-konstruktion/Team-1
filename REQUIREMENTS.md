# Digitales Otoskop – Softwarestand

Mac-App 1.6.0 und ESP-Firmware 1.5.0.

**Die offizielle Erprobung der Hardware steht noch aus.**

## Eingebaut

- [x] Mac-App für Apple Silicon ab macOS 13, auf Deutsch und Englisch. Hell-/Dunkelmodus, Demo und Hilfe sind eingebaut.
- [x] Firmware über USB in der App installieren. Der Assistent zeigt danach das WLAN des Otoskops an.
- [x] Livebild mit 640 × 480 über das WLAN des Otoskops. Das Bild lässt sich pausieren und im Vollbild anzeigen. Bei einem Abbruch versucht die App, sich neu zu verbinden.
- [x] Fotos in der maximalen Auflösung des Kamerasensors aufnehmen und als JPEG im gewählten Ordner speichern. Neue Fotos erscheinen in der Vorschauleiste.
- [x] LED über D0 (GPIO1) von 0 bis 100 % dimmen. Beim Start ist sie aus. Ohne Steuerbefehl schaltet sie nach 10 Sekunden ab.
- [x] Zusätzlich kleine Browseransicht direkt auf dem ESP. Im Otoskop-WLAN lässt sie sich unter `http://192.168.4.1` öffnen. Dort gibt es ein Livebild und eine Taste für Fotos auf microSD.
- [x] Die App funktioniert lokal ohne Konto und Cloud.

## Noch offen

- [ ] Livebild, Fotos, SD-Speicherung und LED-Regelung am aufgebauten Otoskop offiziell erproben.
- [ ] Windows-EXE erstellen und auf Windows testen. Quellpaket und Startskript sind vorhanden.
- [ ] Fotoauslöser am Gerät, Akkuanzeige, Videoaufnahme und automatischen Import von SD-Fotos ergänzen.

Weitere optionale Punkte für später sind zusätzliche Plattformen und Sprachen und mehr Kamera- und Bildfunktionen
