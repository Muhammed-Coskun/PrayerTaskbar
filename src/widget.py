"""
Prayer Times Taskbar Widget — main widget module.

Provides the ``PrayerWidget`` class that embeds itself into the Windows
taskbar as a child window.  It displays a live countdown to the next
prayer time, automatically refreshes API data, handles multi-monitor
setups, and opens the flyout menu on click.

The widget paints itself (no child labels or style sheets), redraws only
when something visible changes, and updates exactly when the minute
changes, so it reacts like a native taskbar button.

Usage (from ``main.py``)::

    from src.widget import PrayerWidget, _active_widget

    widget = PrayerWidget(daily_times, hijri_dates, config)
    widget.show()
"""

import logging
import math
import threading
import time
from datetime import datetime, timedelta

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import (Qt, QObject, QTimer, QPropertyAnimation, QEasingCurve,
                          QPointF, QRect, QRectF, pyqtSignal)
from PyQt6.QtGui import QFontMetricsF, QGuiApplication, QPainter

from src.config import load_config, save_config, get_cache_path
from src.i18n import get_prayer_name, t, set_language, PRAYER_ORDER
from src.win32_helpers import (
    find_all_taskbars,
    inject_into_taskbar,
    is_window_valid,
    get_taskbar_rect,
    get_window_rect,
    native_to_qt,
    user32,
)
from src.data_loader import load_prayer_data, refresh_if_needed, get_coordinates
from src.holy_days import is_ramadan_today
from src.theme import system_theme, system_uses_dark, font

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level active widget reference — accessible from main.py
# ---------------------------------------------------------------------------

_active_widget: "PrayerWidget | None" = None
"""The currently active ``PrayerWidget`` instance.

Updated automatically when the widget is recreated (e.g. after a monitor
disconnect/reconnect).  ``main.py`` can import this to keep a reference
to the live widget.
"""

_DEFAULT_OFFSET = 185        # distance from the right end of the taskbar
_PADDING_H = 12              # space left and right of the text
_GAP = 8                     # between prayer name and countdown
_TICK_SLACK_MS = 30          # update just after the minute has changed
_HOUSEKEEPING_MS = 2_000     # taskbar, screen and theme checks
_SAVE_DELAY_MS = 600         # write the config once moving has stopped
_REOPEN_GUARD_S = 0.3        # a click that closed the flyout must not reopen it


class _Bridge(QObject):
    """Delivers results of background data refreshes to the UI thread."""
    refreshed = pyqtSignal(object)


# ---------------------------------------------------------------------------
# PrayerWidget
# ---------------------------------------------------------------------------

