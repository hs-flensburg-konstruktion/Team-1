# Desktop-Anwendung

Die Anwendung zeigt das Kamerabild per WLAN, speichert Fotos am Rechner und steuert die LED-Helligkeit. Im Demomodus lässt sich die Oberfläche ohne Otoskop ausprobieren.

## Aus dem Quellcode starten

Voraussetzung ist Python 3.10 bis 3.14 in 64 Bit. Die Startskripte installieren die benötigten Pakete beim ersten Start.

- macOS ab Version 13: `bash desktop/Start-Otoskop.command --demo` im Ordner `software` ausführen.
- Windows: `desktop/Start-Otoskop.bat` öffnen und in der Anwendung **Demo** einschalten.

Für das Livebild den Rechner mit dem WLAN des Otoskops verbinden und in der Anwendung auf **Verbinden** klicken.

## Firmware vorbereiten

Für die USB-Einrichtung aus dem Quellcode und für einen eigenen App-Build wird das Firmwarepaket benötigt. Auf dem Mac im Ordner `software` ausführen:

```sh
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/build.sh
python3 desktop/prepare_firmware.py
```

Das Paket liegt danach in `desktop/firmware/`. Für einen Windows-Build kann der erzeugte Ordner mitkopiert werden.

## Anwendung bauen

Auf dem Zielsystem in der Python-Umgebung der Anwendung ausführen:

```sh
python -m pip install -r desktop/requirements-build.txt
python desktop/build.py
```

Der Build liegt in `output/desktop/`. [Lizenzhinweise](licenses/HINWEISE.txt)

## Update: Software und Firmware 2.0.0

Beim ersten Hardware-Test wurde der ESP während der dauerhaften WLAN-Liveübertragung deutlich warm. Für den mobilen Einsatz wurde deshalb ein zusätzlicher Offline-Modus ergänzt. WLAN und Gehörgangbeleuchtung müssen dadurch nicht mehr durchgehend aktiv sein.

### Zwei Betriebsarten

- **Offline-Modus:** Startet beim normalen Einschalten. Ein Druck auf den Auslöser nimmt ein Foto auf und speichert es als JPEG im Ordner `photos` auf der microSD-Karte. WLAN bleibt ausgeschaltet.
- **WLAN-Modus:** Bietet weiterhin Livebild und Helligkeitssteuerung. Zusätzlich lassen sich die auf der SD-Karte gespeicherten Fotos über **SD-Fotos importieren** auf den Rechner übertragen. Die Originale bleiben auf der Karte.

Zum Starten des WLAN-Modus den Auslöser bereits vor dem Einschalten gedrückt halten, nach dem Einschalten mindestens fünf Sekunden weiterhalten und anschließend loslassen. Erst nach dem Loslassen startet das WLAN `Otoskop-…`. Ein normaler Neustart führt wieder in den Offline-Modus. Erneutes Flashen ist nicht nötig.

Bei USB-Versorgung ersetzt ein kurzer Druck auf RESET das Einschalten; der große Schalter trennt nur den Akku.

### Beleuchtung und Status

Im Offline-Modus schaltet sich die Gehörgangbeleuchtung nur für die Aufnahme ein. Eine kurze Vor- und Nachlaufzeit sorgt dafür, dass die Beleuchtung während der Aufnahme stabil ist.

Die externe weiße Status-LED zeigt:

- Dauerlicht: bereit für die nächste Aufnahme.
- Aus während der Aufnahme und des Speicherns.
- Zweimaliges kurzes Blinken: Bild erfolgreich gespeichert, danach wieder Dauerlicht.

Die Ladeanzeige ist in der Firmware vorbereitet, im aktuellen Testaufbau aber hardwareseitig noch nicht angeschlossen und daher noch nicht praktisch geprüft. Vorgesehen sind ein kurzer Blitz alle fünf Sekunden beim Laden und zwei kurze Blitze nach erkanntem Ladeabschluss. Eine Akku-Prozentanzeige ist nicht vorgesehen.

Offline-Aufnahmen im Akkubetrieb, der Wechsel in den WLAN-Modus und der Fotoimport wurden am Testaufbau erfolgreich geprüft. Die microSD-Karte muss als FAT32 formatiert sein.
