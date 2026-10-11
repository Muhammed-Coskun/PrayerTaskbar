"""
main.py — Entry point for the Prayer Times Taskbar Widget.

Initializes the application, loads configuration and prayer data,
sets the language, and starts the Qt event loop.
"""

import sys
import os
import ctypes
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src.config import (load_config, get_cache_path, is_frozen, get_executable_path,
                        get_base_dir, migrate_legacy_files, USER_DIR, LOG_FILE)
from src.i18n import set_language
from src.data_loader import load_prayer_data
from src import autostart
from src import widget as widget_module
from src.theme import font
from src.tray import PrayerTray
from src.single_instance import notify_running_instance, InstanceServer

# Set up logging to a file next to the config (%APPDATA%\PrayerTaskbar when frozen)
os.makedirs(USER_DIR, exist_ok=True)
log_file = LOG_FILE

if getattr(sys, 'stdout', None) is None:
    sys.stdout = open(os.devnull, 'w')
if getattr(sys, 'stderr', None) is None:
    sys.stderr = open(os.devnull, 'w')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        # Keep the log small: at most 1 MB plus one old file
        RotatingFileHandler(log_file, 'a', maxBytes=1_000_000, backupCount=1, encoding='utf-8')
    ]
)

def create_start_menu_shortcut():
    """Create a Windows Start Menu shortcut so the app is searchable."""
    if not is_frozen():
        return
    exe_path = get_executable_path()
    start_menu = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs")
    shortcut_path = os.path.join(start_menu, "PrayerTaskbar.lnk")

    # Creates the shortcut, or repairs it when its target no longer exists
    # (e.g. after the app was moved); a shortcut to another existing copy
    # of the app is left alone
    vbs_path = os.path.join(os.environ["TEMP"], "create_prayer_shortcut.vbs")
    vbs_script = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
Set oFSO = CreateObject("Scripting.FileSystemObject")
Set oLink = oWS.CreateShortcut("{shortcut_path}")
If Not oFSO.FileExists(oLink.TargetPath) Then
    oLink.TargetPath = "{exe_path}"
    oLink.WorkingDirectory = "{os.path.dirname(exe_path)}"
    oLink.IconLocation = "{exe_path}"
    oLink.Save
End If
'''
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_script)
        subprocess.run(["cscript.exe", "//Nologo", vbs_path], creationflags=subprocess.CREATE_NO_WINDOW)
        os.remove(vbs_path)
    except Exception as e:
        logging.error(f"Failed to create start menu shortcut: {e}")

def main():
    """Application entry point."""
    
    # Force Windows to recognize this as a distinct app (fixes taskbar icon grouping)
    if os.name == 'nt':
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PrayerTaskbar.App.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    # The app lives in the taskbar and tray; only "Quit" should end it
    app.setQuitOnLastWindowClosed(False)
    # Windows 11 body text (also used by the tray menu and tooltips)
    app.setFont(font(14))

    # Only one instance: a second start just opens the running one's flyout
    if notify_running_instance():
        logging.info("Another instance is already running, exiting")
        sys.exit(0)

    migrate_legacy_files()
    config = load_config()
    set_language(config.get('language', 'en'))

    cache_path = get_cache_path()
    daily_times, hijri_dates, city_name = load_prayer_data(config, cache_path)

    if not daily_times:
        daily_times = {}
        hijri_dates = {}

    if city_name and not config.get('location_name'):
        config['location_name'] = city_name

    # Set the application-wide icon
    icon_path = os.path.join(get_base_dir(), 'app_icon.ico')
    icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
    app.setWindowIcon(icon)

    create_start_menu_shortcut()
    autostart.sync_path()

    prayer_widget = widget_module.PrayerWidget(daily_times, hijri_dates, config)
    prayer_widget.show()
    widget_module._active_widget = prayer_widget

    tray = PrayerTray(icon)
    tray.show()
    # Parented to the app so it stays alive as long as the app runs
    InstanceServer(tray.show_prayer_times, parent=app)

    # Don't lose a position change that is still waiting to be saved
    def on_quit():
        if widget_module._active_widget is not None:
            widget_module._active_widget.flush_pending_save()
    app.aboutToQuit.connect(on_quit)

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
