"""
autostart.py — "Start with Windows" via the per-user Run registry key.
"""

import logging
import os
import winreg

from src.config import get_executable_path, is_frozen

logger = logging.getLogger(__name__)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "PrayerTaskbar"


def _command() -> str:
    return f'"{get_executable_path()}"'


def is_enabled() -> bool:
    """True if the app is registered to start with Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
        return True
    except OSError:
        return False


def set_enabled(enabled: bool) -> bool:
    """Add or remove the autostart entry. Returns False if that failed."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                            winreg.KEY_SET_VALUE | winreg.KEY_READ) as key:
            if enabled:
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _command())
            elif is_enabled():
                winreg.DeleteValue(key, _VALUE_NAME)
        return True
    except OSError as e:
        logger.error(f"Autostart change failed: {e}")
        return False


def sync_path() -> None:
    """Repair an autostart entry whose exe no longer exists.

    Keeps autostart working after the app was moved or the build layout
    changed (e.g. from a single exe to a folder). An entry that points to
    another existing copy of the app is left alone.
    """
    if not is_frozen() or not is_enabled():
        return
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0,
                            winreg.KEY_SET_VALUE | winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, _VALUE_NAME)
            registered = str(value).strip().strip('"')
            if not os.path.isfile(registered):
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _command())
                logger.info(f"Autostart path repaired (was {registered})")
    except OSError as e:
        logger.error(f"Autostart path sync failed: {e}")
