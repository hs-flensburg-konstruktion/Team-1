# Otoskop 2.0.0 - Testaufbau ohne externe Kondensatoren

Stand: 18. November 2026. Ein A3-Blatt zeigt die vollständige externe
Modulverdrahtung. Keine zusätzlichen Kondensatoren erforderlich. Die auf XIAO
und Sense vorhandenen Bauteile bleiben werkseitig bestückt; es wird kein
Kondensator von den Modulen entfernt.

## Dateien

- [Schaltplan als PDF](Otoskop_2.0.0_Testaufbau.pdf), ein Blatt A3 quer.
- [Bearbeitbare Vektorzeichnung](Otoskop_2.0.0_Testaufbau.svg).
- [Drahtliste](Otoskop_2.0.0_Drahtliste.csv), [Netzliste](Otoskop_2.0.0_Netzliste.csv),
  [externe Netze](Otoskop_2.0.0_Netze.json).
- [Anschlussdetails](ERGAENZUNGEN_2.0.md).
- `generate_schematic.py` erzeugt alle Zeichnungen und Verdrahtungsdaten aus
  derselben Quelle; `settings_reference.h` enthält die passende Pinbelegung.

## Anschlüsse

| Funktion | XIAO-Anschluss | Beschaltung |
| --- | --- | --- |
| Beleuchtung | D0 / GPIO1 | R5 100 Ohm zum AO3400A-Gate, R6 100 kOhm nach GND |
| Auslöser S2 | D3 / GPIO4 | Schließer nach GND, interner Pull-up aktiv |
| Status-LED D5 | D4 / GPIO5 | R9 1 kOhm zur Anode, Kathode nach GND |
| Ladesignal | D5 / GPIO6 / ADC1 | Kathode der roten Onboard-LED über R10/R11, je 10 kOhm |
| USB-Erkennung | D1 / GPIO2 / ADC1 | USB 5V über R12/R13, je 10 kOhm |
| Akku | BAT+ / BAT- | Halterplus über S1 an BAT+, Minus an GND |
| Kamera und microSD | Sense-Erweiterung | Original-Modulstecker verwenden |

R1-R4 je 220 Ohm bleiben als Vorwiderstände der vier Beleuchtungs-LEDs erhalten.
C1-C4 sind aus der externen Schaltung entfernt. Externe Sicherung und Ringstecker
sind ebenfalls nicht vorgesehen. Alle gleichen Netznamen, insbesondere VBAT_SW
und GND, miteinander verbinden. Der LED-Ring wird direkt angelötet.

Die kleineren Messwiderstände belasten die ADC-Eingänge weniger hochohmig als
100-kOhm-Teiler. Die Firmware verwirft die erste Wandlung nach Kanalwechsel,
bildet aus fünf weiteren Messungen den Median und bestätigt Pegeländerungen
erst nach 20 ms. Unklare Pegel werden nach 100 ms als unbekannt behandelt.
Das reduziert kurze Messstörungen, ist aber kein Ersatz für eine stabile
Stromversorgung. Akku-, Masse-, LED- und Messleitungen kurz und direkt führen.
Die bestehenden Versorgungskondensatoren der Originalmodule bleiben notwendig.

Für den 10-kOhm-Aufbau die dazugehörige Firmware 2.0.0 neu installieren.
Die bisherige Firmware für 100-kOhm-Teiler besitzt andere Ladesignal-Schwellen.
Die Software im alten GitHub-Upload-Repository bleibt weiterhin 1.6.0/1.5.0;
für diesen Plan den separaten Versionsordner `Otoskop-2.0.0` verwenden.

## Laden und Anzeige

Lädt: ein kurzer Blitz alle fünf Sekunden. Nach positiv erkanntem Ladeabschluss:
zwei kurze Blitze alle fünf Sekunden. Fotoaufnahme und Speicherbestätigung
haben Vorrang. USB ohne klares Ladesignal, eine bereits volle Zelle beim Start
oder fehlende Ladehistorie erzeugen keine erfundene Vollmeldung. Eingesetzter
Akku und S1 EIN sind zum Laden erforderlich; diese Signale erkennen die
Akkuanwesenheit und Schalterstellung nicht unabhängig.

S1 trennt nur den Akku, nicht USB. Unter USB zum WLAN-Start Auslöser halten,
RESET kurz drücken, fünf Sekunden halten und loslassen. Zum Laden das Gerät
ruhen lassen und das Gehörganglicht ausschalten.

Der Plan ist ein Testentwurf. Elektrischer Aufbau, Ladeanzeige, Spannungseinbrüche
bei Kamera/SD/WLAN und Temperatur müssen am realen Gerät geprüft werden. Eine
uneingeschränkte Funktionsgarantie ohne diese Prüfung ist nicht möglich.

## Erneut erzeugen

```bash
python3 hardware/generate_schematic.py
```

Benötigt Python mit reportlab. Die PDF landet in `output/pdf/`, SVG und CSV/JSON
neben dem Generator. Mit `--settings PFAD` und `--output ORDNER` lassen sich
Referenz und PDF-Ausgabe wählen. Die SVG ist eine Zeichnung, kein KiCad-Projekt.

Grundlagen: [Seeed XIAO, Schaltplan V1.51](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/new-res/202003753_XIAO%20ESP32S3%20Sense_V1.51_SCH_260611.pdf),
[AOS AO3400A](https://www.aosmd.com/res/data_sheets/AO3400A.pdf),
[SG Micro SGM40567](https://www.sg-micro.com/rect/assets/e95e555a-a8a2-4761-b86a-6554dff2d8ed/SGM40567.pdf),
[Espressif ADC, Mehrfachmessung](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/adc_calibration.html#minimize-noise).
