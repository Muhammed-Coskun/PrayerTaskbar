"""
flyout.py — Windows 11 style flyout with today's prayer times.

Opens above the taskbar widget with the native rounded corners, shadow
and acrylic background of Windows 11 flyouts. Shows the location and
date, the next holy day and today's prayers with the next one highlighted.
"""

import math
from datetime import datetime, date, timedelta

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QEvent, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QFontMetrics, QFontMetricsF, QPainter

from src.i18n import (t, get_prayer_name, get_holy_day_name, format_date,
                      format_duration, PRAYER_ORDER)
from src.holy_days import get_next_holy_day
from src.icons import PrayerIcon, prayer_color
from src.controls import IconButton, accent_button
from src.theme import (system_theme, transparency_enabled, css, font, icon_font,
                       round_corners, enable_acrylic,
                       GLYPH_SETTINGS, GLYPH_MAP_PIN, GLYPH_WARNING, GLYPH_STAR)

FLYOUT_WIDTH = 360
_PADDING_H = 20

# Warm gold for the iftar highlight during Ramadan
_IFTAR_DARK = QColor("#FFC850")
_IFTAR_LIGHT = QColor("#9D5D00")


def _muted(theme) -> QColor:
    """Text color for less important text (past prayers, Hijri date).

    The Fluent tertiary text is too faint on the light acrylic, so light
    mode uses the secondary text color.
    """
    return theme.text_tertiary if theme.dark else theme.text_secondary


def _accent_tint(theme, color: QColor) -> QColor:
    """Soft background in an accent color (next prayer, holy day countdown)."""
    tint = QColor(color)
    tint.setAlphaF(0.14 if theme.dark else 0.1)
    return tint


