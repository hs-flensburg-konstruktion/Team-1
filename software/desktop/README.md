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
