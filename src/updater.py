"""
updater.py — Finds newer releases on GitHub and installs them.

Shortly after start and then once a day, the latest GitHub release is
compared with the running version.  When it is newer, ``available`` is
emitted: the tray shows a notification, and the flyout, tray menu and
settings offer to update.  Updating downloads the setup and starts it;
the setup closes the app, installs the new version and starts it again.
"""

import json
import logging
import os
import subprocess
import tempfile
import threading
import urllib.request

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices

from src.config import APP_VERSION, is_frozen

logger = logging.getLogger(__name__)

RELEASES_API = "https://api.github.com/repos/Muhammed-Coskun/PrayerTaskbar/releases/latest"
SETUP_ASSET = "PrayerTaskbar-Setup.exe"

_FIRST_CHECK_MS = 10_000
_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000
_HEADERS = {"User-Agent": "PrayerTaskbar", "Accept": "application/vnd.github+json"}

_instance: "Updater | None" = None


def version_tuple(text: str) -> tuple[int, ...]:
    """"v1.10.2" -> (1, 10, 2), so versions compare numerically."""
    parts = []
    for part in text.strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def fetch_latest_release() -> dict:
    """Return {"version", "page", "download"} of the latest GitHub release."""
    request = urllib.request.Request(RELEASES_API, headers=_HEADERS)
    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    asset = next((a for a in data.get("assets", []) if a.get("name") == SETUP_ASSET), None)
    return {
        "version": data.get("tag_name", "").lstrip("vV"),
        "page": data.get("html_url"),
        "download": asset.get("browser_download_url") if asset else None,
    }


class Updater(QObject):
    """Checks for updates in the background and installs them on request."""

    available = pyqtSignal(dict)   # a newer release was found
    progress = pyqtSignal(int)     # download progress in percent
    failed = pyqtSignal()          # download or start of the setup failed

    def __init__(self, current_version: str = APP_VERSION, parent=None) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self.update: dict | None = None
        self.installing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.check)

    def start(self) -> None:
        """Check soon after start, then once a day (installed app only)."""
        if not is_frozen():
            return
        QTimer.singleShot(_FIRST_CHECK_MS, self.check)
        self._timer.start(_CHECK_INTERVAL_MS)

    def check(self) -> None:
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self) -> None:
        try:
            release = fetch_latest_release()
        except Exception as e:
            logger.info(f"Update check failed: {e}")
            return
        if version_tuple(release["version"]) > version_tuple(self.current_version):
            logger.info(f"Update available: {release['version']}")
            self._emit(self.available, release)

    def _emit(self, signal, *args) -> None:
        try:
            signal.emit(*args)
        except RuntimeError:
            pass  # app is shutting down

    def install(self) -> None:
        """Download the new setup and start it (it updates and restarts the app)."""
        if self.installing or self.update is None:
            return
        url = self.update.get("download")
        if not url:
            # No setup attached to the release: let the user download it
            QDesktopServices.openUrl(QUrl(self.update.get("page") or ""))
            return
        self.installing = True
        self.progress.emit(0)
        threading.Thread(target=self._download_and_run, args=(url,), daemon=True).start()

    def _download_and_run(self, url: str) -> None:
        target = os.path.join(tempfile.gettempdir(), SETUP_ASSET)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "PrayerTaskbar"})
            with urllib.request.urlopen(request, timeout=30) as response, \
                    open(target + ".part", "wb") as file:
                total = int(response.headers.get("Content-Length") or 0)
                done = 0
                while chunk := response.read(256 * 1024):
                    file.write(chunk)
                    done += len(chunk)
                    if total:
                        self._emit(self.progress, done * 100 // total)
            os.replace(target + ".part", target)
            # Keep "Start with Windows" and the desktop icon as the user has them
            subprocess.Popen([target, "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                              "/MERGETASKS=!autostart,!desktopicon"])
            logger.info(f"Started update to {self.update['version']}")
        except Exception:
            logger.exception("Update failed")
            self.installing = False
            self._emit(self.failed)


def start(parent=None) -> Updater:
    """Create the app-wide updater and start the periodic checks."""
    global _instance
    _instance = Updater(parent=parent)
    _instance.available.connect(_remember)
    _instance.start()
    return _instance


def _remember(release: dict) -> None:
    if _instance is not None:
        _instance.update = release


def instance() -> "Updater | None":
    return _instance


def available_update() -> dict | None:
    """The newer release found so far, or None."""
    return _instance.update if _instance is not None else None
