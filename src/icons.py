"""
icons.py — Monochrome line icons for the prayers, in Fluent icon style.

The icons are drawn as vectors so they stay sharp at any display scale
and can be colored with the theme (e.g. accent for the next prayer).
"""

import math

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen

# All icons are designed on a 20 x 20 grid
_GRID = 20.0
_STROKE = 1.5

# Color of each prayer's icon: (dark mode, light mode)
_PRAYER_COLORS = {
    "fajr": ("#C4B5FD", "#7C3AED"),     # dawn: violet
    "sunrise": ("#FDBA74", "#EA580C"),  # sunrise: orange
    "dhuhr": ("#FCD34D", "#D97706"),    # noon: amber
    "asr": ("#FB923C", "#C2410C"),      # afternoon: deep orange
    "maghrib": ("#FDA4AF", "#E11D48"),  # sunset: rose
    "isha": ("#93C5FD", "#2563EB"),     # night: blue
}


def prayer_color(key: str, dark: bool) -> QColor:
    """Icon color of a prayer, readable on dark or light surfaces."""
    dark_hex, light_hex = _PRAYER_COLORS.get(key, ("#FFFFFF", "#000000"))
    return QColor(dark_hex if dark else light_hex)


class PrayerIcon(QWidget):
    """Draws the icon for one prayer key (fajr, sunrise, dhuhr, asr, maghrib, isha)."""

    def __init__(self, key: str, color: QColor, size: int = 20, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self._color = QColor(color)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = self.width() / _GRID
        p.scale(scale, scale)
        pen = QPen(self._color, _STROKE)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        draw = _DRAWERS.get(self._key)
        if draw:
            draw(p)
        p.end()


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------

def _rays(p: QPainter, cx: float, cy: float, r1: float, r2: float, angles) -> None:
    for a in angles:
        rad = math.radians(a)
        dx, dy = math.cos(rad), -math.sin(rad)
        p.drawLine(QPointF(cx + dx * r1, cy + dy * r1), QPointF(cx + dx * r2, cy + dy * r2))


def _horizon_sun(p: QPainter, with_rays: bool) -> None:
    """Half sun on the horizon, as used for dawn, sunrise and sunset."""
    p.drawLine(QPointF(2.5, 15.5), QPointF(17.5, 15.5))
    # Upper half circle (Qt angles: 0° = 3 o'clock, counter-clockwise, 1/16°)
    p.drawArc(QRectF(10 - 4.25, 15.5 - 4.25, 8.5, 8.5), 0, 180 * 16)
    if with_rays:
        _rays(p, 10, 15.5, 6.5, 8.25, (20, 160))


def _arrow(p: QPainter, up: bool) -> None:
    top, bottom = 2.0, 7.5
    p.drawLine(QPointF(10, top), QPointF(10, bottom))
    tip = top if up else bottom
    wing = 2.2 if up else -2.2
    p.drawLine(QPointF(10, tip), QPointF(10 - 2.2, tip + wing))
    p.drawLine(QPointF(10, tip), QPointF(10 + 2.2, tip + wing))


def _sparkle(p: QPainter, cx: float, cy: float, r: float) -> None:
    """Small four-pointed star."""
    path = QPainterPath()
    path.moveTo(cx, cy - r)
    path.quadTo(cx, cy, cx + r, cy)
    path.quadTo(cx, cy, cx, cy + r)
    path.quadTo(cx, cy, cx - r, cy)
    path.quadTo(cx, cy, cx, cy - r)
    p.save()
    p.setBrush(p.pen().color())
    pen = p.pen()
    pen.setWidthF(0.8)
    p.setPen(pen)
    p.drawPath(path)
    p.restore()


def _draw_fajr(p: QPainter) -> None:
    # Dawn: the sun is still below the horizon, the last stars are visible
    _horizon_sun(p, with_rays=False)
    _sparkle(p, 15.0, 4.5, 2.4)
    _sparkle(p, 6.0, 6.5, 1.5)


def _draw_sunrise(p: QPainter) -> None:
    _horizon_sun(p, with_rays=True)
    _arrow(p, up=True)


def _draw_dhuhr(p: QPainter) -> None:
    p.drawEllipse(QPointF(10, 10), 3.75, 3.75)
    _rays(p, 10, 10, 6.25, 8.25, range(0, 360, 45))


def _draw_asr(p: QPainter) -> None:
    # Afternoon: a calmer sun with short rays
    p.drawEllipse(QPointF(10, 10), 3.75, 3.75)
    p.save()
    p.setBrush(p.pen().color())
    p.setPen(Qt.PenStyle.NoPen)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        p.drawEllipse(QPointF(10 + math.cos(rad) * 7, 10 - math.sin(rad) * 7), 0.95, 0.95)
    p.restore()


def _draw_maghrib(p: QPainter) -> None:
    _horizon_sun(p, with_rays=True)
    _arrow(p, up=False)


def _draw_isha(p: QPainter) -> None:
    # Crescent moon: a circle with an offset circle cut out
    outer = QPainterPath()
    outer.addEllipse(QPointF(9.5, 10.5), 6.75, 6.75)
    cut = QPainterPath()
    cut.addEllipse(QPointF(13.25, 7.0), 5.5, 5.5)
    p.drawPath(outer.subtracted(cut))
    _sparkle(p, 15.5, 13.5, 1.8)


_DRAWERS = {
    "fajr": _draw_fajr,
    "sunrise": _draw_sunrise,
    "dhuhr": _draw_dhuhr,
    "asr": _draw_asr,
    "maghrib": _draw_maghrib,
    "isha": _draw_isha,
}
