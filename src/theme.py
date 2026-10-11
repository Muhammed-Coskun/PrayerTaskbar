"""
theme.py — Windows 11 (Fluent) look for all windows of the app.

Provides the colors of the WinUI 3 dark and light themes, the user's
Windows accent color, the Segoe UI Variable / Segoe Fluent Icons fonts
and the DWM window effects (rounded corners, acrylic) used by the flyout.

The taskbar widget and the flyout follow the Windows mode (like the
taskbar itself), the settings window follows the app mode.
"""

import ctypes
import winreg
from ctypes import wintypes
from dataclasses import dataclass

from PyQt6.QtGui import QColor, QFont


_PERSONALIZE_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
_ACCENT_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"

# Windows 11 default blue: Light3, Light2, Light1, Base, Dark1, Dark2, Dark3
_DEFAULT_ACCENT_PALETTE = [
    "#99EBFF", "#4CC2FF", "#0091F8", "#0078D4", "#0067C0", "#003E92", "#001A68",
]


# ---------------------------------------------------------------------------
# Segoe Fluent Icons glyphs
# ---------------------------------------------------------------------------

GLYPH_SETTINGS = "\uE713"
GLYPH_MAP_PIN = "\uE707"
GLYPH_LANGUAGE = "\uF2B7"
GLYPH_MONITOR = "\uE7F4"
GLYPH_MOVE = "\uE7C2"
GLYPH_START = "\uE768"
GLYPH_POWER = "\uE7E8"
GLYPH_INFO = "\uE946"
GLYPH_DOCUMENT = "\uE8A5"
GLYPH_CHEVRON_LEFT = "\uE76B"
GLYPH_CHEVRON_RIGHT = "\uE76C"
GLYPH_WARNING = "\uE7BA"
GLYPH_STAR = "\uE735"


# ---------------------------------------------------------------------------
# Windows settings
# ---------------------------------------------------------------------------

def _read_value(path: str, name: str, default):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return default


def system_uses_dark() -> bool:
    """True if the Windows mode (taskbar, Start, flyouts) is dark."""
    return _read_value(_PERSONALIZE_KEY, "SystemUsesLightTheme", 0) == 0


def apps_use_dark() -> bool:
    """True if the app mode (application windows) is dark."""
    return _read_value(_PERSONALIZE_KEY, "AppsUseLightTheme", 1) == 0


def transparency_enabled() -> bool:
    """True if "Transparency effects" are turned on in Windows."""
    return _read_value(_PERSONALIZE_KEY, "EnableTransparency", 1) == 1


def accent_palette() -> list[str]:
    """Return the 7 accent shades (Light3 … Dark3) of the Windows accent color."""
    data = _read_value(_ACCENT_KEY, "AccentPalette", None)
    try:
        return [f"#{data[i]:02X}{data[i + 1]:02X}{data[i + 2]:02X}" for i in range(0, 28, 4)]
    except (TypeError, IndexError):
        return list(_DEFAULT_ACCENT_PALETTE)


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

def _rgba(hex_rgb: str, alpha: float) -> QColor:
    color = QColor(hex_rgb)
    color.setAlphaF(alpha)
    return color


@dataclass(frozen=True)
class Theme:
    """Fluent color tokens (WinUI 3 theme resources) for one mode."""

    dark: bool
    text: QColor
    text_secondary: QColor
    text_tertiary: QColor
    text_disabled: QColor
    accent: QColor          # AccentFillColorDefault
    accent_text: QColor     # AccentTextFillColorPrimary
    on_accent: QColor       # TextOnAccentFillColorPrimary
    critical: QColor
    success: QColor
    caution: QColor
    window_bg: QColor       # SolidBackgroundFillColorBase (Mica fallback)
    flyout_bg: QColor       # Acrylic fallback color
    acrylic_tint: QColor    # Tint for the acrylic blur
    card: QColor
    card_stroke: QColor
    control: QColor
    control_stroke: QColor
    strong_stroke: QColor
    subtle_hover: QColor
    subtle_pressed: QColor
    divider: QColor

    @property
    def accent_foreground(self) -> QColor:
        """Accent for text and links; the darkest accent shade looks gray in light mode."""
        return self.accent_text if self.dark else self.accent


