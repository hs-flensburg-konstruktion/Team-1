# Otoskop 2.0.0

Neue, getrennte Version mit Offline-Aufnahmen und WLAN-Fotoimport. Desktop-App
und ESP-Firmware tragen beide die Versionsnummer 2.0.0. Die bisherigen
Firmware-/App-Quellstände und App-Releases bleiben erhalten. Die neue App verwendet
eigene Einstellungen, damit auch die Konfiguration der alten App erhalten bleibt.

## Starten und einrichten

Die fertige Mac-App liegt nach dem Paketbau unter `output/desktop/Otoskop.app`.
Sie ist für Apple Silicon ab macOS 13. Die Firmware ist enthalten und wird in
**Otoskop einrichten** einmalig über ein USB-Datenkabel installiert.
Dabei wird das Programm auf dem angeschlossenen ESP ersetzt; die SD-Fotos bleiben
unangetastet. Firmwareinstallation, Offline-Aufnahmen im Akkubetrieb, WLAN-Start und
SD-Fotoimport wurden am 24.11.2026 am Testaufbau geprüft.

Der gesamte externe Aufbau kommt ohne zusätzliche Kondensatoren aus.
Akku-, Masse- und LED-Leitungen kurz und direkt führen. Die Stabilität muss
beim realen Kamera-/SD-/WLAN-Betrieb geprüft werden.

Vor der Verwendung die Hardware um Auslösetaster und Status-LED ergänzen:
[Aktueller Ein-Seiten-Schaltplan](../hardware/Otoskop_2.0.0_Testaufbau.pdf) und
[Verdrahtung](../hardware/ERGAENZUNGEN_2.0.md). GPIO4 ist der Auslöser, GPIO5 die
weiße Status-LED mit Vorwiderstand; GPIO1 bleibt die Beleuchtung am MOSFET.

Der minimale Aufbau mit nur einer Beleuchtungs-LED ist im
[Schaltplan für den ersten Test](../hardware/Otoskop_2.0.0_Erster_Testaufbau.pdf)
beschrieben. Die Ladeerkennung ist darin nicht aufgebaut.

## Offline-Modus

1. FAT32-microSD bis 32 GB einsetzen und normal einschalten.
2. Die weiße Status-LED leuchtet dauerhaft, sobald Kamera, SD und Beleuchtung
   bereit sind. Zum Fotografieren wird kein Rechner benötigt.
3. Ein Tastendruck startet genau eine Aufnahme. Die Status-LED geht aus.
4. Die Gehörgangbeleuchtung schaltet ein. Nach 400 ms Einregelzeit wird ein
   vollständiges JPEG in maximaler Sensorauflösung aufgenommen. Nach 150 ms
   Nachlauf geht das Licht aus. Beide Zeiten sind in `settings.h` einstellbar.
5. Das Foto wird vollständig gespeichert und synchronisiert. Erst dann blinkt
   die Status-LED zweimal kurz und leuchtet anschließend wieder dauerhaft.

Gedrückthalten erzeugt keine Serie. Tastendrücke während der Aufnahme,
Speicherung und Bestätigung werden verworfen. Erst Loslassen und erneutes
Drücken löst das nächste Foto aus. Bei fehlender Karte, Kamera-/Lichtfehler oder
Schreibfehler bleibt die Status-LED im Akkubetrieb aus; nach Beheben des Fehlers neu starten.
Es gibt keine Erfolgsmeldung für eine fehlgeschlagene Aufnahme.

WLAN und Webserver werden im Offline-Modus nicht gestartet. Die Kamera verwendet
einen Einzelbildpuffer und wird zwischen den Aufnahmen deinitialisiert. Das
reduziert aktive Kamera-Verarbeitung; die Versorgung der Sense-Platine und des
Sensors wird dadurch nicht physisch getrennt. Eine bestimmte Temperatur oder
Akkulaufzeit ist damit noch nicht nachgewiesen. Die Beleuchtung startet mit
30 % und muss am Aufbau auf Ausleuchtung und Wärme geprüft werden.

## Laden und äußere Status-LED

Bei angeschlossenem USB hat die Ladeanzeige Vorrang vor der dauerhaften
Bereitschaftsanzeige:

- Lädt: alle fünf Sekunden ein kurzer Blitz (100 ms).
- Ladeabschluss erkannt: alle fünf Sekunden zwei kurze Blitze (je 100 ms,
  100 ms Pause). Der erkannte Abschluss bleibt bis zum Abziehen von USB erhalten;
  ein erneut erkannter Ladezyklus schaltet wieder auf Einzelblinken.
- Zustand unklar: keine Ladeblitze. Insbesondere bedeutet eine ausgeschaltete
  rote Lade-LED nicht automatisch „voll“.
- USB abgezogen: wieder normale Bereitschafts-/Fotoanzeige.

Während einer Offline-Aufnahme bleibt die äußere LED aus. Die zwei Blitze nach
erfolgreichem Speichern haben Vorrang vor der periodischen Ladeanzeige. Diese
setzt anschließend wieder ein. Bei USB-Versorgung sind die Ladeblitze kein
Nachweis für Aufnahmebereitschaft oder eine funktionsfähige SD-Karte.

