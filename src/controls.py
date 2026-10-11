"""
controls.py — Small Windows 11 (Fluent) controls built on Qt widgets.

- IconButton:      subtle, borderless button with a Segoe Fluent Icons glyph
- ToggleSwitch:    the Windows 11 on/off switch
- ComboBox:        a combo box that lets the mouse wheel scroll the page
- SpinningIcon:    a turning glyph, e.g. while checking for updates
- SettingsCard:    a row in the style of the Windows 11 Settings app
- accent_button / hyperlink_button: styled QPushButtons
"""

from PyQt6.QtWidgets import (QAbstractButton, QComboBox, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QSizePolicy, QVBoxLayout, QWidget)
from PyQt6.QtCore import (Qt, QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize,
                          QVariantAnimation, pyqtProperty)
from PyQt6.QtGui import QColor, QFontMetricsF, QPainter

from src.theme import Theme, css, font, icon_font

ICON_SLOT = 30
"""Width for the icon of a SettingsCard: a 20 px glyph needs 30 px to turn without being cut."""


class IconButton(QPushButton):
    """Borderless icon button (Fluent "subtle" button), e.g. for the flyout header."""

    def __init__(self, glyph: str, theme: Theme, tooltip: str = "",
                 size: int = 32, glyph_px: int = 16, parent=None) -> None:
        super().__init__(glyph, parent)
        self.setFont(icon_font(glyph_px))
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if tooltip:
            self.setToolTip(tooltip)
        self.setStyleSheet(
            f"QPushButton {{ color: {css(theme.text_secondary)}; background: transparent;"
            f" border: none; border-radius: 4px; }}"
            f"QPushButton:hover {{ color: {css(theme.text)}; background: {css(theme.subtle_hover)}; }}"
            f"QPushButton:pressed {{ color: {css(theme.text_secondary)};"
            f" background: {css(theme.subtle_pressed)}; }}"
        )


def accent_button(text: str, theme: Theme) -> QPushButton:
    """Filled button in the accent color (Fluent "AccentButton")."""
    btn = QPushButton(text)
    btn.setFont(font(14))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setMinimumHeight(32)
    hover = QColor(theme.accent)
    hover.setAlphaF(0.9)
    pressed = QColor(theme.accent)
    pressed.setAlphaF(0.8)
    btn.setStyleSheet(
        f"QPushButton {{ color: {css(theme.on_accent)}; background: {css(theme.accent)};"
        f" border: none; border-radius: 4px; padding: 0 14px; }}"
        f"QPushButton:hover {{ background: {css(hover)}; }}"
        f"QPushButton:pressed {{ background: {css(pressed)}; }}"
        f"QPushButton:disabled {{ color: {css(theme.text_disabled)};"
        f" background: {css(theme.control)}; }}"
    )
    return btn


def hyperlink_button(text: str, theme: Theme, inline: bool = False) -> QPushButton:
    """Text button in the accent text color (Fluent "HyperlinkButton").

    With *inline* it is a small link without padding, for use in descriptions.
    """
    btn = QPushButton(text)
    btn.setFont(font(12 if inline else 14))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    padding = "2px 0" if inline else "5px 8px"
    hover = ("QPushButton:hover { text-decoration: underline; }" if inline else
             f"QPushButton:hover {{ background: {css(theme.subtle_hover)}; }}"
             f"QPushButton:pressed {{ background: {css(theme.subtle_pressed)}; }}")
    btn.setStyleSheet(
        f"QPushButton {{ color: {css(theme.accent_foreground)}; background: transparent;"
        f" border: none; border-radius: 4px; padding: {padding}; text-align: left; }}"
        + hover
    )
    return btn


