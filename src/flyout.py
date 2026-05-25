"""
flyout.py — Win11-style flyout panel for prayer times.

Displays prayer times, holy day card, and action buttons
in a modern popup above the taskbar widget.
"""

from datetime import datetime, date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QGraphicsDropShadowEffect, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QFont

from src.i18n import (t, get_prayer_name, get_prayer_icon, get_holy_day_name,
                       get_weekday_name, get_month_name, PRAYER_ORDER)
from src.holy_days import get_next_holy_day, get_holy_day_style


class PrayerFlyout(QWidget):
    """Win11 Quick-Settings-style flyout for prayer times."""

    def __init__(self, prayer_widget):
        super().__init__(None)
        self.prayer_widget = prayer_widget
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.Popup
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(340)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self._build_ui()

        # Auto-close when window loses focus
        self._close_timer = QTimer(self)
        self._close_timer.timeout.connect(self._check_active)
        self._close_timer.start(300)

    def _check_active(self):
        if not self.isActiveWindow():
            self._close_timer.stop()
            self.close()

    def _build_ui(self):
        container = QWidget(self)
        container.setObjectName("FlyoutContainer")
        container.setStyleSheet("""
            QWidget#FlyoutContainer {
                background-color: #2b2b2b;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(5)

        # ═══════ HEADER ═══════
        city_name = self.prayer_widget.city_name or t('prayer_times')
        header_label = QLabel(city_name)
        header_label.setStyleSheet(
            "color: #ffffff; font-family: 'Segoe UI Variable Display'; "
            "font-size: 15pt; font-weight: 600; background: transparent; border: none;"
        )
        layout.addWidget(header_label)

        # Date row: Miladi · Hijri
        today = datetime.now().date()
        now = datetime.now()

        weekday = get_weekday_name(now.weekday())
        month = get_month_name(now.month)
        miladi_str = f"{weekday}, {now.day} {month} {now.year}"

        hijri_str = self.prayer_widget.hijri_dates.get(today, "")

        date_row = QHBoxLayout()
        date_row.setSpacing(0)
        date_row.setContentsMargins(0, 0, 0, 0)

        miladi_label = QLabel(miladi_str)
        miladi_label.setStyleSheet(
            "color: #8a8a8a; font-family: 'Segoe UI'; font-size: 9pt; "
            "background: transparent; border: none;"
        )
        date_row.addWidget(miladi_label)

        if hijri_str:
            dot = QLabel("  ·  ")
            dot.setStyleSheet(
                "color: #555555; font-family: 'Segoe UI'; font-size: 9pt; "
                "background: transparent; border: none;"
            )
            date_row.addWidget(dot)
            hicri_label = QLabel(hijri_str)
            hicri_label.setStyleSheet(
                "color: #8a8a8a; font-family: 'Segoe UI'; font-size: 9pt; "
                "background: transparent; border: none;"
            )
            date_row.addWidget(hicri_label)

        date_row.addStretch()
        layout.addLayout(date_row)

        layout.addSpacing(8)
        layout.addWidget(self._make_separator())
        layout.addSpacing(4)

        # ═══════ HOLY DAYS ═══════
        holy_date, holy_key, holy_day_num = get_next_holy_day()
        if holy_date and holy_key:
            layout.addWidget(self._create_holy_day_card(holy_date, holy_key, holy_day_num))
            layout.addSpacing(4)
            layout.addWidget(self._make_separator())
            layout.addSpacing(4)

        # ═══════ PRAYER TIMES ═══════
        now_time = datetime.now()
        daily_times = self.prayer_widget.daily_times

        if today in daily_times:
            times_today = daily_times[today]

            # Find next prayer
            next_p = None
            for p_key in PRAYER_ORDER:
                if p_key in times_today:
                    p_time = times_today[p_key]
                    pt = datetime.strptime(p_time.strip(), "%H:%M").replace(
                        year=now_time.year, month=now_time.month, day=now_time.day
                    )
                    if pt > now_time:
                        next_p = p_key
                        break

            # Render all prayer rows
            for p_key in PRAYER_ORDER:
                if p_key in times_today:
                    p_time = times_today[p_key]
                    pt = datetime.strptime(p_time.strip(), "%H:%M").replace(
                        year=now_time.year, month=now_time.month, day=now_time.day
                    )
                    time_str = p_time.strip()
                    icon = get_prayer_icon(p_key)
                    display_name = get_prayer_name(p_key)
                    is_current = (p_key == next_p)
                    is_past = (pt < now_time)
                    is_iftar = (p_key == 'maghrib' and self.prayer_widget.is_ramadan)
                    layout.addWidget(self._create_prayer_row(
                        icon, display_name, time_str, is_current, is_past, is_iftar
                    ))

        layout.addSpacing(6)
        layout.addWidget(self._make_separator())

        # ═══════ FOOTER ═══════
        footer = QHBoxLayout()
        footer.setSpacing(5)
        footer.setContentsMargins(0, 4, 0, 0)

        # Monitor buttons (only if >1)
        taskbars = self.prayer_widget.taskbars
        if len(taskbars) > 1:
            for i, (name, hwnd) in enumerate(taskbars):
                is_active = (i == self.prayer_widget.current_monitor_index)
                btn = self._make_monitor_btn(name, i, is_active)
                footer.addWidget(btn)

            sep = QLabel("│")
            sep.setStyleSheet(
                "color: #3d3d3d; font-size: 12pt; background: transparent; border: none;"
            )
            sep.setFixedWidth(14)
            footer.addWidget(sep)

        # Position buttons
        left_btn = self._make_icon_btn("◂")
        left_btn.mousePressEvent = lambda e: self.prayer_widget.adjust_position(20)
        footer.addWidget(left_btn)

        right_btn = self._make_icon_btn("▸")
        right_btn.mousePressEvent = lambda e: self.prayer_widget.adjust_position(-20)
        footer.addWidget(right_btn)

        footer.addStretch()

        # Settings button
        settings_btn = self._make_icon_btn("⚙")
        settings_btn.mousePressEvent = lambda e: self._open_settings()
        footer.addWidget(settings_btn)

        # Close button
        exit_btn = self._make_icon_btn("✕")
        exit_btn.mousePressEvent = lambda e: self._quit_app()
        footer.addWidget(exit_btn)

        layout.addLayout(footer)

    # ─── Helper Methods ───

    def _make_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.08); border: none; max-height: 1px;"
        )
        return line

    def _create_holy_day_card(self, holy_date, holy_key, day_num=None):
        """Create a gradient card for the next holy day."""
        style = get_holy_day_style(holy_key)

        # Build display name
        name = get_holy_day_name(holy_key)
        if day_num:
            name = f"{name} — {t('day')} {day_num}"

        card = QWidget()
        card.setFixedHeight(100)
        card.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0.3,
                    stop:0 {style['grad_start']},
                    stop:0.45 {style['grad_mid']},
                    stop:1.0 {style['grad_end']});
                border: none;
                border-radius: 10px;
            }}
        """)

        v_layout = QVBoxLayout(card)
        v_layout.setContentsMargins(16, 10, 14, 10)
        v_layout.setSpacing(1)

        # Line 1: Countdown
        delta = (holy_date - date.today()).days
        countdown_row = QHBoxLayout()
        countdown_row.setSpacing(4)
        countdown_row.setContentsMargins(0, 0, 0, 0)

        if delta == 0:
            num_label = QLabel("✦")
            num_label.setStyleSheet(
                "color: #ffffff; font-family: 'Segoe UI Variable Display'; "
                "font-size: 22pt; font-weight: 700; background: transparent; border: none;"
            )
            countdown_row.addWidget(num_label)
            unit_label = QLabel(t('today'))
            unit_label.setStyleSheet(
                "color: #ffffff; font-family: 'Segoe UI'; font-size: 11pt; "
                "font-weight: 600; background: transparent; border: none;"
            )
            countdown_row.addWidget(unit_label, alignment=Qt.AlignmentFlag.AlignBottom)
        elif delta == 1:
            num_label = QLabel(t('tomorrow'))
            num_label.setStyleSheet(
                "color: #ffffff; font-family: 'Segoe UI Variable Display'; "
                "font-size: 22pt; font-weight: 700; background: transparent; border: none;"
            )
            countdown_row.addWidget(num_label)
        else:
            num_label = QLabel(str(delta))
            num_label.setStyleSheet(
                "color: #ffffff; font-family: 'Segoe UI Variable Display'; "
                "font-size: 22pt; font-weight: 700; background: transparent; border: none;"
            )
            countdown_row.addWidget(num_label)
            unit_label = QLabel(t('days'))
            unit_label.setStyleSheet(
                "color: #ffffff; font-family: 'Segoe UI'; font-size: 10pt; "
                "font-weight: 800; background: transparent; border: none; padding-top: 12px;"
            )
            countdown_row.addWidget(unit_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        countdown_row.addStretch()
        v_layout.addLayout(countdown_row)

        # Line 2: Holy day name
        name_label = QLabel(name)
        name_label.setStyleSheet(
            "color: #ffffff; font-family: 'Segoe UI Variable'; font-size: 11pt; "
            "font-weight: 700; background: transparent; border: none;"
        )
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        v_layout.addWidget(name_label)

        # Line 3: Miladi + Hijri date
        month_name = get_month_name(holy_date.month)
        date_str = f"{holy_date.day} {month_name} {holy_date.year}"

        hijri_str = self.prayer_widget.hijri_dates.get(holy_date, "")
        if hijri_str:
            info_text = f"{date_str}  │  {hijri_str}"
        else:
            info_text = date_str

        info_label = QLabel(info_text)
        info_label.setStyleSheet(
            "color: rgba(255,255,255,0.55); font-family: 'Segoe UI'; font-size: 8pt; "
            "background: transparent; border: none;"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        v_layout.addWidget(info_label)

        return card

    def _make_small_btn(self, text):
        btn = QLabel(text)
        btn.setStyleSheet("""
            color: #8a8a8a;
            font-family: 'Segoe UI';
            font-size: 8pt;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 5px;
            padding: 4px 10px;
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _make_icon_btn(self, text):
        btn = QLabel(text)
        btn.setStyleSheet("""
            color: #8a8a8a;
            font-family: 'Segoe UI';
            font-size: 9pt;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 5px;
            padding: 3px 8px;
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _make_monitor_btn(self, name, index, is_active):
        btn = QLabel(name)
        if is_active:
            btn.setStyleSheet("""
                color: #60cdff; font-family: 'Segoe UI'; font-size: 8pt; font-weight: 600;
                background-color: rgba(96, 205, 255, 0.12);
                border: 1px solid rgba(96, 205, 255, 0.25);
                border-radius: 4px; padding: 3px 8px;
            """)
        else:
            btn.setStyleSheet("""
                color: #e5e5e5; font-family: 'Segoe UI'; font-size: 8pt;
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px; padding: 3px 8px;
            """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.mousePressEvent = lambda e, idx=index: self._on_monitor_click(idx)
        return btn

    def _on_monitor_click(self, index):
        self.prayer_widget.switch_monitor(index)
        self.close()

    def _create_prayer_row(self, icon, name, time_str, is_current, is_past, is_iftar=False):
        row = QWidget()
        row.setFixedHeight(40)

        if is_iftar and not is_past:
            row.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(255, 180, 50, 0.15),
                        stop:0.5 rgba(255, 200, 80, 0.20),
                        stop:1 rgba(255, 180, 50, 0.15));
                    border: 1px solid rgba(255, 190, 60, 0.35);
                    border-radius: 8px;
                }
            """)
            name_color = "#ffc850"
            time_color = "#ffc850"
            font_weight = "600"
            name = f"✦ {t('iftar')} ✦"
            icon = "🌙"
        elif is_current:
            row.setStyleSheet("""
                QWidget {
                    background-color: rgba(96, 205, 255, 0.12);
                    border: 1px solid rgba(96, 205, 255, 0.25);
                    border-radius: 8px;
                }
            """)
            name_color = "#60cdff"
            time_color = "#60cdff"
            font_weight = "600"
        elif is_past:
            row.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 8px;
                }
            """)
            name_color = "#7a7a7a"
            time_color = "#6a6a6a"
            font_weight = "400"
        else:
            row.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 8px;
                }
            """)
            name_color = "#e5e5e5"
            time_color = "#b0b0b0"
            font_weight = "400"

        h_layout = QHBoxLayout(row)
        h_layout.setContentsMargins(12, 0, 14, 0)
        h_layout.setSpacing(0)

        icon_label = QLabel(icon)
        icon_label.setFixedWidth(28)
        icon_label.setStyleSheet("font-size: 14pt; background: transparent; border: none;")
        h_layout.addWidget(icon_label)

        name_label = QLabel(name)
        name_label.setStyleSheet(
            f"color: {name_color}; font-family: 'Segoe UI Variable'; font-size: 10pt; "
            f"font-weight: {font_weight}; background: transparent; border: none;"
        )
        h_layout.addWidget(name_label)

        h_layout.addStretch()

        time_label = QLabel(time_str)
        time_label.setStyleSheet(
            f"color: {time_color}; font-family: 'Segoe UI'; font-size: 10pt; "
            f"font-weight: {font_weight}; background: transparent; border: none;"
        )
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h_layout.addWidget(time_label)

        return row

    def _open_settings(self):
        """Open the settings window."""
        self.close()
        from src.settings_window import SettingsWindow
        self.prayer_widget._settings_window = SettingsWindow(self.prayer_widget)
        self.prayer_widget._settings_window.show()
        self.prayer_widget._settings_window.raise_()
        self.prayer_widget._settings_window.activateWindow()

    def _quit_app(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()

    def sizeHint(self):
        return self.layout().sizeHint() if self.layout() else super().sizeHint()

    def focusOutEvent(self, event):
        self.close()
        super().focusOutEvent(event)