class PrayerFlyout(QWidget):
    """Win11 flyout for prayer times."""

    closed = pyqtSignal()
    """Emitted when the flyout is hidden (closed or focus lost)."""

    def __init__(self, prayer_widget):
        super().__init__(None)
        self.prayer_widget = prayer_widget
        self.theme = system_theme()
        self._acrylic = transparency_enabled()
        self._next_prayer_dt: datetime | None = None
        self._countdown_label: QLabel | None = None
        self._tomorrow_prefix = ""
        self._was_active = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # Per-pixel alpha so the acrylic blur behind the window shows through
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(FLYOUT_WIDTH)

        self._build_ui()

        # Native Windows 11 corners, border and shadow; set before the
        # window is shown so it never appears with square corners
        hwnd = int(self.winId())
        round_corners(hwnd)
        if self._acrylic:
            self._acrylic = enable_acrylic(hwnd, self.theme.acrylic_tint)

        # Fallback for when Windows never activates the flyout; normally it
        # closes in changeEvent as soon as it loses the focus
        self._close_timer = QTimer(self)
        self._close_timer.timeout.connect(self._check_active)

        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._update_countdown)

    def _check_active(self):
        if not self.isActiveWindow():
            self._close_timer.stop()
            self.close()

    def showEvent(self, event):
        super().showEvent(event)
        self._close_timer.start(300)
        self._countdown_timer.start(15_000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._close_timer.stop()
        self._countdown_timer.stop()
        self.closed.emit()

    def changeEvent(self, event):
        # Close right away when another window gets the focus, like the
        # Windows 11 flyouts (instead of waiting for the next timer tick)
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self._was_active = True
            elif self._was_active and self.isVisible():
                self.close()
        super().changeEvent(event)

    # ─── Layout ───

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(_PADDING_H, 18, _PADDING_H, 20)
        root.setSpacing(0)

        root.addLayout(self._build_header())
        root.addSpacing(16)

        holy_card = self._build_holy_day_card()
        if holy_card is not None:
            root.addWidget(holy_card)
            root.addSpacing(12)

        times_today = self.prayer_widget.daily_times.get(date.today())
        if times_today:
            root.addLayout(self._build_prayer_list(times_today))
        else:
            root.addWidget(self._build_empty_state())

    def _label(self, text: str, px: int, color: QColor, semibold: bool = False,
               display: bool = False) -> QLabel:
        label = QLabel(text)
        label.setFont(font(px, semibold=semibold, display=display))
        label.setStyleSheet(f"color: {css(color)}; background: transparent;")
        return label

    def _build_header(self) -> QHBoxLayout:
        th = self.theme
        row = QHBoxLayout()
        row.setSpacing(8)

        texts = QVBoxLayout()
        texts.setSpacing(2)

        name = self.prayer_widget.city_name or t('prayer_times')
        title = self._label("", 20, th.text, semibold=True, display=True)
        available = FLYOUT_WIDTH - 2 * _PADDING_H - 32 - row.spacing()
        elided = QFontMetrics(title.font()).elidedText(
            name, Qt.TextElideMode.ElideRight, available
        )
        title.setText(elided)
        if elided != name:
            title.setToolTip(name)
        texts.addWidget(title)

        today = date.today()
        texts.addWidget(self._label(format_date(today, with_weekday=True), 12, th.text_secondary))
        hijri = self.prayer_widget.hijri_dates.get(today)
        if hijri:
            texts.addWidget(self._label(hijri, 12, _muted(th)))

        row.addLayout(texts, 1)

        settings_btn = IconButton(GLYPH_SETTINGS, th, tooltip=t('settings'))
        settings_btn.clicked.connect(self._open_settings)
        row.addWidget(settings_btn, 0, Qt.AlignmentFlag.AlignTop)
        return row

    def _build_holy_day_card(self) -> QFrame | None:
        holy_date, holy_key, day_num = get_next_holy_day()
        if not holy_date or not holy_key:
            return None

        th = self.theme
        card = QFrame()
        card.setObjectName("HolyDayCard")
        card.setStyleSheet(
            f"QFrame#HolyDayCard {{ background: {css(th.card)};"
            f" border: 1px solid {css(th.control_stroke)}; border-radius: 6px; }}"
        )
        h = QHBoxLayout(card)
        h.setContentsMargins(14, 10, 14, 10)
        h.setSpacing(14)
        h.addWidget(self._build_countdown(holy_date), 0, Qt.AlignmentFlag.AlignVCenter)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addStretch()
        name = get_holy_day_name(holy_key)
        if day_num:
            name = f"{name} · {t('day')} {day_num}"
        name_label = self._label(name, 14, th.text, semibold=True)
        name_label.setWordWrap(True)
        texts.addWidget(name_label)
        texts.addWidget(self._label(format_date(holy_date, with_weekday=True), 12, th.text_secondary))
        hijri = self.prayer_widget.hijri_dates.get(holy_date)
        if hijri:
            texts.addWidget(self._label(hijri, 12, _muted(th)))
        texts.addStretch()
        h.addLayout(texts, 1)
        return card

    def _build_countdown(self, holy_date: date) -> QWidget:
        """Days left as a large number in the accent color: "60 days"."""
        delta = (holy_date - date.today()).days
        if delta <= 0:
            # The holy day is today
            return _Countdown(GLYPH_STAR, t('today_unit'), self.theme.accent_foreground,
                              icon_font(28))
        unit = t('day_unit') if delta == 1 else t('days_unit')
        return _Countdown(str(delta), unit, self.theme.accent_foreground,
                          font(34, semibold=True, display=True))

    def _build_prayer_list(self, times_today: dict) -> QVBoxLayout:
        th = self.theme
        now = datetime.now()
        entries = []
        for key in PRAYER_ORDER:
            time_str = (times_today.get(key) or "").strip()
            if time_str:
                hour, minute = map(int, time_str.split(":"))
                entries.append((key, time_str, now.replace(hour=hour, minute=minute,
                                                           second=0, microsecond=0)))

        next_key = next((key for key, _, dt in entries if dt > now), None)
        is_iftar_day = self.prayer_widget.is_ramadan

        column = QVBoxLayout()
        column.setSpacing(2)
        for key, time_str, dt in entries:
            if key == next_key:
                state = "next"
                self._next_prayer_dt = dt
            elif dt <= now:
                state = "past"
            else:
                state = "upcoming"
            iftar = is_iftar_day and key == "maghrib"
            row = _PrayerRow(th, key, t('iftar') if iftar else get_prayer_name(key),
                             time_str, state, iftar)
            if state == "next":
                row.set_countdown(self._countdown_text())
                self._countdown_label = row.countdown_label
            column.addWidget(row)

        # After Isha: point to tomorrow's Fajr, which the taskbar counts down to
        if next_key is None:
            tomorrow = self.prayer_widget.daily_times.get(date.today() + timedelta(days=1), {})
            fajr = (tomorrow.get("fajr") or "").strip()
            if fajr:
                hour, minute = map(int, fajr.split(":"))
                self._next_prayer_dt = (now + timedelta(days=1)).replace(
                    hour=hour, minute=minute, second=0, microsecond=0)
                column.addSpacing(8)
                hint = self._label("", 12, th.text_secondary)
                hint.setContentsMargins(14, 0, 0, 0)
                self._countdown_label = hint
                self._tomorrow_prefix = f"{t('tomorrow')} · {get_prayer_name('fajr')} {fajr} · "
                column.addWidget(hint)
                self._update_countdown()
        return column

    def _build_empty_state(self) -> QWidget:
        th = self.theme
        location_missing = self.prayer_widget._location_missing()

        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(8, 8, 8, 0)
        v.setSpacing(6)

        glyph = QLabel(GLYPH_MAP_PIN if location_missing else GLYPH_WARNING)
        glyph.setFont(icon_font(28))
        glyph.setStyleSheet(f"color: {css(th.text_tertiary)}; background: transparent;")
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(glyph)
        v.addSpacing(4)

        title = self._label(t('no_location_title' if location_missing else 'no_times_title'),
                            14, th.text, semibold=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(title)

        body = self._label(t('no_location_body' if location_missing else 'no_times_body'),
                           12, th.text_secondary)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        v.addWidget(body)
        v.addSpacing(10)

        button = accent_button(t('choose_location' if location_missing else 'open_settings'), th)
        button.clicked.connect(self._open_settings)
        v.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        return box

    # ─── Countdown ───

    def _countdown_text(self) -> str:
        if self._next_prayer_dt is None:
            return ""
        minutes = int((self._next_prayer_dt - datetime.now()).total_seconds() // 60)
        return format_duration(max(minutes, 0))

    def _update_countdown(self):
        if self._countdown_label is None:
            return
        self._countdown_label.setText(self._tomorrow_prefix + self._countdown_text())

    # ─── Actions ───

    def _open_settings(self):
        """Open the settings window."""
        self.close()
        self.prayer_widget.open_settings()

    def paintEvent(self, event):
        # With acrylic the window stays transparent and Windows draws the blur
        if not self._acrylic:
            p = QPainter(self)
            p.fillRect(self.rect(), self.theme.flyout_bg)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def sizeHint(self):
        return self.layout().sizeHint() if self.layout() else super().sizeHint()

    def focusOutEvent(self, event):
        self.close()
        super().focusOutEvent(event)


class _PrayerRow(QWidget):
    """One prayer in the list; the next prayer gets the Fluent selection look."""

    def __init__(self, theme, key: str, name: str, time_str: str, state: str,
                 iftar: bool = False) -> None:
        super().__init__()
        self._theme = theme
        self._state = state
        self._highlight = (_IFTAR_DARK if theme.dark else _IFTAR_LIGHT) if iftar else theme.accent
        self.countdown_label: QLabel | None = None
        self.setFixedHeight(52 if state == "next" else 40)

        icon_color = prayer_color(key, theme.dark)
        if state == "past":
            text_color = time_color = _muted(theme)
            icon_color.setAlphaF(0.5)
        elif state == "next":
            text_color = theme.text
            time_color = self._highlight if iftar else theme.accent_foreground
        else:
            text_color = theme.text
            time_color = theme.text_secondary
        if iftar and state != "past":
            text_color = icon_color = self._highlight

        h = QHBoxLayout(self)
        h.setContentsMargins(14, 0, 12, 0)
        h.setSpacing(12)
        h.addWidget(PrayerIcon(key, icon_color, 20))

        names = QVBoxLayout()
        names.setSpacing(0)
        names.addStretch()
        self._name_label = self._make_label(name, text_color, state == "next")
        names.addWidget(self._name_label)
        if state == "next":
            self.countdown_label = self._make_label("", theme.text_secondary, False, 12)
            names.addWidget(self.countdown_label)
        names.addStretch()
        h.addLayout(names, 1)

        h.addWidget(self._make_label(time_str, time_color, state == "next"))

    @staticmethod
    def _make_label(text: str, color: QColor, semibold: bool, px: int = 14) -> QLabel:
        label = QLabel(text)
        label.setFont(font(px, semibold=semibold))
        label.setStyleSheet(f"color: {css(color)}; background: transparent;")
        return label

    def set_countdown(self, text: str) -> None:
        if self.countdown_label is not None:
            self.countdown_label.setText(text)

    def paintEvent(self, event):
        if self._state != "next":
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_accent_tint(self._theme, self._highlight))
        p.drawRoundedRect(QRectF(self.rect()), 4, 4)
        # Selection pill on the left, as in WinUI lists
        pill_h = 16
        p.setBrush(self._highlight)
        p.drawRoundedRect(QRectF(0, (self.height() - pill_h) / 2, 3, pill_h), 1.5, 1.5)
        p.end()


class _Countdown(QWidget):
    """A large number (or glyph) with its unit below, e.g. "60 / days".

    Drawn by hand so the visible ink of both lines is centered in the
    card's height; QLabel line boxes add extra space above the digits.
    """

    _GAP = 6       # between the number and the unit
    _HEIGHT = 70   # keeps the card at its usual height

    def __init__(self, top: str, unit: str, color: QColor, top_font) -> None:
        super().__init__()
        self._top = top
        self._unit = unit
        self._color = QColor(color)
        self._top_font = top_font
        self._unit_font = font(12)
        width = max(QFontMetricsF(top_font).horizontalAdvance(top),
                    QFontMetricsF(self._unit_font).horizontalAdvance(unit))
        self.setMinimumSize(math.ceil(width) + 8, self._HEIGHT)

    def paintEvent(self, event):
        top_metrics = QFontMetricsF(self._top_font)
        unit_metrics = QFontMetricsF(self._unit_font)
        # Ink boxes relative to the baseline (top() is negative)
        top_ink = top_metrics.tightBoundingRect(self._top)
        unit_ink = unit_metrics.tightBoundingRect(self._unit)

        # Center the block from the number's top to the unit's baseline;
        # descenders such as the "g" in "gün" may hang below it
        block = top_ink.height() + self._GAP - unit_ink.top()
        top_baseline = (self.height() - block) / 2 - top_ink.top()
        unit_baseline = top_baseline + top_ink.bottom() + self._GAP - unit_ink.top()

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setPen(self._color)
        p.setFont(self._top_font)
        p.drawText(QPointF((self.width() - top_metrics.horizontalAdvance(self._top)) / 2,
                           top_baseline), self._top)
        p.setFont(self._unit_font)
        p.drawText(QPointF((self.width() - unit_metrics.horizontalAdvance(self._unit)) / 2,
                           unit_baseline), self._unit)
        p.end()