class ToggleSwitch(QAbstractButton):
    """Windows 11 toggle switch (40 x 20) with an animated knob."""

    def __init__(self, theme: Theme, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._offset = 0.0
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(40, 20)
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    offset = pyqtProperty(float, _get_offset, _set_offset)

    def setChecked(self, checked: bool) -> None:
        """Set the state without animation (used for the initial value)."""
        super().setChecked(checked)
        self._anim.stop()
        self._set_offset(1.0 if checked else 0.0)

    def _animate(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def sizeHint(self) -> QSize:
        return QSize(40, 20)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        th = self._theme
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        radius = track.height() / 2

        if self.isChecked():
            fill = QColor(th.accent)
            if self.isDown():
                fill.setAlphaF(0.8)
            elif self.underMouse():
                fill.setAlphaF(0.9)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(fill)
            knob_color = th.on_accent
        else:
            p.setPen(th.strong_stroke)
            p.setBrush(th.subtle_hover if self.underMouse() else Qt.BrushStyle.NoBrush)
            knob_color = th.text_secondary
        p.drawRoundedRect(track, radius, radius)

        # Knob grows on hover and stretches while pressed, as in WinUI
        knob_h = 14.0 if (self.underMouse() or self.isDown()) else 12.0
        knob_w = 17.0 if self.isDown() else knob_h
        travel = self.width() - 10 - knob_w
        x = 5 + travel * self._offset
        y = (self.height() - knob_h) / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(knob_color)
        p.drawRoundedRect(QRectF(x, y, knob_w, knob_h), knob_h / 2, knob_h / 2)
        p.end()


class ComboBox(QComboBox):
    """Combo box that ignores the mouse wheel while closed.

    As in the Windows 11 Settings app, scrolling over it scrolls the page
    instead of silently changing the selection.
    """

    def wheelEvent(self, event) -> None:
        event.ignore()


class SpinningIcon(QWidget):
    """A Segoe Fluent Icons glyph that keeps turning, like the Windows Update
    icon while it checks. Fits the icon slot of a SettingsCard."""

    def __init__(self, glyph: str, color: QColor, px: int = 20, parent=None) -> None:
        super().__init__(parent)
        self._glyph = glyph
        self._color = QColor(color)
        self._font = icon_font(px)
        self._angle = 0.0
        self.setFixedWidth(ICON_SLOT)
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(360.0)
        self._anim.setDuration(1000)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._turn)
        self._anim.start()

    def _turn(self, angle: float) -> None:
        self._angle = angle
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self._font)
        p.setPen(self._color)
        # Turn around the middle of the drawn glyph, so it doesn't wobble
        ink = QFontMetricsF(self._font).tightBoundingRect(self._glyph)
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self._angle)
        p.drawText(QPointF(-ink.center().x(), -ink.center().y()), self._glyph)
        p.end()


class SettingsCard(QFrame):
    """A setting row as in the Windows 11 Settings app.

    Layout: [icon] [title / description] ............ [control]
    An optional body widget is shown below the row, separated by a divider.
    """

    def __init__(self, theme: Theme, icon: QWidget | str, title: str,
                 description: str = "", control: QWidget | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self.setObjectName("SettingsCard")
        self.setStyleSheet(
            f"QFrame#SettingsCard {{ background: {css(theme.card)};"
            f" border: 1px solid {css(theme.card_stroke)}; border-radius: 6px; }}"
            f"QFrame#CardDivider {{ background: {css(theme.divider)}; border: none; }}"
        )

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        row = QWidget()
        row.setMinimumHeight(68)
        h = QHBoxLayout(row)
        # The texts start at 12 + 30 (icon slot) + 12 = 54
        h.setContentsMargins(12, 12, 16, 12)
        h.setSpacing(0)

        if isinstance(icon, str):
            icon_label = QLabel(icon)
            icon_label.setFont(icon_font(20))
            icon_label.setFixedWidth(ICON_SLOT)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet(f"color: {css(theme.accent)};")
            h.addWidget(icon_label)
        else:
            h.addWidget(icon)
        h.addSpacing(12)

        # Added to the row first, so the labels get their parent right away:
        # a label without parent flashes up as a window of its own when shown
        texts = QVBoxLayout()
        texts.setSpacing(0)
        h.addLayout(texts, 1)
        self._texts = texts
        self.title_label = QLabel(title)
        self.title_label.setFont(font(14))
        self.title_label.setStyleSheet(f"color: {css(theme.text)};")
        texts.addWidget(self.title_label)
        self.description_label = QLabel(description)
        self.description_label.setFont(font(12))
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet(f"color: {css(theme.text_secondary)};")
        texts.addWidget(self.description_label)
        self.description_label.setVisible(bool(description))

        if control is not None:
            h.addSpacing(16)
            h.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)

        self._layout.addWidget(row)

    def set_description(self, text: str) -> None:
        self.description_label.setText(text)
        self.description_label.setVisible(bool(text))

    def add_text_widget(self, widget: QWidget) -> None:
        """Add a widget below the description, e.g. a hyperlink."""
        self._texts.addWidget(widget, 0, Qt.AlignmentFlag.AlignLeft)

    def add_body(self, body: QWidget) -> None:
        """Append content below the row (e.g. the location search)."""
        divider = QFrame()
        divider.setObjectName("CardDivider")
        divider.setFixedHeight(1)
        self._layout.addWidget(divider)
        body.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._layout.addWidget(body)