class PrayerWidget(QWidget):
    """Taskbar-embedded widget showing a countdown to the next prayer.

    The widget is injected into the Windows taskbar via ``SetParent`` and
    WS_CHILD style manipulation.  It updates the displayed prayer name and
    remaining time at every minute change, watches for taskbar, screen and
    theme changes, and refreshes prayer data from the Diyanet API.

    Args:
        daily_times: Dict mapping ``date`` → prayer times dict
                     (keys: fajr, sunrise, dhuhr, asr, maghrib, isha).
        hijri_dates: Dict mapping ``date`` → Hijri date string.
        config:      Application configuration dictionary.
    """

    # Maximum number of retry attempts when recreating the widget
    _MAX_RECREATE_RETRIES = 3
    # Delay between retry attempts in milliseconds
    _RECREATE_RETRY_DELAY_MS = 2000

    def __init__(
        self,
        daily_times: dict,
        hijri_dates: dict,
        config: dict,
    ) -> None:
        super().__init__()

        # ---- Data ----
        self.daily_times = daily_times
        self.hijri_dates = hijri_dates
        self.config = config
        self.city_name = config.get('location_name', '') or t('prayer_times')
        self.is_ramadan = is_ramadan_today(hijri_dates)

        # ---- Display state ----
        self._name = ""          # prayer name, or a status text
        self._countdown = ""     # "HH:MM", empty for status texts
        self._warn = False       # less than 15 minutes left
        self._minute = None      # minute the display was computed for
        self._hovered = False
        self._pressed = False
        self._theme = system_theme()
        self._font = font(13, semibold=True)

        # ---- Internal state ----
        self._flyout = None
        self._flyout_closed_at = 0.0
        self._drag_origin: tuple[float, int] | None = None
        self._recreate_attempts = 0
        self._refreshing = False
        self._bridge = _Bridge(self)
        self._bridge.refreshed.connect(self._on_refreshed)

        # ---- Window flags ----
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # ---- Taskbar discovery & injection ----
        self.taskbars: list[tuple[str, int]] = find_all_taskbars()
        self.taskbar_hwnd: int | None = None
        self.current_monitor_index: int = 0

        saved_idx = self.config.get("monitor_index", 0)
        if self.taskbars:
            idx = min(saved_idx, len(self.taskbars) - 1)
            self._do_inject(self.taskbars[idx][1])
            self.current_monitor_index = idx
        else:
            # Fallback: try secondary then primary (StartAllBack compat)
            hwnd = user32.FindWindowW("Shell_SecondaryTrayWnd", None)
            if not hwnd:
                hwnd = user32.FindWindowW("Shell_TrayWnd", None)
            if hwnd:
                self._do_inject(int(hwnd))

        # ---- Timers ----
        # Countdown: fires right after each minute change
        self._tick_timer = QTimer(self)
        self._tick_timer.setSingleShot(True)
        self._tick_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._tick_timer.timeout.connect(self._tick)

        # Taskbar alive, monitors, theme, taskbar size, missed minutes
        self._housekeeping_timer = QTimer(self)
        self._housekeeping_timer.timeout.connect(self._housekeeping)
        self._housekeeping_timer.start(_HOUSEKEEPING_MS)

        # API data: check every 30 minutes whether it runs low
        self._data_refresh_timer = QTimer(self)
        self._data_refresh_timer.timeout.connect(self._refresh_data)
        self._data_refresh_timer.start(30 * 60 * 1000)

        # Position changes are written to disk once moving has stopped
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(_SAVE_DELAY_MS)
        self._save_timer.timeout.connect(self._save_config)

        # ---- Initial render ----
        self._tick()

        # Build a flyout once in the background: the first one loads fonts
        # and styles (~200 ms), afterwards it opens instantly
        QTimer.singleShot(1500, self._prewarm_flyout)

    # ------------------------------------------------------------------
    # Taskbar management
    # ------------------------------------------------------------------

    def _housekeeping(self) -> None:
        """React to lost/new taskbars, theme changes and missed minutes."""
        # The taskbar was destroyed (Explorer restart, monitor unplugged)
        if self.taskbar_hwnd and not is_window_valid(self.taskbar_hwnd):
            logger.info("Taskbar lost — recreating widget")
            self._recreate_widget()
            return

        # A monitor was connected or disconnected
        new_taskbars = find_all_taskbars()
        if len(new_taskbars) != len(self.taskbars):
            self.taskbars = new_taskbars
            saved_idx = self.config.get("monitor_index", 0)
            if (
                saved_idx < len(self.taskbars)
                and saved_idx != self.current_monitor_index
            ):
                self._move_to_taskbar(saved_idx)
                return

        # Light/dark taskbar switched
        if system_uses_dark() != self._theme.dark:
            self._theme = system_theme()
            self.update()

        # A minute was missed (e.g. after sleep), else follow taskbar resizes
        if self._current_minute() != self._minute:
            self._tick()
        else:
            self._place()

    def _recreate_widget(self, target_monitor: int | None = None) -> None:
        """Schedule full widget recreation after a brief delay.

        The old widget is torn down and a brand-new ``PrayerWidget`` is
        constructed.  This is the only reliable recovery path after the
        taskbar's native window has been destroyed (``WM_DESTROY``).

        Args:
            target_monitor: Monitor index to inject into.  When *None*
                            the widget keeps its ``current_monitor_index``.
        """
        self._tick_timer.stop()
        self._housekeeping_timer.stop()
        self._data_refresh_timer.stop()

        # Preserve current monitor unless explicitly overridden
        if target_monitor is not None:
            self.config["monitor_index"] = target_monitor
        else:
            self.config["monitor_index"] = self.current_monitor_index

        self._save_timer.stop()
        save_config(self.config)

        # Reset retry counter for the new creation attempt
        self._recreate_attempts = 0
        QTimer.singleShot(1000, self._do_recreate)

    def _do_recreate(self) -> None:
        """Create a replacement ``PrayerWidget`` instance.

        Includes retry logic: if no taskbar is found on the first
        attempt, up to ``_MAX_RECREATE_RETRIES`` additional attempts are
        made with a ``_RECREATE_RETRY_DELAY_MS`` delay between each.
        """
        global _active_widget

        try:
            new_widget = PrayerWidget(
                self.daily_times, self.hijri_dates, self.config
            )

            # Verify that injection actually succeeded
            if new_widget.taskbar_hwnd is None:
                self._recreate_attempts += 1
                if self._recreate_attempts < self._MAX_RECREATE_RETRIES:
                    logger.warning(
                        "Taskbar not found on attempt %d/%d — retrying",
                        self._recreate_attempts,
                        self._MAX_RECREATE_RETRIES,
                    )
                    new_widget.deleteLater()
                    QTimer.singleShot(
                        self._RECREATE_RETRY_DELAY_MS, self._do_recreate
                    )
                    return
                logger.error(
                    "Taskbar not found after %d attempts — giving up",
                    self._MAX_RECREATE_RETRIES,
                )

            new_widget.show()
            _active_widget = new_widget

        except Exception:
            logger.exception("Failed to recreate widget")

        # Tear down the old widget regardless
        self.hide()
        self.deleteLater()

    def _do_inject(self, taskbar_hwnd_int: int) -> None:
        """Inject this widget into the given taskbar.

        Delegates to :func:`src.win32_helpers.inject_into_taskbar` which
        handles ``SetParent`` and the ``WS_CHILD`` style switch.

        Args:
            taskbar_hwnd_int: Native window handle of the target taskbar.
        """
        self.taskbar_hwnd = taskbar_hwnd_int

        # Ensure the native window is fully materialized
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        my_hwnd = int(self.winId())
        logger.info(f"Injecting my_hwnd={my_hwnd} into taskbar_hwnd={self.taskbar_hwnd}")

        success = inject_into_taskbar(my_hwnd, self.taskbar_hwnd)
        logger.info(f"Injection success: {success}")

        if not success:
            logger.error("Injection into taskbar 0x%X failed", taskbar_hwnd_int)
            self.taskbar_hwnd = None

    # ------------------------------------------------------------------
    # Monitor switching & positioning
    # ------------------------------------------------------------------

    def switch_monitor(self, index: int) -> None:
        """Switch the widget to a different monitor's taskbar.

        Args:
            index: Zero-based index into ``self.taskbars``.
        """
        self.taskbars = find_all_taskbars()
        if (
            not self.taskbars
            or index >= len(self.taskbars)
            or index == self.current_monitor_index
        ):
            return
        self._move_to_taskbar(index)

    def _move_to_taskbar(self, index: int) -> None:
        """Re-parent the widget into another (living) taskbar right away."""
        self._do_inject(self.taskbars[index][1])
        if self.taskbar_hwnd is None:
            self._recreate_widget(target_monitor=index)
            return
        self.current_monitor_index = index
        self.config["monitor_index"] = index
        self._save_timer.start()
        self._place()
        self.update()

    def adjust_position(self, delta: int) -> None:
        """Move the widget horizontally by *delta* pixels.

        Positive values shift left, negative values shift right.  The
        new offset is written to ``config.json`` once moving has stopped.

        Args:
            delta: Pixel offset to apply.
        """
        self._set_offset(self.config.get("x_offset", _DEFAULT_OFFSET) + delta)

    def _set_offset(self, offset: int) -> None:
        if self.taskbar_hwnd:
            taskbar_width, _ = get_taskbar_rect(self.taskbar_hwnd)
            offset = min(offset, max(10, taskbar_width - self._content_width()))
        self.config["x_offset"] = max(10, offset)
        self._place()
        self._save_timer.start()

    def _save_config(self) -> None:
        save_config(self.config)

    def flush_pending_save(self) -> None:
        """Write a pending position change now (e.g. before quitting)."""
        if self._save_timer.isActive():
            self._save_timer.stop()
            self._save_config()

    def _place(self) -> None:
        """Size and position the widget in its taskbar (only if it changed)."""
        if not self.taskbar_hwnd:
            return
        taskbar_width, taskbar_height = get_taskbar_rect(self.taskbar_hwnd)
        if taskbar_height <= 0:
            return
        width = self._content_width()
        height = taskbar_height - 6
        x = taskbar_width - width - self.config.get("x_offset", _DEFAULT_OFFSET)
        geometry = QRect(x, (taskbar_height - height) // 2, width, height)
        if geometry != self.geometry():
            self.setGeometry(geometry)

    # ------------------------------------------------------------------
    # Display update
    # ------------------------------------------------------------------

    @property
    def display_text(self) -> str:
        """The text shown in the taskbar, e.g. "Isha   00:22"."""
        return f"{self._name}   {self._countdown}" if self._countdown else self._name

    @staticmethod
    def _current_minute() -> str:
        return datetime.now().strftime("%Y%m%d%H%M")

    def _tick(self) -> None:
        """Update the countdown and schedule the next update for the next minute."""
        self.update_widget()
        now = datetime.now()
        ms_to_next_minute = (60 - now.second) * 1000 - now.microsecond // 1000
        self._tick_timer.start(ms_to_next_minute + _TICK_SLACK_MS)

    def update_widget(self) -> None:
        """Recalculate the countdown and repaint if anything visible changed."""
        name, countdown, warn = self._compute_display()
        self._minute = self._current_minute()
        if (name, countdown, warn) != (self._name, self._countdown, self._warn):
            self._name, self._countdown, self._warn = name, countdown, warn
            self.update()
        self._place()

    def _compute_display(self) -> tuple[str, str, bool]:
        """Return (prayer name or status text, "HH:MM" countdown, warn)."""
        now = datetime.now()
        today = now.date()

        if today not in self.daily_times:
            if self._location_missing():
                return t("location_missing"), "", False
            return t("date_missing"), "", False

        times_today = self.daily_times[today]
        next_key: str | None = None
        next_prayer_dt: datetime | None = None

        for key in PRAYER_ORDER:
            time_str = times_today.get(key)
            if not time_str:
                continue
            prayer_dt = self._parse_prayer_time(time_str, now)
            if prayer_dt > now:
                next_key = key
                next_prayer_dt = prayer_dt
                break

        # All prayers passed today — look at tomorrow's fajr
        if next_key is None:
            tomorrow = today + timedelta(days=1)
            fajr_str = self.daily_times.get(tomorrow, {}).get("fajr")
            if fajr_str:
                next_prayer_dt = self._parse_prayer_time(
                    fajr_str, now.replace(year=tomorrow.year, month=tomorrow.month,
                                          day=tomorrow.day)
                )
                next_key = "fajr"

        if next_key is None or next_prayer_dt is None:
            return t("no_data"), "", False

        total_seconds = int((next_prayer_dt - now).total_seconds())
        hours, remainder = divmod(max(total_seconds, 0), 3600)
        minutes = remainder // 60
        return get_prayer_name(next_key), f"{hours:02d}:{minutes:02d}", total_seconds <= 900

    def _content_width(self) -> int:
        metrics = QFontMetricsF(self._font)
        width = metrics.horizontalAdvance(self._name)
        if self._countdown:
            width += _GAP + metrics.horizontalAdvance(self._countdown)
        return math.ceil(width) + 2 * _PADDING_H

    def paintEvent(self, event) -> None:
        th = self._theme
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Hover / pressed / open state, like Windows 11 taskbar buttons
        flyout_open = self._flyout is not None and self._flyout.isVisible()
        if self._pressed or self._hovered or flyout_open:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(th.subtle_pressed if self._pressed else th.subtle_hover)
            p.drawRoundedRect(QRectF(self.rect()), 4, 4)

        metrics = QFontMetricsF(self._font)
        text_width = self._content_width() - 2 * _PADDING_H
        x = (self.width() - text_width) / 2
        baseline = (self.height() + metrics.ascent() - metrics.descent()) / 2
        p.setFont(self._font)
        p.setPen(th.critical if self._warn else th.text)
        p.drawText(QPointF(x, baseline), self._name)
        if self._countdown:
            p.drawText(QPointF(x + metrics.horizontalAdvance(self._name) + _GAP, baseline),
                       self._countdown)
        p.end()

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def _refresh_data(self) -> None:
        """Check in the background whether API prayer data needs refreshing.

        Called every 30 minutes.  The request runs in a thread so the
        taskbar never freezes while waiting for the network.
        """
        if self._refreshing:
            return
        self._refreshing = True
        config = dict(self.config)
        daily_times = self.daily_times
        bridge = self._bridge

        def work():
            try:
                result = refresh_if_needed(config, get_cache_path(), daily_times)
            except Exception:
                logger.exception("Prayer data refresh failed")
                result = None
            try:
                bridge.refreshed.emit(result)
            except RuntimeError:
                pass  # widget was recreated in the meantime

        threading.Thread(target=work, daemon=True).start()

    def _on_refreshed(self, result) -> None:
        self._refreshing = False
        if result is not None:
            self.daily_times, self.hijri_dates = result
            self.is_ramadan = is_ramadan_today(self.hijri_dates)
            logger.info("Prayer data refreshed from API")
            self.update_widget()

    def reload_data(self) -> None:
        """Reload prayer data and config after settings change.

        Called by the settings window when the user changes location,
        uploads an Excel file, or switches language.
        """
        self.flush_pending_save()
        self.config = load_config()
        set_language(self.config.get('language', 'en'))
        cache_path = get_cache_path()
        daily_times, hijri_dates, city_name = load_prayer_data(self.config, cache_path)
        if daily_times:
            self.daily_times = daily_times
            self.hijri_dates = hijri_dates
            self.city_name = city_name
            self.is_ramadan = is_ramadan_today(hijri_dates)
        self.update_widget()

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, event) -> None:
        """Handle mouse button presses.

        - **Left / Right click**: open the flyout menu, or the settings
          if no location is set yet.
        - **Middle click**: begin horizontal drag to reposition.
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._drag_origin = (event.globalPosition().x(),
                                 self.config.get("x_offset", _DEFAULT_OFFSET))
        elif event.button() in (
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.RightButton,
        ):
            self._pressed = True
            self.update()
            if not self.daily_times and self._location_missing():
                self.open_settings()
            else:
                self.show_modern_menu()

    def mouseMoveEvent(self, event) -> None:
        """Follow the mouse while the middle button is held."""
        if self._drag_origin is not None:
            start_x, start_offset = self._drag_origin
            self._set_offset(start_offset + int(start_x - event.globalPosition().x()))

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._drag_origin = None
        self._pressed = False
        self.update()

    # ------------------------------------------------------------------
    # Flyout menu
    # ------------------------------------------------------------------

    def _location_missing(self) -> bool:
        """True if prayer times come from the API but no usable location is set."""
        return (
            self.config.get("data_source", "api") == "api"
            and get_coordinates(self.config) is None
        )

    def open_settings(self) -> None:
        """Open the settings window (used by the flyout and the tray icon)."""
        from src.settings_window import show_settings
        show_settings()

    def _prewarm_flyout(self) -> None:
        """Build and discard one flyout so the first real one opens instantly."""
        from src.flyout import PrayerFlyout
        try:
            PrayerFlyout(self).deleteLater()
        except Exception:
            logger.exception("Flyout prewarm failed")

    def _on_flyout_closed(self) -> None:
        self._flyout_closed_at = time.monotonic()
        self.update()

    def show_modern_menu(self) -> None:
        """Open (or close) the Win11-style prayer flyout panel.

        If a flyout is already visible it is closed.  Otherwise a new
        ``PrayerFlyout`` is created 12 px above the taskbar, kept inside
        the screen, and animated with a short slide-up + fade.
        """
        # Lazy import to break circular dependency (flyout imports widget)
        from src.flyout import PrayerFlyout

        # Toggle: close if already open
        if self._flyout is not None and self._flyout.isVisible():
            self._flyout.close()
            return

        # The click that took the focus away has just closed the flyout
        if time.monotonic() - self._flyout_closed_at < _REOPEN_GUARD_S:
            return

        # Dispose of stale flyout (prevent memory leak)
        if self._flyout is not None:
            self._flyout.deleteLater()
            self._flyout = None

        self._flyout = PrayerFlyout(self)
        self._flyout.closed.connect(self._on_flyout_closed)
        flyout_w = self._flyout.width()
        flyout_h = self._flyout.sizeHint().height()

        # Centre above the widget (Win32 gives physical pixels)
        left, top, right, _bottom = get_window_rect(int(self.winId()))
        anchor, screen = native_to_qt((left + right) // 2, top)
        avail = (screen or QGuiApplication.primaryScreen()).availableGeometry()
        menu_x = anchor.x() - flyout_w // 2
        menu_x = max(avail.left() + 12, min(menu_x, avail.right() - flyout_w - 12))
        menu_y = max(avail.top() + 12, min(anchor.y(), avail.bottom()) - flyout_h - 12)

        # Short slide-up from 8 px below
        start_y = menu_y + 8
        self._flyout.setGeometry(menu_x, start_y, flyout_w, flyout_h)
        self._flyout.setWindowOpacity(0.0)
        self._flyout.show()
        self._flyout.activateWindow()
        self.update()

        self._slide_anim = QPropertyAnimation(self._flyout, b"geometry")
        self._slide_anim.setDuration(160)
        self._slide_anim.setStartValue(QRect(menu_x, start_y, flyout_w, flyout_h))
        self._slide_anim.setEndValue(QRect(menu_x, menu_y, flyout_w, flyout_h))
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_anim.start()

        self._opacity_anim = QPropertyAnimation(self._flyout, b"windowOpacity")
        self._opacity_anim.setDuration(120)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._opacity_anim.start()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_prayer_time(time_str: str, reference: datetime) -> datetime:
        """Parse an ``HH:MM`` time string into a full ``datetime``.

        The date portion is taken from *reference* so that the resulting
        ``datetime`` falls on the correct day.

        Args:
            time_str:  Time in ``"HH:MM"`` format.
            reference: A ``datetime`` whose date fields are reused.

        Returns:
            A ``datetime`` combining the reference date with the parsed
            time.
        """
        parts = time_str.strip().split(":")
        hour, minute = int(parts[0]), int(parts[1])
        return reference.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
