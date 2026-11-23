CAD-Dateien
# Digitales Otoskop V1

Digitales Otoskop auf Basis des [GliaX/Otoscope](https://github.com/GliaX/Otoscope). Es hat eine Kamera (ESP32-S3), LED-Beleuchtung und einen Akku. Alle Teile sind gesteckt oder geklipst, es wird nichts geklebt.

![Design](Design_Clean_Medizintechnik.png)

> Hochschul-Prototyp (Gruppe 1). Keine Freigabe zur Untersuchung von Patienten.

## Dateien

| Datei | Inhalt |
|---|---|
| `Otoskop_Digital_V1_Gehaeuse.step` | Gehäuse als Baugruppe (6 Teile, ohne Elektronik) |
| `Otoskop_Digital_V1_Gehaeuse.stl` | Gehäuse zusammengebaut, zur Ansicht (zum Drucken die Einzel-STLs nehmen) |
| `01`–`06_*.stl` | Druckteile einzeln |
| `Otoskop_Digital_V1_Druckplatte_BambuLab.3mf` | Alle Druckteile auf einer Platte (256 × 256 mm) |

## Zukaufteile

| Bauteil | Typ |
|---|---|
| Mikrocontroller + Kamera | Seeed XIAO ESP32-S3 Sense, OV3660 |
| Beleuchtung | 4 × SMD-LED 1206, MOSFET AO3400A |
| Akku | XTAR 14500 im AA-Halter |
| Hauptschalter | Marquardt 1801.1102 (Wippe) |
| Foto-Taster | 6 × 6 × 5 mm, 2-Pin DIP |
| Status-LED | 5 mm |

## Druck

PETG, Schichthöhe 0,15–0,2 mm.

| Teil | Farbe | Hinweis |
|---|---|---|
| 01 Kopf | Petrol | Stützen an Zapfen, Kragen und Kinn |
| 02 Kameraträger | Schwarz | flach, LED-Taschen oben |
| 03 Rückdeckel | Anthrazit | Außenseite aufs Bett |
| 04 Griff | Petrol | stehend, 4 Wände, Brim 5 mm |
| 05 Tasterkappe | Signalorange | 100 % Infill |
| 06 Akzentring | Signalorange | flach, 100 % Infill |

## Montage

1. LEDs an den Stirnseiten anlöten und in den Kameraträger klipsen. Den Träger dann von hinten in den Kopf schieben.
2. XIAO-Stapel mit der Kamera voran in den Schacht setzen. Er liegt auf den Auflageleisten auf, USB-C zeigt nach oben zur Öffnung.
3. Status-LED in den Rückdeckel drücken, Kabel durch den Zapfen führen, Rückdeckel aufstecken.
4. Akkuhalter in den Griff schieben. Taster von außen einsetzen und die Kappe aufstecken. Wippschalter von unten einrasten.
5. Akzentring über den Zapfen schieben, dann den Kopf auf den Griff stecken, bis er einrastet.

## Kennwerte

| | Wert | Anforderung |
|---|---:|---|
| Höhe × Breite × Tiefe | 171,5 × 40 × 38,6 mm | ≤ 180 × 40 × 40 |
| Masse (geschätzt) | ≈ 115 g | ≤ 300 g |
| Schwerpunkt unter Kopfachse | 65 mm | ≤ 60 mm (offen) |

Offen ist außerdem: Die Status-LED steht hinten ca. 5,7 mm über.

## Lizenz

Abgeleitet von GliaX/Otoscope. Es gilt die Lizenz des Originalprojekts.
