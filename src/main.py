"""
main.py — Entry point for the Prayer Times Taskbar Widget.

Initializes the application, loads configuration and prayer data,
sets the language, and starts the Qt event loop.
"""

import sys
import os
import logging

import sys
import os
import logging
from src.config import is_frozen, SCRIPT_DIR

# Set up logging to a file in the same directory as the executable/script
log_file = os.path.join(SCRIPT_DIR, "widget_debug.log")

# On Windows with PyInstaller --windowed, sys.stdout and sys.stderr are None.
# This causes print() or logging.StreamHandler() to crash.
# Redirect them to devnull to prevent crashes from 3rd party libs.
if getattr(sys, 'stdout', None) is None:
    sys.stdout = open(os.devnull, 'w')
if getattr(sys, 'stderr', None) is None:
    sys.stderr = open(os.devnull, 'w')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, 'a', 'utf-8')
        # We REMOVED StreamHandler because sys.stderr is None in --windowed mode,
        # which crashes the logger and causes infinite recursion if redirected.
    ]
)

# Only suppress UpdateLayeredWindowIndirect in the log output via a filter
class SuppressWin32Filter(logging.Filter):
    def filter(self, record):
        return "UpdateLayeredWindowIndirect failed" not in record.getMessage()

logging.getLogger().addFilter(SuppressWin32Filter())

from PyQt6.QtWidgets import QApplication

from src.config import load_config, get_cache_path
from src.i18n import set_language
from src.data_loader import load_prayer_data
from src.holy_days import is_ramadan_today
from src import widget as widget_module


def main():
    """Application entry point."""
    config = load_config()

    # Set language from config (default: English)
    set_language(config.get('language', 'en'))

    # Load prayer data (API cache → Excel fallback)
    cache_path = get_cache_path()
    daily_times, hijri_dates, city_name = load_prayer_data(config, cache_path)

    if not daily_times:
        # No data at all — still start so user can open settings
        daily_times = {}
        hijri_dates = {}

    # Update city name in config if loaded from Excel
    if city_name and not config.get('location_name'):
        config['location_name'] = city_name

    # Start Qt application
    app = QApplication(sys.argv)

    prayer_widget = widget_module.PrayerWidget(daily_times, hijri_dates, config)
    prayer_widget.show()
    widget_module._active_widget = prayer_widget

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
