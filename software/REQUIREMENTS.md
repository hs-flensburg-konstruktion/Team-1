# Stand 2.0.0

Implementiert:
- Normaler Start im Offline-Modus, kein WLAN und kein Webserver.
- WLAN nur durch beim Start gehaltenen Auslöser: mindestens fünf Sekunden,
  danach loslassen. Jeder normale Neustart führt wieder zu Offline.
- Entprellter Fotoauslöser; ein Foto pro Druck; kein Wiederholen beim Halten;
  keine Aufnahme durch den Einschaltgriff; keine Warteschlange bei Beschäftigung.
- Status-LED: bereit = dauerhaft an, Aufnahme/Speicherung = aus, Erfolg = zwei
  kurze Blitze, anschließend wieder dauerhaft an. Fehler = keine Bereitschaft.
- Beleuchtung nur zur Offline-Aufnahme, mit Vorlauf, Nachlauf und unabhängigem
  Abschalt-Watchdog. Einzelbildpuffer und Kamera-Deinitialisierung zwischen Fotos.
- Maximale JPEG-Sensorauflösung und vorhandene NVS-/SD-Dateischutzlogik.
- WLAN-Livebild und Fotos direkt zum Rechner sowie manueller LED-Regler.
- SD-Fotoliste mit Seiten und Downloads in Firmware, Webansicht und Desktop-App.
- Auswahlimport, Fortschritt, Abbruch, Geräte-/Größen-/SHA-256-/JPEG-Prüfung,
  Schutz lokaler Originale und Wiederholung ohne doppelte identische Dateien.
- Aufbau ohne zusätzliche Kondensatoren; 10k/10k-Teiler, ADC-Mehrfachmessung
  mit Median und zeitlicher Entstörung.
- Ladeerkennung mit zwei geschützten ADC-Eingängen: Einzel-/Doppelblitz alle
  fünf Sekunden, Fotobestätigung mit Vorrang, kein Vollstatus allein aus LED AUS.
- DE/EN, angepasste Hilfe und USB-Einrichtung, getrennte App-Einstellungen.
- Getrennter Versionsordner, Mac-App, Firmwarepaket und Windows-Quellpaket.

Offen:
- Ladeabgriff und Ladeanzeige am Gerät prüfen; erster Test von Auslöser,
  Status-LED, Beleuchtung, Kamera, SD und WLAN-Import am 24.11.2026 abgeschlossen.
- Lichtstärke/Einregelzeit/Nachlauf und tatsächliche Schärfe prüfen.
- Stromaufnahme und Gehäusetemperatur vergleichen; keine Laufzeitgarantie.
- Windows-EXE auf Windows bauen und testen.

Nicht Bestandteil: USB-Laufwerksmodus, Akkuanzeige, Autofokus-Erweiterung,
automatisches Löschen von SD-Fotos oder automatische Speicherung eines WLAN-Starts.
