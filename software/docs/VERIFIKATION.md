# Prüfung von Otoskop 2.0.0

Stand: 24. November 2026. Softwareprüfungen auf einem Apple-Silicon-Mac;
zusätzlich erster Funktionstest am aufgebauten Otoskop. Ältere Versionen
bleiben separat erhalten.

## Hardware-Test am 24.11.2026

Am Testaufbau mit XIAO ESP32-S3 Sense, OV3660, einem Auslösetaster, einer
weißen Status-LED und einer über MOSFET geschalteten Beleuchtungs-LED wurden
folgende Funktionen geprüft:

- Firmware 2.0.0 über die Mac-App installiert.
- Offline-Start und JPEG-Aufnahmen auf microSD im Akkubetrieb.
- Beleuchtung während der Aufnahme sowie Statusanzeige und Speicherbestätigung.
- WLAN-Start durch beim Einschalten gehaltenen Auslöser und anschließendes
  Loslassen; zusätzlich Start über Auslöser und RESET bei USB-Versorgung.
- Übertragung aufgenommener SD-Fotos über WLAN mit der Mac-App.

Beim Start wurden OV3660, Fotoauflösung 2048 × 1536 und 8 MB PSRAM erkannt.
Eine zunächst nicht erkannte Karte meldete „There is no valid FAT volume“.
Nach dem Einrichten einer einzelnen 16-GB-FAT32-Partition mit MBR auf einer
64-GB-Karte funktionierten Aufnahme und Import. Dies ist ein Test dieser
Karte und keine allgemeine Freigabe für alle 64-GB-Karten.

Die Ladeerkennung war hardwareseitig nicht angeschlossen; die beiden
Messeingänge sind im minimalen Testschaltplan mit Massebrücken vorgesehen.
Ladezustand und Ladeabschluss sind am Aufbau noch nicht geprüft.
Windows, Langzeitbetrieb, Fehlerfälle sowie Stromaufnahme und Temperatur
im direkten Vergleich der beiden Modi sind ebenfalls noch offen.

## Softwareprüfungen vom 18.11.2026

- ESP-Firmware mit Arduino-ESP32 3.3.11 für XIAO ESP32-S3, OPI-PSRAM und
  unverändertem 8-MB-Partitionslayout kompiliert: 1.087.189 Bytes Programm
  (32 % des App-Slots), 56.952 Bytes statischer RAM (17 %). Dynamischer PSRAM-
  Bedarf und Kameratreiber sind damit nicht am Sensor verifiziert.
- Vier C++-Hostprogramme erfolgreich: Foto-Dateinamen/Zählergrenzen,
  JPEG-Abmessungen/ungültige Daten neue Auslöser-/Startlogik und Ladeanzeige. JPEG-, Lade- und
  Auslösertests zusätzlich mit UndefinedBehaviorSanitizer.
- Auslösertests decken normales Einschalten, 5-Sekunden-Grenze, erforderliches
  Loslassen, frühes Loslassen, Kontaktprellen, Millis-Überlauf, langes Halten,
  erneutes Auslösen nach Loslassen sowie unterdrückte Tastendrücke bei
  Beschäftigung und Fehler ab.
- 6 Python-Porterkennungstests und Shell-Syntaxprüfung erfolgreich.
- 43 Desktoptests erfolgreich. Neue Tests verwenden den echten Qt-HTTP-Client
  gegen einen lokalen Testserver: mehrseitige SD-Liste, Auswahlimport ohne
  funktionsfähige Kamera, bytegenaue Speicherung, wiederholter Import,
  Namenskollisionen, Prüfsummen-/Größen-/JPEG-Fehler, falsches Gerät, ungültige
  Dateinamen, Abbruch mit später Antwort, Sprachwechsel, Fenster schließen und
  Rückkehr zur normalen Verbindung. Vorhandene Livebild-, USB-, Foto-, LED- und
  Oberflächentests bestehen weiterhin. Die zwei Übersetzungstests wurden nach
  einer abschließenden Beschriftungskorrektur zusätzlich wiederholt.
- UI-Vorschauen auf Deutsch/Englisch, hell/dunkel und SD-Auswahl angesehen.
  Die Vorschauen unter `output/vorschau` zeigen Demo-/simulierte Daten.
- Mac-App mit Firmware 2.0.0 und esptool gebaut, arm64 bestätigt und lokale
  Signatur mit `codesign --verify --deep --strict` geprüft.
- Paketierte GUI startet im Offscreen-Demomodus und bleibt bis zum Testende aktiv.
  Paketierter USB-Helfer besteht den Selbsttest: Firmware 2.0.0, esptool 5.1.0,
  ESP32-S3-Stub mit 5632 Bytes. Dabei wird kein USB-Gerät geöffnet.

Die Testprotokolle liegen unter `build/`. Desktop-HTTP-Tests benötigen Zugriff
auf lokale Loopback-Ports. Der erste Lauf in der Sandbox wurde deshalb vom
Betriebssystem blockiert; der vollständige Lauf mit Loopback-Zugriff bestand.

## Weitere Prüfungen am Gerät

Die folgenden Punkte enthalten auch die ursprünglichen Prüfschritte. Die oben
aufgeführten Funktionen wurden am 24.11.2026 im normalen Ablauf geprüft;
Grenz-, Fehler- und Langzeittests stehen weiterhin aus.

- Verdrahtung von Auslöser und Status-LED; richtiger Einschaltgriff auch unter
  USB-Versorgung, frühes Loslassen, langes Halten im Betrieb und wiederholte Fotos.
- Reale Bilder mit OV3660 bzw. tatsächlichem Sensor: maximale Auflösung,
  Bildschärfe, Belichtungsregelung, initial 30 % Licht, 400 ms Vorlauf und
  150 ms Nachlauf. Nachlauf ersetzt keine korrekte Fokussierung.
