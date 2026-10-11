# PrayerTaskbar

A lightweight Windows taskbar widget that displays prayer times based on official Diyanet (Presidency of Religious Affairs of Turkey) data. The widget sits in the taskbar and provides a countdown to the next prayer.

## Features

- **Live Countdown:** Shows the remaining time until the next prayer directly in the taskbar.
- **Windows 11 Design:** The prayer times flyout uses the native acrylic background, rounded corners and shadow, and the settings look like the Windows 11 Settings app. Light/dark mode and the accent color follow your Windows settings.
- **Flyout:** Clicking the widget shows today's prayer times, the next prayer with its countdown, and the next religious holy day (with Gregorian and Hijri dates).
- **Tray Icon:** The app shows up in the notification area, where you can open the prayer times, the settings, or quit it.
- **Multi-Monitor Support:** Choose which monitor's taskbar the widget appears on.
- **Language Support:** Available in English, German, and Turkish.
- **Diyanet API:** Fetches prayer times automatically for your selected city.
- **Autostart:** Option to launch automatically when Windows starts.

## How to Use

1. Download the latest release and extract the `PrayerTaskbar` folder.
2. Run `PrayerTaskbar.exe` (no Python installation required).
3. Click the widget in the taskbar and open the settings (⚙ icon), or use the tray icon.
4. Search for your city and select your preferred language.

To move the widget along the taskbar, use the arrows in the settings or drag it with the middle mouse button.

## Build from Source

This project uses Python and PyQt6.

```bash
pip install -r requirements.txt
pyinstaller --noconfirm PrayerTaskbar.spec
```

The app is built into `dist/PrayerTaskbar/`; distribute the whole folder.

## Credits

Special thanks to [Abdus.dev Diyanet API](https://prayertimes.api.abdus.dev/) for providing the reliable and fast JSON API wrapper for Diyanet prayer times.
