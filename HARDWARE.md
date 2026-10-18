# Digitales Glia-Otoskop – Hardware (Machbarkeitsstudie)

**Stand:** 18.10.2026 · **Phase:** Low-Budget-Prototyp (V1)

## Ziel

Ein kostengünstiger Versuchsaufbau auf Grundlage des [Open-Source-Glia-Otoskops](https://github.com/GliaX/Otoscope). Zunächst verwenden wir **nur die beim Seeed XIAO ESP32-S3 Sense mitgelieferte Kamera**. Untersucht werden Nahfokus, Ausleuchtung, JPEG-Aufnahmen, lokale Bildspeicherung, WLAN-Livebild und Akkubetrieb mit USB-C-Ladung.

Ein integriertes Display und eine höherwertige Kamera sind **optionale Erweiterungen**.

## Einkaufsliste – Prototyp V1

Alle Beträge sind **Bruttopreise in EUR (Recherche: 18.10.2026)**, **ohne Versand**. Die Mengen beziehen sich auf einen Prototypen.

| Pos. | Bauteil / Zweck | Menge | Lieferant / Bestelllink | Einzelpreis | Gesamt |
|---:|---|---:|---|---|---:|
| 1 | **Seeed XIAO ESP32-S3 Sense (ohne Header)** – inkl. Kamera (bei Reichelt als **OV3660, 3 MP** gelistet), Erweiterungsplatine, WLAN, microSD-Steckplatz, USB-C und LiPo-Ladefunktion | 1 Set | [Reichelt – XIAO ESP32S3 SEN](https://www.reichelt.de/de/de/shop/produkt/xiao_esp32s3_sense_wifi_bt_kamera_ov3660_ohne_header-358353) | 15,40 € | 15,40 € |
| 2 | **XTAR 14500 Li-Ion-Akku, 3,6 V / 800 mAh**, mit Schutzschaltung | 1 | [Reichelt – XTAR 14500](https://www.reichelt.de/de/de/shop/produkt/industriezelle_li-ion_14500_3_6_v_800_mah_button_top-253362) | 5,70 € | 5,70 € |
| 3 | **Weiße SMD-LED, 1206, 120°** – Ausleuchtung des Gehörgangs | 4 | [Reichelt – 1206W2C-KHC-B](https://www.reichelt.de/de/de/shop/produkt/led_smd_1206_weiss_560_mcd_120_-361551) | 0,15 € | 0,60 € |
| 4 | **N-MOSFET 2N7000, TO-92** – LED-Schaltung/Helligkeitsregelung, Eignung anhand des Gesamtstroms prüfen | 1 | [Reichelt – 2N 7000](https://www.reichelt.de/de/de/shop/produkt/mosfet_n-ch_60v_0_115a_0_4w_1_7r_to-92-41141) | 0,09 € | 0,09 € |
| 5 | **Mini-Schiebeschalter** – Akkutrennung / Ein-Aus | 1 | [Reichelt – NK 236](https://www.reichelt.de/de/de/shop/produkt/subminiatur-schiebeschalter_1x_um_gerade-27898) | 1,47 € | 1,47 € |
| 6 | **Lochrasterplatine, 60 × 40 mm** – Aufbau der Beleuchtungs- und Bedienelektronik | 1 | [Reichelt – LR-DS-46](https://www.reichelt.de/de/de/shop/produkt/lochrasterplatine_doppelseitig_60_x_40_mm-319112) | 1,20 € | 1,20 € |
| 7 | **3D-gedrucktes Testgehäuse**, Kamera-/LED-Halterung und späterer Spekulumadapter | 1 Satz | Eigenfertigung mit vorhandenem Filament; CAD-Basis: [GliaX/Otoscope](https://github.com/GliaX/Otoscope) | 0,00 €¹ | 0,00 €¹ |
| 8 | **USB-C-Daten-/Ladekabel** – Flashen und Laden | 1 | Vorhanden | 0,00 €¹ | 0,00 €¹ |
| 9 | **Batteriehalter für 1 × AA/14500**, mit Lötfahnen (Passung der geschützten 14500-Zelle noch prüfen) | 1 | [Reichelt – AA-Batteriehalter](https://www.reichelt.de/de/de/shop/produkt/batteriehalter_fuer_1_mignonzelle_aa_loetfahne-8434) | 0,31 € | 0,31 € |
| | **Gesamtsumme V1 (ohne Versand)** | | | | **24,16 €** |

¹ **Kein zusätzlicher Einkauf angenommen**. Filamentverbrauch, Arbeitszeit, Werkzeug und Ausschuss sind nicht eingepreist.

**Aus vorhandenem Bestand bzw. separat bereitzustellen:** Eine kompatible **microSD-Karte** für die lokale Bildspeicherung sowie **LED-Vorwiderstände (je LED einzeln), Gate-Pulldown-Widerstand, Taster für die Fotoaufnahme, Kabel und geeignete Steck-/Lötverbindungen**. Diese Teile sind **nicht in den 24,16 € enthalten**. Ohne microSD-Karte ist die geplante lokale Speicherung nicht verfügbar.

## Optionale Erweiterungen

| Bauteil / Zweck | Menge | Lieferant / Link | Mehrkosten |
|---|---:|---|---:|
| **Welch-Allyn-Universal-Ohrtrichter, wiederverwendbar, 2,5 mm** – Passform-/Sichtfeldtest | 1 | [Welch Allyn – 24302-U](https://shop.welchallyn.de/ersatzteile-und-zubehor/ohrtrichter-spekula) | 3,71 € |
| **Welch-Allyn-Universal-Ohrtrichter, wiederverwendbar, 4,0 mm** – Passform-/Sichtfeldtest | 1 | [Welch Allyn – 24304-U](https://shop.welchallyn.de/ersatzteile-und-zubehor/ohrtrichter-spekula) | 2,99 € |
| **1,3-Zoll-IPS-Farbdisplay, ST7789, 240 × 240 Pixel, SPI** – Live-Vorschau am Gerät | 1 | [Reichelt – Joy-IT DEBO2 LCD240X240](https://www.reichelt.de/de/de/shop/produkt/entwicklerboards_-_display_lcd_1_3_240_x_240_pixel_st7789-296742) | 7,20 € |
| **5-MP-OV5640-Kamera mit Autofokus** – späterer Ersatz der mitgelieferten Kamera | 1 | [Reichelt – XIAO 5MP-Kamera](https://www.reichelt.de/de/de/shop/produkt/xiao_-_kamera_5mp_fuer_xiao_esp32se_sense-379751) | ca. 12,10 €² |
| **Zusätzliche Makrolinse / verstellbarer Objektivhalter** – falls für den Nahfokus erforderlich | nach Test | Noch festzulegen | offen |

**Hinweis:** Die mechanische Kompatibilität der angegebenen wiederverwendbaren Welch-Allyn-Ohrtrichter mit dem Glia-Anschluss muss vor dem Kauf geprüft werden. Das Glia-Projekt verwendet unter anderem andere Spekulum-Ausführungen. Der benötigte Adapter ist daher noch zu konstruieren.

² Lieferumfang des Sense-Sets vor der Bestellung prüfen: Je nach Revision kann bereits ein anderes Kameramodul beiliegen. Ein separates Kamera-Upgrade ist ausdrücklich **nicht für V1** vorgesehen.

## Kostenübersicht

| Ausbaustufe | Warenwert ohne Versand |
|---|---:|
| **V1 – Grundaufbau mit mitgelieferter Kamera, ohne Display/Ohrtrichter** | **24,16 €** |
| V1 + beide optionalen Ohrtrichter | 30,86 € |
| V1 + Vorschau-Display | 31,36 € |
| V1 + Display + beide Ohrtrichter | 38,06 € |
| V1 + Display + späteres 5-MP-Kamera-Upgrade (ohne Ohrtrichter) | ca. 43,46 € |

**Nicht enthalten:** Versandkosten (für die V1-Bestellung mindestens die Lieferanten Reichelt und EREMIT), möglicherweise zusätzlich zu beschaffende Kleinteile aus dem Bestand, Filamentkosten und Werkzeug.

## Technische Prüfpunkte

1. **Optik:** Fokus und Bildwinkel mit mitgelieferter Kamera bei kurzen Arbeitsabständen prüfen. Erst danach über Makrolinse oder OV5640 entscheiden.
2. **Beleuchtung:** Vier weiße LEDs mit **je einem Vorwiderstand** betreiben; Helligkeit, Ausleuchtung, Reflexionen und Erwärmung untersuchen.
3. **Akku:** Der XIAO besitzt eine Ladefunktion für eine LiPo-Zelle über USB-C. Akkupolarität, Ladeverhalten und Verschaltung des Ein-Aus-Schalters vor Inbetriebnahme prüfen.
4. **Speicherung/WLAN:** JPEG-Aufnahmen auf einer separat bereitgestellten microSD-Karte speichern; Livebild über WLAN im Browser anzeigen.
5. **Mechanik:** Erst optischen Prüfstand aufbauen, danach kompaktes 3D-gedrucktes Gehäuse und Spekulumadapter entwickeln.
6. **Optionales Display:** Vor Einbau freie GPIOs, Schnittstellen und gleichzeitigen Kamera-/SD-Betrieb prüfen.
7. **Sicherheit:** Der Versuchsaufbau ist **kein freigegebenes Medizinprodukt** und darf ohne entsprechende Prüfung nicht an Patienten eingesetzt werden.

## Referenzen

- [Seeed XIAO ESP32-S3 Sense – Dokumentation](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)
- [GliaX/Otoscope – Open-Source-Projekt](https://github.com/GliaX/Otoscope)

> **Status:** Vorläufige Einkaufsliste für die Machbarkeitsstudie. Preise, Lieferbarkeit und Kompatibilität vor Bestellung bestätigen.