- Vollständige Sequenz aus Status aus, Licht an, Aufnahme, Licht aus, SD-Schreiben,
  zwei Bestätigungsblitzen und Bereitschaft. Licht bleibt bei Fehlern aus;
  der unabhängige 10-Sekunden-Watchdog muss auch bei blockierter Kamera greifen.
- Fehlende, volle, beschädigte und entfernte SD-Karte; fehlende Kamera; kein
  Erfolgsblinken nach Fehlern; Wiederanlauf und Erhalt vorhandener Bilder.
- SD-Import auf echter Hardware, einschließlich großer Kartenverzeichnisse,
  langen Übertragungen, Abbruch, erneutem Import und anschließender Liveansicht.
- Stromaufnahme und Gehäusetemperatur im direkten Vergleich zum WLAN-Livebild.
  Kamera-Deinitialisierung beendet den Treiber; Sensor-/SD-Versorgung bleiben
  angeschlossen. Es wurde keine bestimmte Akkulaufzeit oder Temperatur bestätigt.
- Stromunterbrechung beim Speichern bleibt ein Risiko für die aktuelle Datei und
  FAT. Der vorhandene Hauptschalter hat keine Software-Vorwarnung.
- Ladeversuch mit überprüfter Platinenrevision: ADC-Grenzen, leere/teilgeladene/
  volle Zelle, bereits voll beim Einstecken, kein Akku, S1 AUS, Abziehen/erneutes
  Einstecken von USB, gleichzeitige Fotoaufnahme. Keine unberechtigte Vollmeldung.
- Nativer Windows-Build, Start, USB-Installation und WLAN-Import auf Windows.

## Reproduzieren

Im Ordner `software` mit eingerichteter Python-Umgebung:

```bash
./scripts/build.sh
.venv/bin/python desktop/prepare_firmware.py
./scripts/test.sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=desktop .venv/bin/python -m unittest discover -s desktop/tests -v
.venv/bin/python desktop/build.py
.venv/bin/python desktop/package_source.py
```

Die getrennte Firmware-/App-Version und ihre enthaltenen SHA-256-Prüfsummen sind
in `desktop/firmware/manifest.json` dokumentiert. Das neue Firmwarepaket nutzt
weiterhin die bisherigen Flash-Adressen; der NVS-Fotozähler wird nicht gelöscht.

## Schaltplan Rev. 2.0

Am 18.11.2026 auf ein A3-Blatt reduziert: Auslöser an GPIO4, Status-LED über
1 kOhm an GPIO5; externe Sicherung F1 und Ringstecker J2 entfernt. PDF gerendert
und visuell geprüft; SVG, externe Netze und Drahtliste aus gemeinsamer Quelle
erzeugt. Firmware-Pins gegen settings.h geprüft. Dies ist ein Planungsabgleich,
kein bestandener elektrischer Test. Alte Hardware-Unterlagen sind archiviert.

## Ladeerkennung in Version 2.0.0

Der Herstellerplan XIAO V1.51 wurde einschließlich der realen Verbindungen von
SGM40567 nCHG, CHG0, U1.R11 und VBUS geprüft. SG Micro spezifiziert 160 ms aktives
Signal je 1280 ms während Ladung und 51,2 s kontinuierliches Signal am Abschluss.
Das 5-V-Signal benötigt den gezeichneten Teiler nach ADC1; USB wird separat
erfasst. Dies ist eine Prüfung der Herstellerunterlagen, keine elektrische
Messung des vorliegenden Boards.

C++-Tests mit UndefinedBehaviorSanitizer prüfen passende/unpassende Pulsfolgen,
Pegelübergänge, positiven Abschluss, ausbleibende Pulse ohne Vollmeldung, dauerhaft
aktive/inaktive Eingänge ohne Ladeverlauf, ADC-Zwischenpegel/Überbereich,
USB-Abziehen/Neuanstecken, Abtastlücken, Millis-Überlauf, die beiden 5-Sekunden-
Blinkmuster und den Vorrang der Fotobestätigung. Diese Tests haben bestanden.
Der ADC-/LED-Task läuft unabhängig von blockierenden Kamera- und SD-Funktionen.

## Externer Aufbau ohne Kondensatoren

C1-C4 sind aus PDF, SVG, Stückliste und externen Netzen entfernt. Die Bestückung
auf den Originalmodulen bleibt erhalten. R10-R13 je 10 kOhm, 1 %. In der
Firmware wird eine erste Wandlung nach Kanalwechsel verworfen; danach folgt
der Median aus fünf kalibrierten Messwerten. Pegeländerungen brauchen 20 ms
Stabilität, unklare Pegel 100 ms bis zur Ungültigkeit. Die Ladeschwellen sind
an die Belastung durch die vorhandene rote LED und U1.R11 angepasst: aktiv
bis 400 mV, inaktiv ab 650 mV. Der alte 100-kOhm-Aufbau hat andere Pegel.

Die Hosttests prüfen Ausreißer innerhalb von Messbursts, kurze Störungen auf
USB und Ladesignal, unklare Pegel sowie die Erkennung eines echten Ladeverlaufs
und Ladeabschlusses trotz Störungen. Alle Tests bestehen. Dies simuliert
Messwerte; es ist kein Nachweis für die reale Störfestigkeit des Aufbaus.

Vor Freigabe am Board prüfen: Lade-ADC-Pegel, USB-ADC-Pegel, Erwärmung und
Spannungseinbrüche beim Kamerastart, SD-Schreiben und WLAN-Streaming. Die
Software kann eine unzureichende Stromversorgung nicht ausgleichen. Es ist
keine uneingeschränkte Funktionsgarantie ohne Hardwareprüfung erteilt.
