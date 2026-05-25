# Gebetszeitleiste

Ein elegantes, modernes Windows-Taskleisten-Widget für Gebetszeiten, basierend auf den offiziellen Daten der Diyanet (Präsidium für Religionsangelegenheiten der Türkei). Das Widget nistet sich nahtlos in die Windows-Taskleiste ein und zeigt einen Live-Countdown zum nächsten Gebet.

## Features

- **Live-Countdown:** Zeigt direkt in der Taskleiste die Zeit bis zum nächsten Gebet an.
- **Modernes Win11-Flyout:** Ein Klick auf das Widget öffnet ein ansprechendes, rahmenloses Flyout mit allen Gebetszeiten des Tages und den nächsten religiösen Feiertagen.
- **Multimonitor-Support:** Wähle aus, auf welchem Bildschirm das Widget angezeigt werden soll.
- **Lokalisierung:** Unterstützt Deutsch, Englisch und Türkisch.
- **Diyanet API:** Holt sich automatisch die Gebetszeiten für jede beliebige Stadt per API.
- **Autostart:** Kann automatisch mit Windows gestartet werden.

## Installation / Nutzung

1. Lade die fertige `PrayerTaskbar.exe` aus dem `dist/` Ordner herunter.
2. Doppelklicke auf die `.exe` (es ist keine Installation von Python notwendig).
3. Klicke in der Taskleiste auf das Widget und dann auf das **Zahnrad (⚙)**.
4. Suche deine Stadt über die Suchleiste und wähle die gewünschte Sprache aus.
5. FERTIG!

## Entwickler (Selbst kompilieren)

Das Projekt basiert auf Python und PyQt6.

```bash
pip install -r requirements.txt
py -m PyInstaller --onefile --windowed --noconfirm --name PrayerTaskbar src/main.py
```
