# Verdrahtung für Otoskop 2.0.0 ohne externe Kondensatoren

Der [aktuelle Schaltplan](Otoskop_2.0.0_Testaufbau.pdf) enthält alle Anschlüsse.
Die Originalmodule XIAO/Sense bleiben vollständig bestückt. C1-C4 der früheren
externen Schaltung entfallen; keine Bauteile von den Originalmodulen entfernen.

## Versorgung, Auslöser und Status-LED

```text
Halter + ---------- S1 EIN/AUS -------- XIAO BAT+ und LED-Ring +
Halter - ------------------------------ XIAO BAT- / GND
XIAO D3 / GPIO4 ---- S2 Schließer ------ GND
XIAO D4 / GPIO5 ---- R9 1 kOhm --- D5 Anode; D5 Kathode --- GND
XIAO D0 / GPIO1 ---- R5 100 Ohm -------- AO3400A Gate / Pin 1
Q1 Gate ------------ R6 100 kOhm ------- GND
Q1 Source / Pin 2 ---------------------- GND
Q1 Drain / Pin 3 ----------------------- Kathoden der vier Beleuchtungs-LEDs
LED-Ring + -------- je 220 Ohm --------- je LED-Anode
```

Jede Beleuchtungs-LED braucht ihren eigenen 220-Ohm-Widerstand. Der Taster ist
nicht rastend und nutzt den internen Pull-up des GPIO4. Die äußere weiße LED
wird aktiv HIGH betrieben. Die LED wird nicht direkt an die Akkuspannung gelegt.
Akku-, Masse-, LED- und Messleitungen kurz und direkt führen. Die Stabilität der
Versorgung muss insbesondere beim Starten der Kamera und bei WLAN geprüft werden.

## Ladeerkennung ohne Kondensatoren

```text
U1.CHG0-K / nCHG -- R10 10 kOhm --+-- XIAO D5 / GPIO6 / ADC1
                                +-- R11 10 kOhm -- GND

XIAO 5V / VBUS ---- R12 10 kOhm --+-- XIAO D1 / GPIO2 / ADC1
                                +-- R13 10 kOhm -- GND
```

R10-R13 jeweils 1 %, mindestens 0,125 W. Keine zusätzlichen Kondensatoren.
Die ADC-Pins werden ohne internen Pull-up/-down betrieben. Die Widerstände
müssen erhalten bleiben; 5 V niemals direkt an einen GPIO anschließen.

Der Ladeabgriff ist die Kathode der roten Onboard-LED CHG0 auf der Seite des
Ladebausteins SGM40567, nicht die 5-V-Anode. Hier ist eine feine Lötverbindung
am Board nötig. Vor dem Löten die konkrete Platinenrevision und die Verbindung
prüfen. Die vorhandene rote LED und ihr Vorwiderstand U1.R11 bleiben bestückt.
Dieser U1.R11 ist nicht der externe Widerstand R11 im obigen Plan.

Bei USB 5 V liegen ungefähr 2,5 V am USB-ADC. Am Lade-ADC ist der inaktive
Pegel niedriger: Die vorhandene rote LED und ihr 10-kOhm-Vorwiderstand belasten
das Signal zusammen mit dem externen 10k/10k-Teiler. Etwa 1 V ist dort ein
plausibler Rechenwert; der reale Wert muss am Board geprüft werden.
Die Firmware wertet bis 400 mV als aktiv und ab 650 mV als inaktiv. Dazwischen
bleibt der Pegel zunächst unbestimmt. Sie verwirft eine erste ADC-Wandlung,
nutzt den Median aus fünf Messungen und entstört Pegeländerungen zeitlich.
Deshalb zusammen mit diesem Plan die aktualisierte Firmware 2.0.0 installieren.
Die ältere Ausführung mit 100-kOhm-Teilern nicht mit diesen Werten mischen.

D5 als Bauteilnummer der weißen LED und XIAO D5 als Padname sind verschiedene
Bezeichnungen: XIAO D5 ist GPIO6, die weiße Status-LED hängt an XIAO D4/GPIO5.
D1/GPIO2 ist USB-ADC. D2/GPIO3 wird wegen seiner Boot-Funktion vermieden.
GPIO21 und D8-D10 bleiben für die SD-Karte reserviert.

## Anzeige und USB-Betrieb

Im Akkubetrieb: Status dauerhaft an = bereit, aus während Aufnahme/Speicherung,
zweimal blinken nach erfolgreichem Speichern. Beim Laden: ein Blitz alle fünf
Sekunden; nach erkanntem Abschluss zwei Blitze alle fünf Sekunden. Die
Fotobestätigung hat Vorrang. Ohne eindeutigen Ladeverlauf kein Vollstatus.

S1 trennt nur den Akku. Bei angeschlossenem USB kann das Gerät auch mit S1 AUS
weiterlaufen. Laden benötigt S1 EIN und eingesetzte Zelle; zum Neustart unter
USB RESET verwenden. Die Anzeige ersetzt keine unabhängige Erkennung der
Akkuanwesenheit oder Schalterstellung. Ein realer Lade-/Dauerbetriebtest steht aus.
