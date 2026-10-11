"""
tray.py — Notification area (system tray) icon.

Shows the app in the Windows notification area overflow (the ^ menu),
so it is visible that the app is running and can be controlled there:

- Left click: open the prayer times flyout.
- Right click: context menu with prayer times, settings and quit.
- Tooltip: the current countdown shown in the taskbar widget.
- Notification: once per version when an update is available.

Like the Windows system icons, the icon is a monochrome silhouette:
white on a dark taskbar, black on a light one.
"""

from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPainter, QPixmap

from src.i18n import t
from src import updater
from src import widget as widget_module
from src.theme import system_uses_dark, get_theme

_TOOLTIP_REFRESH_MS = 10_000


def _silhouette(icon: QIcon, dark_taskbar: bool) -> QIcon:
    """Recolor the app icon to a single color, keeping its shape (alpha)."""
    color = get_theme(dark_taskbar).text
    result = QIcon()
    for size in (16, 20, 24, 32, 48, 64):
        pixmap = icon.pixmap(size, size)
        if pixmap.isNull():
            continue
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.GlobalColor.transparent)
        p = QPainter(tinted)
        p.drawPixmap(0, 0, pixmap)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(tinted.rect(), color)
        p.end()
        result.addPixmap(tinted)
    return result if not result.isNull() else icon


class PrayerTray(QSystemTrayIcon):
    """Tray icon that always talks to the currently active PrayerWidget.

    The widget may be recreated (e.g. after Explorer restarts), so the
    live instance is looked up via ``widget_module._active_widget`` on
    every action instead of being stored here.
    """

    def __init__(self, icon: QIcon, parent=None) -> None:
        super().__init__(parent)
        self._app_icon = icon
        self._dark_taskbar = system_uses_dark()
        self.setIcon(_silhouette(icon, self._dark_taskbar))

        self._menu = QMenu()
        # Rebuild on every open so a language change applies immediately
        self._menu.aboutToShow.connect(self._build_menu)
        self.setContextMenu(self._menu)
        self.activated.connect(self._on_activated)

        self._refresh()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh)
        self._refresh_timer.start(_TOOLTIP_REFRESH_MS)

        if updater.instance() is not None:
            updater.instance().available.connect(self._on_update_available)
        self.messageClicked.connect(self._start_update)

    def _build_menu(self) -> None:
        self._menu.clear()
        self._menu.addAction(t("prayer_times"), self.show_prayer_times)
        self._menu.addAction(t("settings"), self._open_settings)
        update = updater.available_update()
        if update:
            self._menu.addAction(t("update_menu").format(version=update["version"]),
                                 self._start_update)
        self._menu.addSeparator()
        self._menu.addAction(t("quit"), QApplication.instance().quit)

    def _on_update_available(self, release: dict) -> None:
        """Notify once per version, so ignoring an update doesn't nag.

        Only for automatic checks; a manual check shows its result in the
        settings, and with automatic updates off the user wants no popups.
        """
        if not updater.instance().automatic:
            return
        version = release["version"]
        w = widget_module._active_widget
        if w is not None and w.config.get("notified_version") == version:
            return
        self.showMessage(t("update_notify_title"),
                         t("update_notify_body").format(version=version),
                         self._app_icon, 10_000)
        if w is not None:
            w.remember("notified_version", version)

    def _start_update(self) -> None:
        if updater.available_update():
            from src.settings_window import start_update
            start_update()

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
        from src.settings_window import show_settings
        show_settings()

    def _refresh(self) -> None:
        """Update the tooltip and follow a light/dark taskbar switch."""
        w = widget_module._active_widget
        text = w.display_text if w is not None else ""
        self.setToolTip(f"PrayerTaskbar\n{text}" if text else "PrayerTaskbar")

        dark = system_uses_dark()
        if dark != self._dark_taskbar:
            self._dark_taskbar = dark
            self.setIcon(_silhouette(self._app_icon, dark))
