"""
Configuration management for the Prayer Times Taskbar Widget.

Handles loading, saving, and accessing the application configuration.
Provides path utilities that are aware of both development and
PyInstaller-frozen environments.
"""

import json
import os
import sys


# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

def is_frozen() -> bool:
    """Check whether the application is running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False)

if is_frozen():
    SCRIPT_DIR: str = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""Resolved path of the main project directory (one level above src/)."""

CONFIG_FILE: str = os.path.join(SCRIPT_DIR, "config.json")
"""Full path to the configuration file."""

DATA_DIR: str = os.path.join(SCRIPT_DIR, "data")
"""Full path to the data/ subdirectory used for caches and local storage."""

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict = {
    "monitor_index": 0,
    "x_offset": 185,
    "language": "en",
    "city": "",
    "country": "",
    "location_id": None,
    "location_name": "",
    "data_source": "api",       # 'api' or 'excel'
    "excel_path": None,
    "autostart": False,
}
"""
Default values for every recognised configuration key.

When ``load_config`` reads an existing file it merges the stored values
on top of these defaults so that newly introduced keys always receive a
sensible initial value.
"""


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load configuration from *config.json* and merge with defaults.

    If the file does not exist or contains invalid JSON the pure defaults
    are returned instead.  Keys present in ``DEFAULT_CONFIG`` but missing
    from the file are filled in automatically.

    Returns:
        A dictionary with all configuration values.
    """
    config = DEFAULT_CONFIG.copy()

    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                stored = json.load(fh)
            config.update(stored)
        except (json.JSONDecodeError, OSError):
            # Fall back to defaults on corrupt / unreadable files.
            pass

    return config


def save_config(config: dict) -> None:
    """Persist *config* to *config.json*.

    The file is written with an indentation of two spaces and UTF-8
    encoding so that it remains human-readable and editable.

    Args:
        config: The configuration dictionary to save.
    """
    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2, ensure_ascii=False)


def get_data_dir() -> str:
    """Return the path to the *data/* directory, creating it if needed.

    Returns:
        Absolute path to the data directory.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR


def get_cache_path() -> str:
    """Return the path to the prayer-times cache file.

    The parent *data/* directory is created automatically when it does
    not yet exist.

    Returns:
        Absolute path to ``prayer_times_cache.json``.
    """
    return os.path.join(get_data_dir(), "prayer_times_cache.json")


    pass


def get_base_dir() -> str:
    """Return the base directory for bundled resources.

    When the application is frozen by PyInstaller this points to the
    temporary extraction folder (``sys._MEIPASS``).  In a normal Python
    environment it falls back to ``SCRIPT_DIR``.

    Returns:
        Absolute path to the base resource directory.
    """
    if is_frozen():
        # pylint: disable=protected-access
        return sys._MEIPASS  # type: ignore[attr-defined]
    return SCRIPT_DIR


def get_executable_path() -> str:
    """Return the path to the running executable.

    Used for registering the application in the Windows autostart
    registry.  When frozen the actual ``.exe`` path is returned;
    otherwise the path to the current Python interpreter is used.

    Returns:
        Absolute path to the executable.
    """
    if is_frozen():
        return sys.executable
    return sys.executable
