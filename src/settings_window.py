"""
Settings dialog for the Prayer Times Taskbar Widget.

Provides a Win11-style dark frameless window with sections for:
- Language selection (English / Turkish / German)
- Location search via the Diyanet API
- Excel prayer data upload
- Default monitor selection
- Windows autostart toggle (registry-based)
- About information

The window closes when it loses focus and notifies the parent
prayer widget to reload its data on close.
"""

import os
import sys
import json
import shutil
import webbrowser
import winreg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QLineEdit, QPushButton, QFileDialog,
                              QGraphicsDropShadowEffect, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from src.config import load_config, save_config, get_data_dir, get_executable_path, is_frozen
from src.i18n import t, set_language, get_language
from src.data_loader import search_locations, fetch_prayer_times, save_cache, parse_api_data
from src.config import get_cache_path


# ---------------------------------------------------------------------------
# Language mapping
# ---------------------------------------------------------------------------

LANGUAGE_ITEMS = [
    ("English", "en"),
    ("Türkçe", "tr"),
    ("Deutsch", "de"),
]
"""Display-name / code pairs for the language combo box."""


# ---------------------------------------------------------------------------
# Shared stylesheet fragments
# ---------------------------------------------------------------------------

_LABEL_STYLE = "color: #b0b0b0; font-size: 9pt; font-family: 'Segoe UI';"

_INPUT_STYLE = """
    background: #3d3d3d;
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 10px;
    font-family: 'Segoe UI';
"""

_BUTTON_STYLE = """
    background: rgba(96, 205, 255, 0.15);
    color: #60cdff;
    border: 1px solid rgba(96, 205, 255, 0.25);
    border-radius: 6px;
    padding: 8px 16px;
    font-family: 'Segoe UI';
"""

_COMBO_STYLE = """
    QComboBox {
        background: #3d3d3d;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        padding: 6px 10px;
        font-family: 'Segoe UI';
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background: #3d3d3d;
        color: white;
        selection-background-color: rgba(96, 205, 255, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-family: 'Segoe UI';
    }
"""

_SEPARATOR_STYLE = (
    "background: rgba(255, 255, 255, 0.08); min-height: 1px; max-height: 1px;"
)


# ---------------------------------------------------------------------------
# SettingsWindow
# ---------------------------------------------------------------------------

