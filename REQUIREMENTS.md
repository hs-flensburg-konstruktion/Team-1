# Digitales Otoskop – Anforderungen

Stand: Mac-App 1.5.0, ESP-Firmware 1.4.0. Die Häkchen zeigen, was eingebaut ist. Der offizielle Hardwaretest steht noch aus.

## Eingebaut

- [x] Mac-App für Apple Silicon ab macOS 13 (SW-01).
- [x] Neu in 1.5: Hell und dunkel über Sonne und Mond umschalten. Die App merkt sich die Auswahl (OPT-04).
- [x] Livebild mit 640 × 480 über das WLAN des Otoskops, mit Pause, Vollbild und Verbindungsanzeige (SW-05, SW-08, SW-13, SW-14, SW-18, OPT-05).
- [x] Oberfläche auf Deutsch und Englisch, mit Demo und Hilfe zur Einrichtung (SW-04, SW-06, SW-07, SW-10).
- [x] ESP-Firmware per USB direkt in der App installieren. Der Assistent führt durch die Einrichtung und zeigt das WLAN an (SW-09, OPT-11).
- [x] Fehler bei Kamera und Verbindung anzeigen und bei Abbruch erneut verbinden (SW-11, SW-17, SW-31, OPT-15, OPT-30).
- [x] Fotos per Knopf oder Leertaste in der maximalen Auflösung des Kamerasensors aufnehmen. Original-JPEG im gewählten Ordner speichern und in der App als Vorschau anzeigen (SW-19, SW-21, SW-23, SW-24, SW-26, SW-27).
- [x] Über die Webseite des ESP Fotos separat auf microSD speichern (SW-25).
- [x] Lokal arbeiten, ohne Konto und Cloud (SW-12, SW-29, SW-33).
- [x] Anleitung, Beschreibung der ESP-Schnittstelle und Testskripte sind im Projekt (SW-16, SW-35, SW-36, SW-37, SW-39, OPT-36).

## Teilweise eingebaut

- Windows nutzt denselben App-Code. Es gibt ein Startskript und ein Quellpaket. Die fertige EXE und der Test unter Windows stehen noch aus (SW-02, SW-03).
- LED-Regler und PWM sind im Code. Die Ausgabe ist im ausgelieferten Stand mit `LIGHT_GPIO = -1` deaktiviert. Der passende Pin muss für den Aufbau gesetzt werden (SW-15, SW-20, SW-34).
- Die App erkennt unterstützte Geräte über USB. Das WLAN wählt man selbst. Die ESP-Webseite bietet Livebild und SD-Aufnahme (OPT-03, OPT-09, OPT-16).
- Die Seitenleiste lässt sich ausblenden. Die App zeigt Fotos der aktuellen Sitzung und benennt PC-Fotos mit Datum und Uhrzeit. SD-Fotos werden durchnummeriert (OPT-07, OPT-24, OPT-27).
- Die App prüft JPEGs und zeigt Schreibfehler an. Bei einem Abbruch auf der SD-Karte können unvollständige Dateien bleiben (SW-28, SW-32).
- Details zum Flashen und serielle ESP-Meldungen helfen bei der Fehlersuche (OPT-17, OPT-31, OPT-39).

## Noch offen

- [ ] Livebild und Aufnahme am aufgebauten Otoskop prüfen, auch bei längerer Nutzung (SW-30).
- [ ] Physischen Fotoauslöser ergänzen (SW-22).
- [ ] Akkuanzeige, Videoaufnahme und automatischen Import von SD-Fotos umsetzen (OPT-08, OPT-19, OPT-25).

Weitere optionale Punkte für später sind zusätzliche Plattformen und Sprachen, mehr Kamera- und Bildfunktionen, automatische Einrichtung, Datensicherung und Updates.
