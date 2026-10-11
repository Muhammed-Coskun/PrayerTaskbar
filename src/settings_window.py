"""
Settings window for the Prayer Times Taskbar Widget.

A normal app window in the style of the Windows 11 Settings app, with
setting cards grouped into:
- Prayer times: location search (Diyanet API) and Excel import
- Taskbar: screen and position of the widget
- General: language and autostart
- About: version, project link and quitting the app

Every change applies immediately; there is no save button.
"""

import logging
import os
import shutil
import threading

from PyQt6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)
from PyQt6.QtCore import Qt, QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QCursor, QDesktopServices, QGuiApplication

from src import autostart
from src import updater
from src import widget as widget_module
from src.config import APP_VERSION, load_config, save_config, get_cache_path, get_data_dir
from src.controls import ComboBox, SettingsCard, ToggleSwitch, accent_button, hyperlink_button
from src.data_loader import search_locations, fetch_prayer_times, save_cache, get_coordinates
from src.i18n import t, set_language
from src.theme import (app_theme, css, font, icon_font, set_caption_color, set_dark_title_bar,
                       GLYPH_MAP_PIN, GLYPH_DOCUMENT, GLYPH_MONITOR, GLYPH_MOVE,
                       GLYPH_LANGUAGE, GLYPH_START, GLYPH_INFO, GLYPH_POWER,
                       GLYPH_CHEVRON_LEFT, GLYPH_CHEVRON_RIGHT)
from src.win32_helpers import find_all_taskbars, get_window_rect, native_to_qt

logger = logging.getLogger(__name__)

LANGUAGE_ITEMS = [
    ("English", "en"),
    ("Türkçe", "tr"),
    ("Deutsch", "de"),
]
"""Display-name / code pairs for the language combo box."""

GITHUB_URL = "https://github.com/Muhammed-Coskun/PrayerTaskbar"
DIYANET_URL = "https://namazvakitleri.diyanet.gov.tr"

_MAX_RESULTS = 8
_SEARCH_DELAY_MS = 450
_POSITION_STEP = 20

_window: "SettingsWindow | None" = None


def show_settings() -> None:
    """Open the settings window, or bring it to the front if it is open."""
    global _window
    if _window is None:
        _window = SettingsWindow()
        _window.destroyed.connect(_forget_window)
    if _window.isMinimized():
        _window.showNormal()
    _window.show()
    _window.raise_()
    _window.activateWindow()


def _forget_window(*_args) -> None:
    global _window
    _window = None


def start_update() -> None:
    """Show the settings (with the download progress) and install the update."""
    show_settings()
    if updater.instance() is not None:
        updater.instance().install()


def _active_widget():
    """The live taskbar widget (it is replaced when it switches screens)."""
    return widget_module._active_widget


class _Bridge(QObject):
    """Delivers results of background requests to the UI thread."""
    done = pyqtSignal(object, object)


