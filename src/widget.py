"""
Prayer Times Taskbar Widget — main widget module.

Provides the ``PrayerWidget`` class that embeds itself into the Windows
taskbar as a child window.  It displays a live countdown to the next
prayer time, automatically refreshes API data, handles multi-monitor
setups, and opens the flyout menu on click.

Usage (from ``main.py``)::

    from src.widget import PrayerWidget, _active_widget

    widget = PrayerWidget(daily_times, hijri_dates, config)
    widget.show()
"""

import logging
from datetime import datetime, timedelta, date

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QFontMetrics

from src.config import load_config, save_config, get_cache_path
from src.i18n import get_prayer_name, t, set_language, PRAYER_ORDER
from src.win32_helpers import (
    find_all_taskbars,
    inject_into_taskbar,
    is_window_valid,
    get_taskbar_rect,
    get_window_rect,
    user32,
)
from src.data_loader import load_prayer_data, refresh_if_needed
from src.holy_days import is_ramadan_today

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


# ---------------------------------------------------------------------------
# PrayerWidget
# ---------------------------------------------------------------------------

class PrayerWidget(QWidget):
    """Taskbar-embedded widget showing a countdown to the next prayer.

    The widget is injected into the Windows taskbar via ``SetParent`` and
    WS_CHILD style manipulation.  It periodically updates the displayed
    prayer name and remaining time, rescans for taskbar changes, and
    refreshes prayer data from the Diyanet API.

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

        # ---- Internal state ----
        self._flyout = None
        self._dragging = False
        self._drag_start_x: float = 0.0
        self._recreate_attempts = 0

        # ---- Window flags ----
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # ---- Stylesheet: transparent bg, hover effect, white text ----
        self.setStyleSheet(
            """
            QWidget#MainContainer {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
            }
            QWidget#MainContainer:hover {
                background-color: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 12);
            }
            QLabel {
                color: white;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            """
        )

        # ---- UI structure ----
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(10, 0, 10, 0)

        self.label = QLabel("Loading...")
        self.label.setFont(QFont("Segoe UI Semibold", 10))
        self.label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        inner_layout.addWidget(
            self.label, alignment=Qt.AlignmentFlag.AlignCenter
        )

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

        # ---- Initial render ----
        self.update_widget()

        # ---- Update timer: refresh display every 10 seconds ----
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self.update_widget)
        self._update_timer.start(10_000)

        # ---- Rescan timer: detect taskbar changes every 5 seconds ----
        self._rescan_timer = QTimer(self)
        self._rescan_timer.timeout.connect(self._rescan_taskbars)
        self._rescan_timer.start(5_000)

        # ---- Data refresh timer: check API data every 30 minutes ----
        self._data_refresh_timer = QTimer(self)
        self._data_refresh_timer.timeout.connect(self._refresh_data)
        self._data_refresh_timer.start(30 * 60 * 1000)

    # ------------------------------------------------------------------
    # Taskbar management
    # ------------------------------------------------------------------

    def _rescan_taskbars(self) -> None:
        """Detect lost or newly connected taskbars and react accordingly.

        If the current taskbar window has been destroyed (e.g. monitor
        disconnected), the widget is recreated.  If a new monitor
        appears and matches the saved preference, the widget switches
        to it.
        """
        # Check if current taskbar is still alive
        if self.taskbar_hwnd and not is_window_valid(self.taskbar_hwnd):
            logger.info("Taskbar lost — recreating widget")
            self._recreate_widget()
            return

        # Look for newly attached monitors
        new_taskbars = find_all_taskbars()
        if len(new_taskbars) != len(self.taskbars):
            self.taskbars = new_taskbars
            saved_idx = self.config.get("monitor_index", 0)
            if (
                saved_idx < len(self.taskbars)
                and saved_idx != self.current_monitor_index
            ):
                self._recreate_widget(target_monitor=saved_idx)

    def _recreate_widget(self, target_monitor: int | None = None) -> None:
        """Schedule full widget recreation after a brief delay.

        The old widget is torn down and a brand-new ``PrayerWidget`` is
        constructed.  This is the only reliable recovery path after the
        taskbar's native window has been destroyed (``WM_DESTROY``).

        Args:
            target_monitor: Monitor index to inject into.  When *None*
                            the widget keeps its ``current_monitor_index``
                            (bug fix — the original incorrectly fell back
                            to monitor 0).
        """
        global _active_widget

        self._update_timer.stop()
        self._rescan_timer.stop()
        self._data_refresh_timer.stop()

        # Preserve current monitor unless explicitly overridden
        if target_monitor is not None:
            self.config["monitor_index"] = target_monitor
        else:
            self.config["monitor_index"] = self.current_monitor_index

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
        my_hwnd = int(self.winId())
        logger.info(f"Injecting my_hwnd={my_hwnd} into taskbar_hwnd={self.taskbar_hwnd}")

        # Ensure the native window is fully materialized
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        my_hwnd = int(self.winId())

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
        if (
            not self.taskbars
            or index >= len(self.taskbars)
            or index == self.current_monitor_index
        ):
            return
        self._recreate_widget(target_monitor=index)

    def adjust_position(self, delta: int) -> None:
        """Move the widget horizontally by *delta* pixels.

        Positive values shift left, negative values shift right.  The
        new offset is persisted to ``config.json`` immediately.

        Args:
            delta: Pixel offset to apply.
        """
        x_offset = self.config.get("x_offset", 185)
        x_offset = max(10, x_offset + delta)
        self.config["x_offset"] = x_offset
        save_config(self.config)
        self.update_widget()

    # ------------------------------------------------------------------
    # Display update
    # ------------------------------------------------------------------

    def update_widget(self) -> None:
        """Recalculate the countdown and update the displayed text.

        Called every 10 seconds by the update timer.  Determines the
        next upcoming prayer, formats the display string with translated
        prayer name and ``HH:MM`` countdown, and dynamically sizes the
        widget to fit the text within the taskbar.
        """
        # Verify taskbar is still alive
        if self.taskbar_hwnd and not is_window_valid(self.taskbar_hwnd):
            self._recreate_widget()
            return

        now = datetime.now()
        today = now.date()

        display_text = "Loading..."

        if today not in self.daily_times:
            display_text = t("date_missing")
        else:
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
                if tomorrow in self.daily_times:
                    fajr_str = self.daily_times[tomorrow].get("fajr")
                    if fajr_str:
                        tomorrow_now = now.replace(
                            year=tomorrow.year,
                            month=tomorrow.month,
                            day=tomorrow.day,
                        )
                        next_prayer_dt = self._parse_prayer_time(
                            fajr_str, tomorrow_now
                        )
                        next_key = "fajr"

            if next_key is None or next_prayer_dt is None:
                display_text = t("no_data")
            else:
                # --- Countdown calculation ---
                diff = next_prayer_dt - now
                total_seconds = int(diff.total_seconds())
                hours, remainder = divmod(max(total_seconds, 0), 3600)
                minutes, _ = divmod(remainder, 60)

                # --- Colour: red-ish if < 15 minutes ---
                if total_seconds <= 900:
                    self.label.setStyleSheet(
                        "color: #ff8b8b; background-color: transparent;"
                        " border: none; padding: 0px;"
                    )
                else:
                    self.label.setStyleSheet(
                        "color: #e5e5e5; background-color: transparent;"
                        " border: none; padding: 0px;"
                    )

                prayer_display_name = get_prayer_name(next_key)
                display_text = f"{prayer_display_name}   {hours:02d}:{minutes:02d}"

        self.label.setText(display_text)

        # --- Dynamic width & position inside the taskbar ---
        if self.taskbar_hwnd:
            tb_w, tb_h = get_taskbar_rect(self.taskbar_hwnd)
            if tb_h > 0:
                fm = QFontMetrics(self.label.font())
                text_width = fm.horizontalAdvance(display_text)

                w = text_width + 24
                h = tb_h - 6

                x_offset = self.config.get("x_offset", 185)
                x = tb_w - w - x_offset
                y = (tb_h - h) // 2

                logger.info(f"Setting geometry: x={x}, y={y}, w={w}, h={h} for text '{display_text}'")
                self.setGeometry(x, y, w, h)

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def _refresh_data(self) -> None:
        """Periodically check if API prayer data needs refreshing.

        Called every 30 minutes.  Uses :func:`refresh_if_needed` to
        determine whether remaining future data is running low and, if
        so, fetches fresh data from the Diyanet API.
        """
        cache_path = get_cache_path()
        updated = refresh_if_needed(
            self.config, cache_path, self.daily_times
        )
        if updated is not None:
            self.daily_times = updated
            logger.info("Prayer data refreshed from API")
            self.update_widget()

    def reload_data(self) -> None:
        """Reload prayer data and config after settings change.

        Called by the settings window when the user changes location,
        uploads an Excel file, or switches language.
        """
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

    def mousePressEvent(self, event) -> None:
        """Handle mouse button presses.

        - **Left / Right click**: open the flyout menu.
        - **Middle click**: begin horizontal drag to reposition.
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._dragging = True
            self._drag_start_x = event.globalPosition().x()
        elif event.button() in (
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.RightButton,
        ):
            self.show_modern_menu()

    def mouseMoveEvent(self, event) -> None:
        """Track horizontal drag movement while middle button is held."""
        if self._dragging:
            current_x = event.globalPosition().x()
            dx = int(self._drag_start_x - current_x)
            self._drag_start_x = current_x
            self.adjust_position(dx)

    def mouseReleaseEvent(self, event) -> None:
        """End drag on middle button release."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._dragging = False

    # ------------------------------------------------------------------
    # Flyout menu
    # ------------------------------------------------------------------

    def show_modern_menu(self) -> None:
        """Open (or close) the Win11-style prayer flyout panel.

        If a flyout is already visible it is closed.  Otherwise a new
        ``PrayerFlyout`` is created and animated with a slide-up +
        opacity transition.
        """
        # Lazy import to break circular dependency (flyout imports widget)
        from src.flyout import PrayerFlyout

        # Toggle: close if already open
        if self._flyout is not None and self._flyout.isVisible():
            self._flyout.close()
            self._flyout = None
            return

        # Dispose of stale flyout (prevent memory leak)
        if self._flyout is not None:
            self._flyout.deleteLater()
            self._flyout = None

        # Refresh taskbar list in case monitors changed
        self.taskbars = find_all_taskbars()

        self._flyout = PrayerFlyout(self)

        # Position the flyout centred above the widget
        left, top, right, bottom = get_window_rect(int(self.winId()))
        flyout_w = self._flyout.sizeHint().width()
        flyout_h = self._flyout.sizeHint().height()

        menu_x = left + (right - left) // 2 - flyout_w // 2
        menu_y = top - flyout_h - 12

        # Slide-up animation: start 18 px lower and glide up
        start_y = menu_y + 18
        self._flyout.setGeometry(menu_x, start_y, flyout_w, flyout_h)
        self._flyout.setWindowOpacity(0.0)
        self._flyout.show()
        self._flyout.activateWindow()

        # Position animation
        self._slide_anim = QPropertyAnimation(self._flyout, b"geometry")
        self._slide_anim.setDuration(280)
        self._slide_anim.setStartValue(
            QRect(menu_x, start_y, flyout_w, flyout_h)
        )
        self._slide_anim.setEndValue(
            QRect(menu_x, menu_y, flyout_w, flyout_h)
        )
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._slide_anim.start()

        # Opacity animation
        self._opacity_anim = QPropertyAnimation(
            self._flyout, b"windowOpacity"
        )
        self._opacity_anim.setDuration(250)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
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