Der ESP beobachtet das echte nCHG-Signal des Ladebausteins SGM40567. Nach drei
plausiblen Ladepulsen erkennt er „lädt“. Ein anschließendes, mindestens fünf
Sekunden lang aktives Signal bestätigt den Ladeabschluss. Bloßes Ausbleiben der
Pulse bestätigt ihn nicht. Wird USB erst bei bereits vollem Akku angeschlossen
oder der ESP nach dem Abschluss neu gestartet, kann das Signal uneindeutig sein;
dann bleibt der Zustand unbekannt. Dies verhindert eine erfundene Vollmeldung.
Ein eingesetzter Akku und S1 EIN sind zum Laden erforderlich; die Abfrage ersetzt
keine unabhängige Akkuanwesenheits- oder Schaltererkennung.

Die Zusatzbeschaltung verwendet vier Widerstände (je 10 kOhm, 1 %),
keine zusätzlichen Kondensatoren. Die Werkbestückung auf XIAO/Sense bleibt
erhalten. Mehrfachmessung und zeitliche Entstörung sind in der Firmware enthalten. Lade-LED und USB liegen auf der 5-V-Seite; niemals
direkt an einen ESP-GPIO anschließen. Der Schaltplan zeigt die geteilten Signale
an D5/GPIO6 und D1/GPIO2. D1 ist damit für die USB-Erkennung belegt. Ein
Akku-Prozentwert wird nicht berechnet. Die neue Firmware muss nach dieser
Verdrahtung erneut über die App installiert werden; die Versionsnummer bleibt
2.0.0. Der reale Ladeversuch am Aufbau steht aus.

## WLAN-Modus

Auslöser bereits vor dem Einschalten gedrückt halten, mindestens fünf Sekunden
halten und loslassen. Erst das Loslassen startet den WLAN-Modus. Früheres
Loslassen startet Offline. Es gibt keinen Wechsel durch Gedrückthalten im
laufenden Betrieb. Die Auswahl gilt nur bis zum nächsten Neustart; normal
neustarten führt immer wieder in den Offline-Modus. Kein erneutes Flashen nötig.

Bei angeschlossenem USB versorgt das Kabel den ESP trotz ausgeschaltetem
Hauptschalter. Dann Auslöser halten, RESET am XIAO kurz drücken, Auslöser noch
fünf Sekunden halten und loslassen. Auslöser und BOOT sind unterschiedliche Tasten.

Mit **Otoskop-XXXXXX**, Passwort **Otoskop-2026**, verbinden und in der App
**Verbinden** wählen. Livebild, Fotos direkt auf den Rechner und LED-Regler sind
weiter vorhanden. Im WLAN-Modus wird der physische Auslöser nicht für Fotos
verwendet. „Kein Internet“ ist bei diesem lokalen WLAN normal.

## Fotos von der SD-Karte importieren

Im WLAN-Modus in der App **SD-Fotos importieren** wählen. Fotos
ankreuzen und **Auswahl importieren** anklicken. Das Livebild pausiert während
des Imports und wird danach entsprechend der zuvor gewählten Vorschau-Einstellung
wieder verbunden. Auch bei ausgefallener Kamera ist der Import möglich, solange
WLAN und SD verfügbar sind.

Die App prüft Dateigröße, Gerätekennung, SHA-256 und Lesbarkeit des JPEG. Ziel ist
`SD-Import/<Gerätekennung>` im gewählten Fotoordner. Identische Dateien werden
übersprungen; unterschiedliche Dateien mit gleichem Namen bleiben zusätzlich
erhalten. Die Vorschauleiste zeigt die letzten 100 importierten bzw. aufgenommenen
Fotos. Originale auf der SD werden niemals automatisch gelöscht. Bei Abbruch oder
Fehler bleiben bereits vollständig importierte Dateien erhalten. Der Import kann
wiederholt werden. Fotos mit weniger als 4 Bytes oder über 4 MiB sind nicht auswählbar.

Alternativ sind die Fotos direkt über `http://192.168.4.1` unter **SD-Fotos
anzeigen** herunterladbar oder mit einem Kartenleser als normale JPEGs lesbar.
USB dient der Einrichtung und Diagnose; ein USB-Laufwerksmodus ist nicht eingebaut.
Ein Ausschalten während des Schreibens kann trotz Synchronisierung die aktuelle
Datei oder das FAT-Dateisystem beschädigen. Vor Ausschalten die Doppelblitze und
die anschließend dauerhaft leuchtende Status-LED abwarten.

## Windows und Entwicklung

Der gemeinsame Quellcode enthält alle neuen Funktionen auch für Windows.
Start: `desktop/Start-Otoskop.bat` mit Python 3.10–3.14 in 64 Bit.
Für eine eigenständige EXE auf Windows:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r desktop\requirements-build.txt
.venv\Scripts\python.exe desktop\build.py
```

Ein nativer Windows-Build und Windows-Tests stehen aus. Offline-Aufnahmen,
Moduswechsel und WLAN-Import wurden am aufgebauten Otoskop geprüft.
Details zu Prüfungen und noch offenen Hardwaretests: [VERIFIKATION](VERIFIKATION.md).

Auf diesem Mac kann die bestehende Python-Umgebung ohne Änderung wiederverwendet
werden. Alle Ausgaben liegen in diesem neuen Versionsordner:

```bash
./scripts/build.sh
.venv/bin/python desktop/prepare_firmware.py
./scripts/test.sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=desktop .venv/bin/python -m unittest discover -s desktop/tests -v
.venv/bin/python desktop/build.py
.venv/bin/python desktop/package_source.py
```

Die lokale Arduino CLI und ctags wurden in diesen Ordner kopiert; der vorhandene
Espressif-Core 3.3.11 wird mit einer eigenen Build-Konfiguration genutzt. Auf
einem anderen Mac zuerst `./scripts/setup.sh` ausführen und eine eigene `.venv`
mit `desktop/requirements-build.txt` anlegen.