class SettingsWindow(QWidget):
    """Windows 11 style settings window (single instance via show_settings)."""

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("PrayerTaskbar")
        self.setMinimumSize(480, 420)
        self.theme = app_theme()

        self._bridge = _Bridge(self)
        self._bridge.done.connect(lambda callback, result: callback(result))
        self._search_id = 0
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(_SEARCH_DELAY_MS)
        self._search_timer.timeout.connect(self._start_search)

        self._update_button: QPushButton | None = None
        if updater.instance() is not None:
            updater.instance().available.connect(self._on_update_available)
            updater.instance().progress.connect(self._on_update_progress)
            updater.instance().failed.connect(self._on_update_failed)

        self.setObjectName("SettingsWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet(
            f"QWidget#SettingsWindow {{ background: {css(self.theme.window_bg)}; }}"
            "QScrollArea { background: transparent; border: none; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.viewport().setAutoFillBackground(False)
        layout.addWidget(self._scroll)

        self._build_page()
        self._place_window()

        # Title bar in the window color, like Windows 11 apps
        hwnd = int(self.winId())
        set_dark_title_bar(hwnd, self.theme.dark)
        set_caption_color(hwnd, self.theme.window_bg)

    def _place_window(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        width = min(640, avail.width() - 80)
        height = min(780, avail.height() - 80)
        self.resize(width, height)
        self.move(avail.x() + (avail.width() - width) // 2,
                  avail.y() + (avail.height() - height) // 2)

    # ------------------------------------------------------------------
    # Page
    # ------------------------------------------------------------------

    def _build_page(self) -> None:
        """Build all cards; called again after a language change."""
        page = QWidget()
        page.setObjectName("Page")
        v = QVBoxLayout(page)
        v.setContentsMargins(28, 20, 28, 28)
        v.setSpacing(4)

        title = self._label(t("settings"), 28, self.theme.text, semibold=True, display=True)
        v.addWidget(title)

        cfg = load_config()

        self._add_group(v, t("prayer_times"))
        v.addWidget(self._build_location_card(cfg))
        v.addWidget(self._build_excel_card(cfg))

        self._add_group(v, t("taskbar"))
        v.addWidget(self._build_screen_card(cfg))
        v.addWidget(self._build_position_card())

        self._add_group(v, t("general"))
        v.addWidget(self._build_language_card(cfg))
        v.addWidget(self._build_autostart_card())

        self._add_group(v, t("about"))
        v.addWidget(self._build_about_card())
        v.addWidget(self._build_quit_card())
        v.addStretch()

        # Replaces (and deletes) the previous page
        self._scroll.setWidget(page)

    def _rebuild(self) -> None:
        scrollbar = self._scroll.verticalScrollBar()
        position = scrollbar.value()
        self._search_id += 1  # drop results of searches still running
        self._build_page()
        QTimer.singleShot(0, lambda: scrollbar.setValue(position))

    def _add_group(self, layout: QVBoxLayout, text: str) -> None:
        layout.addSpacing(20)
        layout.addWidget(self._label(text, 14, self.theme.text, semibold=True))
        layout.addSpacing(4)

    def _label(self, text: str, px: int, color, semibold: bool = False,
               display: bool = False) -> QLabel:
        label = QLabel(text)
        label.setFont(font(px, semibold=semibold, display=display))
        label.setStyleSheet(f"color: {css(color)};")
        return label

    # ------------------------------------------------------------------
    # Prayer times: location
    # ------------------------------------------------------------------

    @staticmethod
    def _location_text(cfg: dict) -> str:
        if get_coordinates(cfg) is None:
            return t("location_none")
        return cfg.get("location_name") or t("location_none")

    def _build_location_card(self, cfg: dict) -> SettingsCard:
        th = self.theme
        card = SettingsCard(th, GLYPH_MAP_PIN, t("location"), self._location_text(cfg))
        self._location_card = card

        body = QWidget()
        bv = QVBoxLayout(body)
        # Indent to the card title: 16 margin + 22 icon + 16 spacing
        bv.setContentsMargins(54, 12, 16, 14)
        bv.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(8)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(t("search_placeholder"))
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setFont(font(14))
        self._search_input.setMinimumHeight(32)
        self._search_input.textEdited.connect(lambda _text: self._search_timer.start())
        self._search_input.returnPressed.connect(self._start_search)
        row.addWidget(self._search_input, 1)

        search_btn = accent_button(t("search"), th)
        search_btn.clicked.connect(self._start_search)
        row.addWidget(search_btn)
        bv.addLayout(row)

        self._results_layout = QVBoxLayout()
        self._results_layout.setSpacing(2)
        bv.addLayout(self._results_layout)

        self._status_label = QLabel()
        self._status_label.setFont(font(12))
        self._status_label.setWordWrap(True)
        self._status_label.hide()
        bv.addWidget(self._status_label)

        card.add_body(body)
        return card

    def _set_status(self, text: str, color=None) -> None:
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color: {css(color or self.theme.text_secondary)};")
        self._status_label.setVisible(bool(text))

    def _clear_results(self) -> None:
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _start_search(self) -> None:
        self._search_timer.stop()
        query = self._search_input.text().strip()
        self._search_id += 1
        search_id = self._search_id
        if len(query) < 2:
            self._clear_results()
            self._set_status("")
            return
        self._set_status(t("searching"))
        self._run_async(lambda: search_locations(query, raise_errors=True),
                        lambda results: self._show_results(search_id, query, results))

    @staticmethod
    def _rank_results(query: str, results: list[dict]) -> list[dict]:
        """Put exact and prefix matches first; the API also returns fuzzy matches."""
        q = query.casefold()

        def rank(location: dict) -> int:
            names = [str(location.get(k) or "").casefold() for k in ("name", "ascii_name")]
            if q in names:
                return 0
            if any(name.startswith(q) for name in names):
                return 1
            if any(q in name for name in names):
                return 2
            return 3

        return sorted(results, key=rank)

    def _show_results(self, search_id: int, query: str, results) -> None:
        if search_id != self._search_id:
            return  # a newer search is running
        self._clear_results()
        if results is None:
            self._set_status(t("search_failed"), self.theme.critical)
            return
        if not results:
            self._set_status(t("no_results"))
            return
        self._set_status("")
        for location in self._rank_results(query, results)[:_MAX_RESULTS]:
            item = _ResultItem(self.theme, location)
            item.clicked.connect(lambda _checked, loc=location: self._select_location(loc))
            self._results_layout.addWidget(item)

    @staticmethod
    def _format_location(location: dict) -> str:
        """Build a readable name string from a location dict."""
        parts = [str(location[key]) for key in ("name", "country_code") if location.get(key)]
        return ", ".join(parts) if parts else str(location.get("id", ""))

    def _select_location(self, location: dict) -> None:
        """Save the selected location and load its prayer times."""
        location_id = location.get("id")
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        name = self._format_location(location)

        cfg = load_config()
        cfg.update({
            "location_id": location_id,
            "location_name": name,
            "latitude": latitude,
            "longitude": longitude,
            "data_source": "api",
        })
        save_config(cfg)

        self._search_id += 1
        self._clear_results()
        self._search_input.clear()
        self._location_card.set_description(name)
        self._excel_card.set_description(self._excel_text(cfg))

        if latitude is None or longitude is None:
            self._set_status(t("times_failed"), self.theme.critical)
            return
        self._set_status(t("loading_times"))
        self._run_async(lambda: fetch_prayer_times(latitude, longitude),
                        lambda raw: self._on_times_loaded(location_id, raw))

    def _on_times_loaded(self, location_id, raw) -> None:
        if load_config().get("location_id") != location_id:
            return  # another location was picked in the meantime
        if raw:
            save_cache(get_cache_path(), location_id, raw)
            self._set_status(t("times_loaded"), self.theme.success)
        else:
            self._set_status(t("times_failed"), self.theme.critical)
        widget = _active_widget()
        if widget is not None:
            widget.reload_data()

    # ------------------------------------------------------------------
    # Prayer times: Excel import
    # ------------------------------------------------------------------

    @staticmethod
    def _excel_text(cfg: dict) -> str:
        path = cfg.get("excel_path")
        if cfg.get("data_source") == "excel" and path:
            return t("excel_active").format(name=os.path.basename(path))
        return t("excel_desc")

    def _build_excel_card(self, cfg: dict) -> SettingsCard:
        browse = QPushButton(t("browse"))
        browse.setFont(font(14))
        browse.setMinimumHeight(32)
        browse.setCursor(Qt.CursorShape.PointingHandCursor)
        browse.clicked.connect(self._on_import_excel)

        card = SettingsCard(self.theme, GLYPH_DOCUMENT, t("excel_title"),
                            self._excel_text(cfg), browse)
        link = hyperlink_button(t("download_link"), self.theme, inline=True)
        link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DIYANET_URL)))
        card.add_text_widget(link)
        self._excel_card = card
        return card

    def _on_import_excel(self) -> None:
        """Copy the chosen XLSX into data/ and use it as the data source."""
        path, _ = QFileDialog.getOpenFileName(self, t("excel_title"), "", "Excel (*.xlsx)")
        if not path:
            return
        dest = os.path.join(get_data_dir(), os.path.basename(path))
        try:
            shutil.copy2(path, dest)
        except shutil.SameFileError:
            pass

        cfg = load_config()
        cfg["data_source"] = "excel"
        cfg["excel_path"] = dest
        save_config(cfg)
        self._excel_card.set_description(self._excel_text(cfg))
        widget = _active_widget()
        if widget is not None:
            widget.reload_data()

    # ------------------------------------------------------------------
    # Taskbar: screen and position
    # ------------------------------------------------------------------

    @staticmethod
    def _screen_label(index: int, taskbar_hwnd: int) -> str:
        label = t("screen_n").format(n=index + 1)
        left, top, right, bottom = get_window_rect(taskbar_hwnd)
        _point, screen = native_to_qt((left + right) // 2, (top + bottom) // 2)
        if screen is not None and screen.name():
            label = f"{label} · {screen.name()}"
        return label

    def _build_screen_card(self, cfg: dict) -> SettingsCard:
        combo = ComboBox()
        combo.setFont(font(14))
        combo.setMinimumHeight(32)
        combo.setMinimumWidth(200)
        taskbars = find_all_taskbars()
        for index, (_name, hwnd) in enumerate(taskbars):
            combo.addItem(self._screen_label(index, hwnd), index)
        if not taskbars:
            combo.addItem(t("screen_n").format(n=1), 0)

        widget = _active_widget()
        current = widget.current_monitor_index if widget is not None else cfg.get("monitor_index", 0)
        combo.setCurrentIndex(max(0, min(current, combo.count() - 1)))
        combo.setEnabled(len(taskbars) > 1)
        combo.currentIndexChanged.connect(lambda i: self._on_screen_changed(combo.itemData(i)))
        return SettingsCard(self.theme, GLYPH_MONITOR, t("screen"), t("screen_desc"), combo)

    @staticmethod
    def _on_screen_changed(index) -> None:
        if index is None:
            return
        widget = _active_widget()
        if widget is not None:
            widget.switch_monitor(index)
        else:
            cfg = load_config()
            cfg["monitor_index"] = index
            save_config(cfg)

    def _build_position_card(self) -> SettingsCard:
        buttons = QWidget()
        h = QHBoxLayout(buttons)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        for glyph, tooltip, delta in (
            (GLYPH_CHEVRON_LEFT, t("move_left"), _POSITION_STEP),
            (GLYPH_CHEVRON_RIGHT, t("move_right"), -_POSITION_STEP),
        ):
            btn = QPushButton(glyph)
            btn.setFont(icon_font(12))
            btn.setFixedSize(40, 32)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Keep moving while the button is held down
            btn.setAutoRepeat(True)
            btn.setAutoRepeatDelay(400)
            btn.setAutoRepeatInterval(80)
            btn.clicked.connect(lambda _checked, d=delta: self._move_widget(d))
            h.addWidget(btn)
        return SettingsCard(self.theme, GLYPH_MOVE, t("position"), t("position_desc"), buttons)

    @staticmethod
    def _move_widget(delta: int) -> None:
        widget = _active_widget()
        if widget is not None:
            widget.adjust_position(delta)

    # ------------------------------------------------------------------
    # General: language and autostart
    # ------------------------------------------------------------------

    def _build_language_card(self, cfg: dict) -> SettingsCard:
        combo = ComboBox()
        combo.setFont(font(14))
        combo.setMinimumHeight(32)
        combo.setMinimumWidth(160)
        current = cfg.get("language", "en")
        for display, code in LANGUAGE_ITEMS:
            combo.addItem(display, code)
            if code == current:
                combo.setCurrentIndex(combo.count() - 1)
        combo.currentIndexChanged.connect(lambda i: self._on_language_changed(combo.itemData(i)))
        return SettingsCard(self.theme, GLYPH_LANGUAGE, t("language"), t("language_desc"), combo)

    def _on_language_changed(self, code) -> None:
        if not code:
            return
        cfg = load_config()
        cfg["language"] = code
        save_config(cfg)
        set_language(code)
        widget = _active_widget()
        if widget is not None:
            widget.reload_data()
        # Rebuild after the combo box finished handling its signal
        QTimer.singleShot(0, self._rebuild)

    def _build_autostart_card(self) -> SettingsCard:
        control = QWidget()
        h = QHBoxLayout(control)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)
        state = self._label("", 14, self.theme.text)
        switch = ToggleSwitch(self.theme)
        switch.setChecked(autostart.is_enabled())
        state.setText(t("on") if switch.isChecked() else t("off"))

        def on_toggled(checked: bool) -> None:
            if not autostart.set_enabled(checked):
                switch.blockSignals(True)
                switch.setChecked(not checked)
                switch.blockSignals(False)
            state.setText(t("on") if switch.isChecked() else t("off"))

        switch.toggled.connect(on_toggled)
        h.addWidget(state)
        h.addWidget(switch)
        return SettingsCard(self.theme, GLYPH_START, t("autostart_title"),
                            t("autostart_desc"), control)

    # ------------------------------------------------------------------
    # About
    # ------------------------------------------------------------------

    def _build_about_card(self) -> SettingsCard:
        update = updater.available_update()
        if update is None:
            self._update_button = None
            link = hyperlink_button("GitHub", self.theme)
            link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
            return SettingsCard(self.theme, GLYPH_INFO, "PrayerTaskbar",
                                t("about_desc").format(version=APP_VERSION), link)

        # A newer version exists: offer to install it right here
        self._update_button = accent_button(t("update_now"), self.theme)
        self._update_button.clicked.connect(start_update)
        if updater.instance().installing:
            self._update_button.setEnabled(False)
        self._about_card = SettingsCard(self.theme, GLYPH_INFO, "PrayerTaskbar",
                                        t("update_available").format(version=update["version"]),
                                        self._update_button)
        return self._about_card

    def _on_update_available(self, _release: dict) -> None:
        QTimer.singleShot(0, self._rebuild)

    def _on_update_progress(self, percent: int) -> None:
        if self._update_button is not None:
            self._update_button.setEnabled(False)
            self._update_button.setText(t("update_downloading").format(percent=percent))

    def _on_update_failed(self) -> None:
        if self._update_button is not None:
            self._update_button.setEnabled(True)
            self._update_button.setText(t("update_now"))
            self._about_card.set_description(t("update_failed"))

    def _build_quit_card(self) -> SettingsCard:
        quit_btn = QPushButton(t("quit"))
        quit_btn.setFont(font(14))
        quit_btn.setMinimumHeight(32)
        quit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        quit_btn.clicked.connect(QApplication.instance().quit)
        return SettingsCard(self.theme, GLYPH_POWER, t("quit_title"), t("quit_desc"), quit_btn)

    # ------------------------------------------------------------------
    # Background work
    # ------------------------------------------------------------------

    def _run_async(self, work, callback) -> None:
        """Run *work* in a thread and pass its result (None on error) to *callback*."""
        bridge = self._bridge

        def run():
            try:
                result = work()
            except Exception:
                logger.exception("Background request failed")
                result = None
            try:
                bridge.done.emit(callback, result)
            except RuntimeError:
                pass  # the window was closed in the meantime

        threading.Thread(target=run, daemon=True).start()


class _ResultItem(QPushButton):
    """One search result: place name and country / time zone."""

    def __init__(self, theme, location: dict) -> None:
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-radius: 4px; }}"
            f"QPushButton:hover {{ background: {css(theme.subtle_hover)}; }}"
            f"QPushButton:pressed {{ background: {css(theme.subtle_pressed)}; }}"
        )
        h = QHBoxLayout(self)
        h.setContentsMargins(10, 0, 10, 0)
        h.setSpacing(12)

        name = QLabel(location.get("name") or str(location.get("id", "")))
        name.setFont(font(14))
        name.setStyleSheet(f"color: {css(theme.text)};")
        h.addWidget(name)
        h.addStretch()

        details = " · ".join(str(location[k]) for k in ("country_code", "timezone") if location.get(k))
        detail = QLabel(details)
        detail.setFont(font(12))
        detail.setStyleSheet(f"color: {css(theme.text_secondary)};")
        h.addWidget(detail)

        for label in (name, detail):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
