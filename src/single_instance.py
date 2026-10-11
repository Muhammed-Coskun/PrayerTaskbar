"""
single_instance.py — Ensure only one PrayerTaskbar instance runs.

The first instance listens on a named local socket.  A second instance
connects to it, asks it to show the prayer times flyout, and exits.
"""

import ctypes
import logging
import os
from typing import Callable

from PyQt6.QtCore import QObject
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

logger = logging.getLogger(__name__)

# Per-user name so different Windows users do not block each other
SERVER_NAME = f"PrayerTaskbar.SingleInstance.{os.environ.get('USERNAME', 'user')}"
_ACTIVATE_MSG = b"activate"
_ASFW_ANY = -1


def notify_running_instance() -> bool:
    """Try to reach an already running instance.

    Returns:
        True if another instance is running (and was asked to activate),
        False if this process should become the primary instance.
    """
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if not socket.waitForConnected(500):
        return False

    # Let the running instance bring its flyout to the foreground
    if os.name == "nt":
        try:
            ctypes.windll.user32.AllowSetForegroundWindow(_ASFW_ANY)
        except Exception:
            pass

    socket.write(_ACTIVATE_MSG)
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


class InstanceServer(QObject):
    """Listens for activation requests from later-started instances."""

    def __init__(self, on_activate: Callable[[], None], parent=None) -> None:
        super().__init__(parent)
        self._on_activate = on_activate
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._handle_connection)

        if not self._server.listen(SERVER_NAME):
            # Stale socket from a crashed instance: remove and retry
            QLocalServer.removeServer(SERVER_NAME)
            if not self._server.listen(SERVER_NAME):
                logger.error(f"Single-instance server failed: {self._server.errorString()}")

    def _handle_connection(self) -> None:
        socket = self._server.nextPendingConnection()
        if socket is None:
            return
        socket.readyRead.connect(lambda s=socket: self._read(s))
        socket.disconnected.connect(socket.deleteLater)

    def _read(self, socket: QLocalSocket) -> None:
        if bytes(socket.readAll()).strip() == _ACTIVATE_MSG:
            logger.info("Activation request from second instance")
            self._on_activate()
