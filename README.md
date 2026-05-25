# PrayerTaskbar

A lightweight Windows taskbar widget that displays prayer times based on official Diyanet (Presidency of Religious Affairs of Turkey) data. The widget sits in the taskbar and provides a countdown to the next prayer.

## Features

- **Live Countdown:** Shows the remaining time until the next prayer directly in the taskbar.
- **Flyout Menu:** Clicking the widget opens a menu with the day's prayer times and upcoming religious holy days.
- **Multi-Monitor Support:** Choose which monitor's taskbar the widget appears on.
- **Language Support:** Available in English, German, and Turkish.
- **Diyanet API:** Fetches prayer times automatically for your selected city.
- **Autostart:** Option to launch automatically when Windows starts.

## How to Use

1. Download the pre-built `PrayerTaskbar.exe` from the `dist/` folder or releases page.
2. Run the `.exe` file (no Python installation required).
3. Click the widget in the taskbar and open the settings (⚙ icon).
4. Search for your city and select your preferred language.

## Build from Source

This project uses Python and PyQt6.

```bash
pip install -r requirements.txt
py -m PyInstaller --onefile --windowed --noconfirm --name PrayerTaskbar src/main.py
```
