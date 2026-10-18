# Digitales Glia-Otoskop – Hardware

**Stand:** 18.10.2026 · **Phase:** Low-Budget-Prototyp (V1)

## Ziel

Kostengünstiger Versuchsaufbau auf Grundlage des [Open-Source-Glia-Otoskops](https://github.com/GliaX/Otoscope). Für V1 wird die **mit dem Seeed XIAO ESP32-S3 Sense gelieferte Kamera** verwendet. Getestet werden Nahfokus, Beleuchtung, JPEG-Aufnahmen, microSD-Speicherung, WLAN-Livebild und Akkubetrieb mit USB-C-Ladung.

Ein integriertes Display und eine höherwertige Kamera sind **optionale Erweiterungen**.

## Einkaufsliste – Prototyp V1

Bruttopreise in EUR (Stand: 18.10.2026), **ohne Versand**. Mengen für einen Prototypen.

| Pos. | Bauteil / Zweck | Menge | Lieferant / Bestelllink | Stückpreis | Gesamtpreis |
|---:|---|---:|---|---:|---:|
| 1 | **Seeed XIAO ESP32-S3 Sense (ohne Header)** – inkl. Kamera (bei Reichelt als **OV3660, 3 MP** gelistet), Erweiterungsplatine, WLAN, microSD-Steckplatz und USB-C | 1 Set | [Reichelt – XIAO ESP32-S3 Sense](https://www.reichelt.de/de/de/shop/produkt/xiao_esp32s3_sense_wifi_bt_kamera_ov3660_ohne_header-358353) | 15,40 € | 15,40 € |
| 2 | **XTAR 14500 Li-Ion-Akku**, 3,6 V / 800 mAh, mit Schutzschaltung | 1 | [Reichelt – XTAR 14500](https://www.reichelt.de/de/de/shop/produkt/industriezelle_li-ion_14500_3_6_v_800_mah_button_top-253362) | 5,70 € | 5,70 € |
| 3 | **Batteriehalter für 1 × AA/14500**, mit Lötfahnen | 1 | [Reichelt – AA-Batteriehalter](https://www.reichelt.de/de/de/shop/produkt/batteriehalter_fuer_1_mignonzelle_aa_loetfahne-8434) | 0,31 € | 0,31 € |
| 4 | **Weiße SMD-LED, Bauform 1206, 120°** – Beleuchtung | 4 | [Reichelt – 1206W2C-KHC-B](https://www.reichelt.de/de/de/shop/produkt/led_smd_1206_weiss_560_mcd_120_-361551) | 0,15 € | 0,60 € |
| 5 | **N-MOSFET AO3400A, Logic-Level, SOT-23** – gemeinsames Schalten/Dimmen der vier LEDs | 1 | [Reichelt – AO3400A](https://www.reichelt.de/de/de/shop/produkt/mosfet_n-ch_30v_5_7a_0_018r_sot-23-166490) | 0,18 € | 0,18 € |
| 6 | **Marquardt-Wippschalter 1801.1102**, rastend EIN/AUS – Hauptschalter | 1 | [Reichelt – Wippschalter](https://www.reichelt.de/de/de/shop/produkt/wippschalter_1x_aus_schwarz-36768) | 1,99 € | 1,99 € |
| | **Gesamtsumme V1 (ohne Versand)** | | | | **24,18 €** |

**Bereits vorhanden / nicht Teil der Bestellung:** microSD-Karte, USB-C-Daten-/Ladekabel, vier LED-Vorwiderstände, Gate-Widerstand und Gate-Pulldown, Foto-Taster, Kabel/Lötmaterial sowie Filament für ein 3D-gedrucktes Gehäuse. Die Beleuchtung wird in V1 **zunächst mit 3,3 V ohne zusätzlichen Spannungswandler** getestet.

## Optionale Erweiterungen

| Bauteil | Menge | Lieferant / Link | Mehrkosten |
|---|---:|---|---:|
| Welch-Allyn-Ohrtrichter, wiederverwendbar, 2,5 mm | 1 | [Welch Allyn – 24302-U](https://shop.welchallyn.de/ersatzteile-und-zubehor/ohrtrichter-spekula) | 3,71 € |
| Welch-Allyn-Ohrtrichter, wiederverwendbar, 4,0 mm | 1 | [Welch Allyn – 24304-U](https://shop.welchallyn.de/ersatzteile-und-zubehor/ohrtrichter-spekula) | 2,99 € |
| IPS-Farbdisplay, 1,3 Zoll, ST7789, 240 × 240 Pixel | 1 | [Reichelt – Joy-IT](https://www.reichelt.de/de/de/shop/produkt/entwicklerboards_-_display_lcd_1_3_240_x_240_pixel_st7789-296742) | 7,20 € |
| 5-MP-OV5640-Kamera mit Autofokus (späterer Austausch) | 1 | [Reichelt – XIAO 5-MP-Kamera](https://www.reichelt.de/de/de/shop/produkt/xiao_-_kamera_5mp_fuer_xiao_esp32se_sense-379751) | ca. 12,10 € |
| Makrolinse / verstellbarer Objektivhalter, falls benötigt | nach Test | noch festzulegen | offen |

## Kostenübersicht

| Ausbaustufe | Warenwert ohne Versand |
|---|---:|
| **V1 – Grundaufbau ohne Display und Ohrtrichter** | **24,18 €** |
| V1 + beide optionalen Ohrtrichter | 30,88 € |
| V1 + Vorschau-Display | 31,38 € |
| V1 + Display + beide Ohrtrichter | 38,08 € |
| V1 + Display + späteres 5-MP-Kamera-Upgrade | ca. 43,48 € |

> **Status:** Vorläufige Stückliste für einen Hochschul-Prototyp. Keine Freigabe zur Untersuchung von Patienten.

## Referenzen

- [GliaX/Otoscope – GitHub](https://github.com/GliaX/Otoscope)
- [Seeed XIAO ESP32-S3 Sense – Dokumentation](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)
