# Digitales Otoskop – Anforderungen

Stand: Mac-App 1.5.0, ESP-Firmware 1.4.0. Die Häkchen zeigen, was eingebaut ist. Der offizielle Hardwaretest steht noch aus.

## Eingebaut

- [x] Mac-App für Apple Silicon ab macOS 13.
- [x] Neu in 1.5: Hell und dunkel über Sonne und Mond umschalten. Die App merkt sich die Auswahl.
- [x] Livebild mit 640 × 480 über das WLAN des Otoskops, mit Pause, Vollbild und Verbindungsanzeige.
- [x] Oberfläche auf Deutsch und Englisch, mit Demo und Hilfe zur Einrichtung.
- [x] ESP-Firmware per USB direkt in der App installieren. Der Assistent führt durch die Einrichtung und zeigt das WLAN an.
- [x] Fehler bei Kamera und Verbindung anzeigen und bei Abbruch erneut verbinden.
- [x] Fotos per Knopf oder Leertaste in der maximalen Auflösung des Kamerasensors aufnehmen. Original-JPEG im gewählten Ordner speichern und in der App als Vorschau anzeigen.
- [x] Über die Webseite des ESP Fotos separat auf microSD speichern.
- [x] Lokal arbeiten, ohne Konto und Cloud.
- [x] Anleitung, Beschreibung der ESP-Schnittstelle und Testskripte sind im Projekt.

## Teilweise eingebaut

- Windows nutzt denselben App-Code. Es gibt ein Startskript und ein Quellpaket. Die fertige EXE und der Test unter Windows stehen noch aus.
- LED-Regler und PWM sind im Code. Die Ausgabe ist im ausgelieferten Stand mit `LIGHT_GPIO = -1` deaktiviert. Der passende Pin muss für den Aufbau gesetzt werden.
- Die App erkennt unterstützte Geräte über USB. Das WLAN wählt man selbst. Die ESP-Webseite bietet Livebild und SD-Aufnahme.
- Die Seitenleiste lässt sich ausblenden. Die App zeigt Fotos der aktuellen Sitzung und benennt PC-Fotos mit Datum und Uhrzeit. SD-Fotos werden durchnummeriert.
- Die App prüft JPEGs und zeigt Schreibfehler an. Bei einem Abbruch auf der SD-Karte können unvollständige Dateien bleiben.
- Details zum Flashen und serielle ESP-Meldungen helfen bei der Fehlersuche.

## Noch offen

- [ ] Livebild und Aufnahme am aufgebauten Otoskop prüfen, auch bei längerer Nutzung.
- [ ] Physischen Fotoauslöser ergänzen.
- [ ] Akkuanzeige, Videoaufnahme und automatischen Import von SD-Fotos umsetzen.

Weitere optionale Punkte für später sind zusätzliche Plattformen und Sprachen, mehr Kamera- und Bildfunktionen, automatische Einrichtung, Datensicherung und Updates.
