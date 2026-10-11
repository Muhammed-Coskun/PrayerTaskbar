"""
tray.py — Notification area (system tray) icon.

Shows the app in the Windows notification area overflow (the ^ menu),
so it is visible that the app is running and can be controlled there:

- Left click: open the prayer times flyout.
- Right click: context menu with prayer times, settings and quit.
- Tooltip: the current countdown shown in the taskbar widget.
"""

from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon

from src.i18n import t
from src import widget as widget_module

_TOOLTIP_REFRESH_MS = 10_000


class PrayerTray(QSystemTrayIcon):
    """Tray icon that always talks to the currently active PrayerWidget.

    The widget may be recreated (e.g. after Explorer restarts), so the
    live instance is looked up via ``widget_module._active_widget`` on
    every action instead of being stored here.
    """

    def __init__(self, icon: QIcon, parent=None) -> None:
        super().__init__(icon, parent)

        self._menu = QMenu()
        # Rebuild on every open so a language change applies immediately
        self._menu.aboutToShow.connect(self._build_menu)
        self.setContextMenu(self._menu)
        self.activated.connect(self._on_activated)

        self._update_tooltip()
        self._tooltip_timer = QTimer(self)
        self._tooltip_timer.timeout.connect(self._update_tooltip)
        self._tooltip_timer.start(_TOOLTIP_REFRESH_MS)

    def _build_menu(self) -> None:
        self._menu.clear()
        self._menu.addAction(t("prayer_times"), self.show_prayer_times)
        self._menu.addAction(t("settings"), self._open_settings)
        self._menu.addSeparator()
        self._menu.addAction(t("quit"), QApplication.instance().quit)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_prayer_times()

    def show_prayer_times(self) -> None:
        """Open the flyout (no-op toggle-close if it is already open)."""
        w = widget_module._active_widget
        if w is None:
            return
        if w._flyout is not None and w._flyout.isVisible():
            w._flyout.activateWindow()
            return
        w.show_modern_menu()

    def _open_settings(self) -> None:
        w = widget_module._active_widget
        if w is not None:
            w.open_settings()

    def _update_tooltip(self) -> None:
        w = widget_module._active_widget
        text = w.label.text() if w is not None else ""
        self.setToolTip(f"PrayerTaskbar\n{text}" if text else "PrayerTaskbar")