def get_theme(dark: bool) -> Theme:
    """Build the Fluent theme for dark or light mode with the system accent."""
    light3, light2, _light1, _base, dark1, dark2, _dark3 = accent_palette()
    if dark:
        return Theme(
            dark=True,
            text=QColor("#FFFFFF"),
            text_secondary=_rgba("#FFFFFF", 0.786),
            text_tertiary=_rgba("#FFFFFF", 0.544),
            text_disabled=_rgba("#FFFFFF", 0.363),
            accent=QColor(light2),
            accent_text=QColor(light3),
            on_accent=QColor("#000000"),
            critical=QColor("#FF99A4"),
            success=QColor("#6CCB5F"),
            caution=QColor("#FCE100"),
            window_bg=QColor("#202020"),
            flyout_bg=QColor("#2C2C2C"),
            acrylic_tint=_rgba("#2C2C2C", 0.9),
            card=_rgba("#FFFFFF", 0.0512),
            card_stroke=_rgba("#000000", 0.1),
            control=_rgba("#FFFFFF", 0.0605),
            control_stroke=_rgba("#FFFFFF", 0.0698),
            strong_stroke=_rgba("#FFFFFF", 0.544),
            subtle_hover=_rgba("#FFFFFF", 0.0605),
            subtle_pressed=_rgba("#FFFFFF", 0.0419),
            divider=_rgba("#FFFFFF", 0.0837),
        )
    return Theme(
        dark=False,
        text=_rgba("#000000", 0.894),
        text_secondary=_rgba("#000000", 0.62),
        text_tertiary=_rgba("#000000", 0.446),
        text_disabled=_rgba("#000000", 0.361),
        accent=QColor(dark1),
        accent_text=QColor(dark2),
        on_accent=QColor("#FFFFFF"),
        critical=QColor("#C42B1C"),
        success=QColor("#0F7B0F"),
        caution=QColor("#9D5D00"),
        window_bg=QColor("#F3F3F3"),
        flyout_bg=QColor("#F9F9F9"),
        acrylic_tint=_rgba("#F9F9F9", 0.94),
        card=_rgba("#FFFFFF", 0.7),
        card_stroke=_rgba("#000000", 0.0578),
        control=_rgba("#FFFFFF", 0.7),
        control_stroke=_rgba("#000000", 0.0578),
        strong_stroke=_rgba("#000000", 0.446),
        subtle_hover=_rgba("#000000", 0.0373),
        subtle_pressed=_rgba("#000000", 0.0241),
        divider=_rgba("#000000", 0.0803),
    )


def system_theme() -> Theme:
    """Theme for the taskbar widget and the flyout (Windows mode)."""
    return get_theme(system_uses_dark())


def app_theme() -> Theme:
    """Theme for application windows such as the settings (app mode)."""
    return get_theme(apps_use_dark())


def css(color: QColor) -> str:
    """Format a color for Qt style sheets, keeping its alpha."""
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

def font(px: int, semibold: bool = False, display: bool = False) -> QFont:
    """Segoe UI Variable in the Fluent type ramp.

    The named Semibold instance is used instead of a weight, because Qt
    otherwise synthesizes a heavier bold from the variable font.
    """
    family = "Segoe UI Variable Display" if display else "Segoe UI Variable Text"
    f = QFont()
    if semibold:
        f.setFamilies([f"{family} Semibold", "Segoe UI Semibold"])
    else:
        f.setFamilies([family, "Segoe UI"])
    f.setPixelSize(px)
    return f


def icon_font(px: int) -> QFont:
    """Segoe Fluent Icons (Windows 11) with Segoe MDL2 Assets as fallback."""
    f = QFont()
    f.setFamilies(["Segoe Fluent Icons", "Segoe MDL2 Assets"])
    f.setPixelSize(px)
    return f


# ---------------------------------------------------------------------------
# DWM window effects
# ---------------------------------------------------------------------------

_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_WINDOW_CORNER_PREFERENCE = 33
_DWMWA_CAPTION_COLOR = 35
_DWMWCP_ROUND = 2
_WCA_ACCENT_POLICY = 19
_ACCENT_ENABLE_ACRYLICBLURBEHIND = 4


class _AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_uint),
        ("AccentFlags", ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_uint),
    ]


class _WindowCompositionAttribData(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]


def _set_dwm_int(hwnd: int, attribute: int, value: int) -> bool:
    try:
        v = ctypes.c_int(value)
        return ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), attribute, ctypes.byref(v), ctypes.sizeof(v)
        ) == 0
    except (OSError, AttributeError):
        return False


def round_corners(hwnd: int) -> bool:
    """Let Windows 11 round the window and give it the native border and shadow."""
    return _set_dwm_int(hwnd, _DWMWA_WINDOW_CORNER_PREFERENCE, _DWMWCP_ROUND)


def set_dark_title_bar(hwnd: int, dark: bool) -> bool:
    return _set_dwm_int(hwnd, _DWMWA_USE_IMMERSIVE_DARK_MODE, int(dark))


def set_caption_color(hwnd: int, color: QColor) -> bool:
    """Color the native title bar (Windows 11), e.g. to match the window."""
    colorref = color.red() | (color.green() << 8) | (color.blue() << 16)
    return _set_dwm_int(hwnd, _DWMWA_CAPTION_COLOR, colorref)


def enable_acrylic(hwnd: int, tint: QColor) -> bool:
    """Blur what is behind the window, tinted like Windows 11 flyouts.

    The window must not paint its own background for the blur to show.
    """
    abgr = (
        (tint.alpha() << 24) | (tint.blue() << 16) | (tint.green() << 8) | tint.red()
    )
    policy = _AccentPolicy(_ACCENT_ENABLE_ACRYLICBLURBEHIND, 2, abgr, 0)
    data = _WindowCompositionAttribData(
        _WCA_ACCENT_POLICY,
        ctypes.cast(ctypes.pointer(policy), ctypes.c_void_p),
        ctypes.sizeof(policy),
    )
    try:
        return bool(ctypes.windll.user32.SetWindowCompositionAttribute(
            wintypes.HWND(hwnd), ctypes.byref(data)
        ))
    except (OSError, AttributeError):
        return False
