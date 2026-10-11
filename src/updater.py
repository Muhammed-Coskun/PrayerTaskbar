"""
updater.py — Finds newer releases on GitHub and installs them.

Each time the app starts (installed app only) and whenever "Check for
updates" is clicked, the latest GitHub release is compared with the
running version.  A newer one is offered in the flyout, the tray menu and
the settings.  When the check at start finds one, it is installed right
away if automatic updates are on; otherwise the tray shows a
notification.  Installing downloads the setup, starts it and closes the
app; the setup replaces the app and starts the new version.
"""

import json
import logging
import os
import subprocess
import tempfile
import threading
import time
import urllib.request
from datetime import datetime

from PyQt6.QtCore import QCoreApplication, QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices

from src.config import APP_VERSION, is_frozen

logger = logging.getLogger(__name__)

RELEASES_API = "https://api.github.com/repos/Muhammed-Coskun/PrayerTaskbar/releases/latest"
SETUP_ASSET = "PrayerTaskbar-Setup.exe"

_FIRST_CHECK_MS = 10_000
_RETRY_MS = 60_000      # right after logging in, the network may not be up yet
_RETRIES = 3
_MIN_CHECK_MS = 2_000   # keep "Checking for updates…" on screen long enough to read
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
    """Checks for updates in the background and installs them."""

    available = pyqtSignal(dict)   # a newer release was found
    notify = pyqtSignal(dict)      # tell the user about it (found at start, not installed)
    state_changed = pyqtSignal()   # a check started or finished
    progress = pyqtSignal(int)     # download progress in percent
    failed = pyqtSignal()          # download or start of the setup failed
    _checked = pyqtSignal(object, bool)  # (newer release or None, failed), to the UI thread
    _downloaded = pyqtSignal(str)        # path of the downloaded setup, to the UI thread

    def __init__(self, current_version: str = APP_VERSION, parent=None) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self.update: dict | None = None
        self.installing = False
        self.checking = False
        self.check_failed = False
        self.last_checked: datetime | None = None
        self.automatic = True   # install an update found at start without asking
        self._at_start = False  # the running check is the one at start
        self._installing_automatically = False
        self._check_started = 0.0
        self._retries_left = _RETRIES
        self._retry_timer = QTimer(self)
        self._retry_timer.setSingleShot(True)
        self._retry_timer.setInterval(_RETRY_MS)
        self._retry_timer.timeout.connect(self._check_at_start)
        self._checked.connect(self._on_checked)
        self._downloaded.connect(self._run_setup)
        self.failed.connect(self._on_install_failed)

    def start(self, automatic: bool = True) -> None:
        """Check once, shortly after the app started (installed app only)."""
        self.automatic = automatic
        if is_frozen():
            QTimer.singleShot(_FIRST_CHECK_MS, self._check_at_start)

    def _check_at_start(self) -> None:
        self.check(at_start=True)

    def check(self, at_start: bool = False) -> None:
        """Look for a newer release in the background (also used by the button)."""
        if self.checking or self.installing:
            return
        self.checking = True
        self._at_start = at_start
        self._check_started = time.monotonic()
        self.state_changed.emit()
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self) -> None:
        try:
            release = fetch_latest_release()
        except Exception as e:
            logger.info(f"Update check failed: {e}")
            self._emit(self._checked, None, True)
            return
        newer = version_tuple(release["version"]) > version_tuple(self.current_version)
        self._emit(self._checked, release if newer else None, False)

    def _on_checked(self, release, failed: bool) -> None:
        # A quick answer would only flash "Checking for updates…"
        elapsed_ms = (time.monotonic() - self._check_started) * 1000
        wait_ms = max(0, int(_MIN_CHECK_MS - elapsed_ms))
        QTimer.singleShot(wait_ms, lambda: self._finish_check(release, failed))

    def _finish_check(self, release, failed: bool) -> None:
        self.checking = False
        self.check_failed = failed
        if not failed:
            self.last_checked = datetime.now()
            self._retry_timer.stop()
        if release is not None:
            logger.info(f"Update available: {release['version']}")
            self.update = release
            self.available.emit(release)
        self.state_changed.emit()

        if not self._at_start:
            return
        self._at_start = False
        if failed:
            if self._retries_left > 0:
                self._retries_left -= 1
                self._retry_timer.start()
        elif release is not None:
            if self.automatic:
                self.install(automatically=True)
            else:
                self.notify.emit(release)

    def _emit(self, signal, *args) -> None:
        try:
            signal.emit(*args)
        except RuntimeError:
            pass  # app is shutting down

    def install(self, automatically: bool = False) -> None:
        """Download the new setup and start it (it updates and restarts the app)."""
        if self.installing or self.update is None:
            return
        url = self.update.get("download")
        if not url:
            # No setup attached to the release: the user has to download it
            if automatically:
                self.notify.emit(self.update)
            else:
                QDesktopServices.openUrl(QUrl(self.update.get("page") or ""))
            return
        self.installing = True
        self._installing_automatically = automatically
        self.progress.emit(0)
        threading.Thread(target=self._download, args=(url,), daemon=True).start()

    def _download(self, url: str) -> None:
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
        except Exception:
            logger.exception("Update download failed")
            self.installing = False
            self._emit(self.failed)
            return
        self._emit(self._downloaded, target)

    def _run_setup(self, target: str) -> None:
        # Automatic updates show no setup window at all
        mode = "/VERYSILENT" if self._installing_automatically else "/SILENT"
        try:
            # Keep "Start with Windows" and the desktop icon as the user has them
            subprocess.Popen([target, mode, "/SUPPRESSMSGBOXES", "/NORESTART",
                              "/MERGETASKS=!autostart,!desktopicon"])
        except OSError:
            logger.exception("Could not start the setup")
            self.installing = False
            self.failed.emit()
            return
        logger.info(f"Started update to {self.update['version']}")
        # Close properly (saves the settings, removes the tray icon); the
        # setup starts the new version when it is done
        QCoreApplication.quit()

    def _on_install_failed(self) -> None:
        if self._installing_automatically:
            # Let the user update by hand instead
            self._installing_automatically = False
            self.notify.emit(self.update)


def start(parent=None, automatic: bool = True) -> Updater:
    """Create the app-wide updater and schedule the check at start."""
    global _instance
    _instance = Updater(parent=parent)
    _instance.start(automatic)
    return _instance


def instance() -> "Updater | None":
    return _instance


def available_update() -> dict | None:
    """The newer release found so far, or None."""
    return _instance.update if _instance is not None else None
