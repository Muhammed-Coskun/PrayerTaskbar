<div align="center">

[English](README.md) · [Türkçe](README.tr.md) · **Deutsch**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./.github/assets/logo-white.png">
  <img src="./.github/assets/logo.png" alt="PrayerTaskbar-Logo" title="PrayerTaskbar-Logo" width="140"/>
</picture>

# PrayerTaskbar

### Gebetszeiten direkt in deiner Windows-Taskleiste
PrayerTaskbar zeigt neben der Uhr, wie lange es bis zum nächsten Gebet dauert. Ein Klick öffnet die heutigen Gebetszeiten und den nächsten Feiertag.

[![Windows 11](https://img.shields.io/badge/Windows-11-0078D4?labelColor=27303D)](https://www.microsoft.com/windows/windows-11)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?labelColor=27303D&logo=python&logoColor=FFFFFF)](https://www.python.org)
[![PyQt](https://img.shields.io/badge/PyQt-6-41CD52?labelColor=27303D&logo=qt&logoColor=FFFFFF)](https://www.riverbankcomputing.com/software/pyqt/)
[![Lizenz: MIT](https://img.shields.io/badge/license-MIT-27303D?labelColor=27303D&color=0877d2)](/LICENSE)

<img src="./.github/assets/prayer-times.png" alt="Die heutigen Gebetszeiten über der Taskleiste" width="380"/>

## Download

[![Für Windows herunterladen](https://img.shields.io/badge/Herunterladen-Windows-0078D4?labelColor=0067C0&color=005A9E)](https://github.com/Muhammed-Coskun/PrayerTaskbar/releases/latest/download/PrayerTaskbar-Setup.exe)

*Starte das Setup, danach erscheint PrayerTaskbar in deiner Taskleiste.*<br>
*Zeigt Windows eine SmartScreen-Warnung, klicke auf „Weitere Informationen“ und dann auf „Trotzdem ausführen“.*<br>
*PrayerTaskbar ist Open Source. Jedes Setup wird von [GitHub Actions](https://github.com/Muhammed-Coskun/PrayerTaskbar/actions/workflows/release.yml) aus diesem Code gebaut.*

## Funktionen

<div align="left">

- **Countdown in der Taskleiste:** Die Zeit bis zum nächsten Gebet, direkt neben der Uhr. In den letzten 15 Minuten wird sie rot.
- **Der Tag auf einen Blick:** Ein Klick zeigt alle heutigen Gebetszeiten, das nächste Gebet ist hervorgehoben.
- **Nächster Feiertag:** Sieh, wie viele Tage es noch bis zum nächsten Feiertag sind, etwa Ramadan oder Bayram. Die Daten folgen dem Kalender von Diyanet.
- **Deine Stadt:** Such nach deiner Stadt, die Gebetszeiten kommen von Diyanet.
- **Gemacht für Windows 11:** Passt sich dem hellen und dunklen Modus und deiner Akzentfarbe an.
- **Drei Sprachen:** Englisch, Türkisch und Deutsch.
- **Automatische Updates:** Neue Versionen installieren sich beim Start von selbst. Schaltest du das aus, sagt dir die App nur Bescheid. Jedes Update wird vor der Installation mit seiner Prüfsumme auf GitHub verglichen.

</div>

## Einstellungen

Wähle deine Stadt oder importiere eine Gebetszeiten-Tabelle von Diyanet.

<img src="./.github/assets/settings-location.png" alt="Einstellungen zum Ort" width="600"/>

Wähle den Bildschirm und verschiebe das Widget in der Taskleiste.

<img src="./.github/assets/settings-taskbar.png" alt="Einstellungen zur Taskleiste" width="600"/>

Ändere die Sprache und starte PrayerTaskbar mit Windows.

<img src="./.github/assets/settings-general.png" alt="Allgemeine Einstellungen" width="600"/>

### Datenschutz

PrayerTaskbar hat kein Konto, keine Werbung und kein Tracking. Die App verbindet sich nur mit:

<div align="left">

- **prayertimes.api.abdus.dev**, um die Gebetszeiten für deine Stadt zu laden
- **github.com**, um nach Updates zu suchen und sie herunterzuladen

</div>

Deine Einstellungen bleiben auf deinem PC in `%APPDATA%\PrayerTaskbar`.

### Aus dem Quellcode bauen

<div align="left">

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m src.main
```

Für die App und das Setup führe `.venv\Scripts\pyinstaller --noconfirm PrayerTaskbar.spec` und danach `ISCC installer.iss` aus [Inno Setup](https://jrsoftware.org/isinfo.php) aus. Der [Release-Workflow](.github/workflows/release.yml) macht dasselbe und kompiliert zusätzlich den Bootloader von PyInstaller aus dem Quellcode.

</div>

### Danke

Gebetszeiten von [Diyanet](https://namazvakitleri.diyanet.gov.tr), bereitgestellt über die [abdus.dev Diyanet API](https://prayertimes.api.abdus.dev/)

### Lizenz

Veröffentlicht unter der [MIT-Lizenz](/LICENSE)

</div>