class SettingsWindow(QWidget):
    """Win11-style dark settings dialog.

    Args:
        prayer_widget: The main prayer widget instance.  A reference is kept
            so the widget can be told to reload data when the settings dialog
            is closed or the user changes data-related options.
    """

    def __init__(self, prayer_widget=None):
        super().__init__()
        self.prayer_widget = prayer_widget
        self.config = load_config()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._focus_timer = QTimer(self)
        self._focus_timer.setInterval(250)
        self._focus_timer.timeout.connect(self._check_active)
        self._has_gained_focus = False

        self._setup_window()
        self._build_ui()
        self._center_on_screen()
        self._focus_timer.start()

    # ------------------------------------------------------------------
    # Window configuration
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configure frameless, translucent, always-on-top window flags."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)

        # Drop shadow around the dialog
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

    def _center_on_screen(self) -> None:
        """Position the window at the centre of the primary screen."""
        screen = self.screen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2
        self.move(x, y)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct all UI sections inside a dark rounded container."""
        # Outer layout (holds the styled container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        # Container frame with dark background
        container = QFrame(self)
        container.setStyleSheet(
            "QFrame { background: #2b2b2b; border-radius: 12px; }"
        )
        outer.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # --- Header ---
        layout.addLayout(self._build_header())
        layout.addWidget(self._separator())

        # --- Language ---
        layout.addLayout(self._build_language_section())
        layout.addWidget(self._separator())

        # --- Location search ---
        layout.addLayout(self._build_location_section())
        layout.addWidget(self._separator())

        # --- Excel upload ---
        layout.addLayout(self._build_excel_section())
        layout.addWidget(self._separator())

        # --- Default screen ---
        layout.addLayout(self._build_screen_section())
        layout.addWidget(self._separator())

        # --- Autostart ---
        layout.addLayout(self._build_autostart_section())
        layout.addWidget(self._separator())

        # --- About ---
        layout.addLayout(self._build_about_section())
        layout.addWidget(self._separator())

        # --- Save / Close ---
        layout.addLayout(self._build_footer_buttons())

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self) -> QHBoxLayout:
        """Title bar with 'Settings' text and a close button."""
        row = QHBoxLayout()

        title = QLabel(t("settings"))
        title.setFont(QFont("Segoe UI", 15))
        title.setStyleSheet("color: white;")
        row.addWidget(title)

        row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton { color: #b0b0b0; background: transparent; border: none; "
            "font-size: 14pt; font-family: 'Segoe UI'; }"
            "QPushButton:hover { color: white; }"
        )
        close_btn.clicked.connect(self._on_close)
        row.addWidget(close_btn)

        return row

    # ------------------------------------------------------------------
    # Language section
    # ------------------------------------------------------------------

    def _build_language_section(self) -> QVBoxLayout:
        """Language label + combo box."""
        section = QVBoxLayout()
        section.setSpacing(6)

        lbl = QLabel(t("language"))
        lbl.setStyleSheet(_LABEL_STYLE)
        section.addWidget(lbl)

        self.lang_combo = QComboBox()
        self.lang_combo.setStyleSheet(_COMBO_STYLE)
        current_lang = self.config.get("language", "en")
        selected_idx = 0

        for idx, (display, code) in enumerate(LANGUAGE_ITEMS):
            self.lang_combo.addItem(display, code)
            if code == current_lang:
                selected_idx = idx

        self.lang_combo.setCurrentIndex(selected_idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        section.addWidget(self.lang_combo)

        return section

    def _on_language_changed(self, index: int) -> None:
        """Apply the newly selected language immediately."""
        code = self.lang_combo.itemData(index)
        if code:
            set_language(code)
            self.config["language"] = code
            save_config(self.config)

    # ------------------------------------------------------------------
    # Location section
    # ------------------------------------------------------------------

    def _build_location_section(self) -> QVBoxLayout:
        """Location search input, button, results list, and status."""
        section = QVBoxLayout()
        section.setSpacing(6)

        lbl = QLabel(t("location"))
        lbl.setStyleSheet(_LABEL_STYLE)
        section.addWidget(lbl)

        # Search input + button row
        row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("e.g. Berlin, Ankara...")
        self.search_input.setStyleSheet(_INPUT_STYLE)
        row.addWidget(self.search_input)

        self.search_btn = QPushButton(t("search"))
        self.search_btn.setStyleSheet(_BUTTON_STYLE)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.clicked.connect(self._on_search)
        row.addWidget(self.search_btn)
        section.addLayout(row)

        # Results container
        self.results_layout = QVBoxLayout()
        self.results_layout.setSpacing(2)
        section.addLayout(self.results_layout)

        # Current location status
        loc_name = self.config.get("location_name", "") or "Not set"
        self.location_status = QLabel(f"📍 {loc_name}")
        self.location_status.setStyleSheet(
            "color: #60cdff; font-size: 9pt; font-family: 'Segoe UI';"
        )
        section.addWidget(self.location_status)

        return section

    def _on_search(self) -> None:
        """Start a location search with a small debounce delay."""
        self.search_btn.setEnabled(False)
        self.search_btn.setText(t("loading"))
        self._search_timer.start(150)

    def _do_search(self) -> None:
        """Execute the API location search and display results."""
        query = self.search_input.text().strip()
        if not query:
            self.search_btn.setEnabled(True)
            self.search_btn.setText(t("search"))
            return

        results = search_locations(query)

        # Clear old results
        self._clear_results()

        # Show up to 10 results as clickable labels
        for loc in results[:10]:
            label_text = self._format_location(loc)
            btn = QPushButton(label_text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { color: white; background: transparent; "
                "border: none; text-align: left; padding: 4px 0; "
                "font-family: 'Segoe UI'; font-size: 9pt; }"
                "QPushButton:hover { color: #60cdff; }"
            )
            btn.clicked.connect(lambda checked, l=loc: self._on_location_select(l))
            self.results_layout.addWidget(btn)

        if not results:
            no_res = QLabel(t("no_data"))
            no_res.setStyleSheet("color: #b0b0b0; font-size: 9pt; font-family: 'Segoe UI';")
            self.results_layout.addWidget(no_res)

        self.search_btn.setEnabled(True)
        self.search_btn.setText(t("search"))

    def _on_location_select(self, location: dict) -> None:
        """Save the selected location, fetch prayer times, and update UI."""
        location_id = location.get("id")
        location_name = self._format_location(location)

        self.config["location_id"] = location_id
        self.config["location_name"] = location_name
        self.config["data_source"] = "api"
        save_config(self.config)

        self.location_status.setText(f"📍 {location_name}")
        self._clear_results()

        # Fetch prayer times for the new location
        if location_id:
            raw_data = fetch_prayer_times(location_id)
            if raw_data:
                cache_path = get_cache_path()
                save_cache(cache_path, location_id, raw_data)
                self.location_status.setText(
                    f"📍 {location_name}  ✓ {t('data_loaded')}"
                )

    @staticmethod
    def _format_location(location: dict) -> str:
        """Build a readable name string from a location dict."""
        parts = []
        for key in ("region", "city", "country"):
            val = location.get(key)
            if val:
                parts.append(str(val))
        return ", ".join(parts) if parts else str(location.get("id", ""))

    def _clear_results(self) -> None:
        """Remove all widgets from the search-results layout."""
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    # ------------------------------------------------------------------
    # Excel upload section
    # ------------------------------------------------------------------

    def _build_excel_section(self) -> QVBoxLayout:
        """Excel file picker and Diyanet download link."""
        section = QVBoxLayout()
        section.setSpacing(6)

        lbl = QLabel(t("upload_excel"))
        lbl.setStyleSheet(_LABEL_STYLE)
        section.addWidget(lbl)

        upload_btn = QPushButton("📂 " + t("upload_excel"))
        upload_btn.setStyleSheet(_BUTTON_STYLE)
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_btn.clicked.connect(self._on_upload_excel)
        section.addWidget(upload_btn)

        link = QLabel('📥 <a href="https://namazvakitleri.diyanet.gov.tr" '
                       'style="color:#60cdff;">namazvakitleri.diyanet.gov.tr</a>')
        link.setStyleSheet("font-family: 'Segoe UI'; font-size: 9pt;")
        link.setOpenExternalLinks(True)
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        section.addWidget(link)

        return section

    def _on_upload_excel(self) -> None:
        """Open a file dialog, copy the chosen XLSX into data/, and update config."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("upload_excel"),
            "",
            "Excel Files (*.xlsx)",
        )
        if not path:
            return

        data_dir = get_data_dir()
        dest = os.path.join(data_dir, os.path.basename(path))
        try:
            shutil.copy2(path, dest)
        except shutil.SameFileError:
            pass

        self.config["data_source"] = "excel"
        self.config["excel_path"] = dest
        save_config(self.config)

    # ------------------------------------------------------------------
    # Default screen section
    # ------------------------------------------------------------------

    def _build_screen_section(self) -> QVBoxLayout:
        """Monitor selection combo box."""
        from src.win32_helpers import find_all_taskbars

        section = QVBoxLayout()
        section.setSpacing(6)

        lbl = QLabel(t("default_screen"))
        lbl.setStyleSheet(_LABEL_STYLE)
        section.addWidget(lbl)

        self.screen_combo = QComboBox()
        self.screen_combo.setStyleSheet(_COMBO_STYLE)

        taskbars = find_all_taskbars()
        selected_idx = 0
        monitor_idx = self.config.get("monitor_index", 0)

        for idx, (name, _hwnd) in enumerate(taskbars):
            self.screen_combo.addItem(name, idx)
            if idx == monitor_idx:
                selected_idx = idx

        if not taskbars:
            self.screen_combo.addItem("Screen 1", 0)

        self.screen_combo.setCurrentIndex(selected_idx)
        self.screen_combo.currentIndexChanged.connect(self._on_screen_changed)
        section.addWidget(self.screen_combo)

        return section

    def _on_screen_changed(self, index: int) -> None:
        """Persist the newly selected monitor index."""
        data = self.screen_combo.itemData(index)
        if data is not None:
            self.config["monitor_index"] = data
            save_config(self.config)

    # ------------------------------------------------------------------
    # Autostart section
    # ------------------------------------------------------------------

    def _build_autostart_section(self) -> QVBoxLayout:
        """Autostart checkbox backed by the Windows Run registry key."""
        section = QVBoxLayout()
        section.setSpacing(6)

        self.autostart_cb = QCheckBox(t("autostart"))
        self.autostart_cb.setStyleSheet(
            "QCheckBox { color: white; font-family: 'Segoe UI'; font-size: 9pt; }"
            "QCheckBox::indicator { width: 16px; height: 16px; }"
        )
        self.autostart_cb.setChecked(self._is_autostart_enabled())
        self.autostart_cb.toggled.connect(self._toggle_autostart)
        section.addWidget(self.autostart_cb)

        return section

    @staticmethod
    def _is_autostart_enabled() -> bool:
        """Check if the autostart registry value exists."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            winreg.QueryValueEx(key, "PrayerTaskbar")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    @staticmethod
    def _toggle_autostart(checked: bool) -> None:
        """Write or remove the PrayerWidget autostart registry entry."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ,
            )
            if checked:
                exe_path = get_executable_path()
                winreg.SetValueEx(
                    key, "PrayerTaskbar", 0, winreg.REG_SZ, f'"{exe_path}"'
                )
            else:
                winreg.DeleteValue(key, "PrayerTaskbar")
            winreg.CloseKey(key)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # About section
    # ------------------------------------------------------------------

    def _build_about_section(self) -> QVBoxLayout:
        """Version label and project link."""
        section = QVBoxLayout()
        section.setSpacing(4)

        version = QLabel("PrayerTaskbar")
        version.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 9pt;")
        section.addWidget(version)

        link = QLabel(
            '<a href="https://github.com/Muhammed-Coskun/PrayerTaskbar" '
            'style="color:#60cdff;">github.com/Muhammed-Coskun/PrayerTaskbar</a>'
        )
        link.setStyleSheet("font-family: 'Segoe UI'; font-size: 9pt;")
        link.setOpenExternalLinks(True)
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        section.addWidget(link)

        return section

    # ------------------------------------------------------------------
    # Footer buttons
    # ------------------------------------------------------------------

    def _build_footer_buttons(self) -> QHBoxLayout:
        """Save and Close buttons at the bottom of the dialog."""
        row = QHBoxLayout()
        row.addStretch()

        save_btn = QPushButton(t("save"))
        save_btn.setStyleSheet(_BUTTON_STYLE)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        row.addWidget(save_btn)

        close_btn = QPushButton(t("close"))
        close_btn.setStyleSheet(
            "background: rgba(255,255,255,0.06); color: #b0b0b0; "
            "border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; "
            "padding: 8px 16px; font-family: 'Segoe UI';"
        )
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._on_close)
        row.addWidget(close_btn)

        return row

    def _on_save(self) -> None:
        """Persist the current config and close the dialog."""
        save_config(self.config)
        self._on_close()

    # ------------------------------------------------------------------
    # Close / focus handling
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        """Close the settings window and tell the prayer widget to reload."""
        self._focus_timer.stop()
        self.close()
        if self.prayer_widget is not None and hasattr(self.prayer_widget, "reload_data"):
            self.prayer_widget.reload_data()

    def _check_active(self) -> None:
        """Close the window if it loses focus."""
        if self.isActiveWindow():
            self._has_gained_focus = True
        elif getattr(self, '_has_gained_focus', False) and not self._has_active_child():
            self._focus_timer.stop()
            self._on_close()

    def _has_active_child(self) -> bool:
        """Return True if any child popup (e.g. combo dropdown) is active."""
        active = self.focusWidget()
        if active is not None:
            return True
        # Check combo-box popups which steal focus temporarily
        for combo in self.findChildren(QComboBox):
            view = combo.view()
            if view is not None and view.isVisible():
                return True
        return False

    # ------------------------------------------------------------------
    # Drag and Move Handling
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        """Allow dragging the window natively via the OS."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.windowHandle():
                self.windowHandle().startSystemMove()
            event.accept()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _separator() -> QFrame:
        """Create a subtle horizontal line separator."""
        line = QFrame()
        line.setStyleSheet(_SEPARATOR_STYLE)
        line.setFixedHeight(1)
        return line
