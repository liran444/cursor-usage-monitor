"""Info icon that shows its note immediately, inside the same window.

Qt's QToolTip waits before appearing and can stall this frameless window.
The note is a child of the usage card, so hover does not open another window.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from cursor_usage_app.app.widget.colors import active_palette
from cursor_usage_app.app.widget.material_icons import material_pixmap

_ICON_SIZE = 14


def _overlay_host(anchor: QWidget) -> QWidget:
    """Largest ancestor that is still inside the top-level window."""
    host = anchor
    parent = anchor.parentWidget()
    window = anchor.window()
    while (parent is not None) and (parent is not window):
        host = parent
        parent = parent.parentWidget()
    return host


class _InstantHint(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("instantInfoHint")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self._label = QLabel()
        self._label.setObjectName("instantInfoHintText")
        layout.addWidget(self._label)
        self.apply_active_palette()
        self.hide()

    def apply_active_palette(self) -> None:
        palette = active_palette()
        self.setStyleSheet(
            f"""
            QFrame#instantInfoHint {{
                background-color: {palette.popup_bg};
                border: 1px solid {palette.popup_border};
                border-radius: 6px;
            }}
            QLabel#instantInfoHintText {{
                color: {palette.popup_title};
                background: transparent;
                border: none;
                font-size: 11px;
            }}
            """
        )

    def set_text(self, text: str) -> None:
        self._label.setText(text)
        self.adjustSize()

    def show_for(self, anchor: QWidget) -> None:
        host = _overlay_host(anchor)
        if self.parentWidget() is not host:
            self.setParent(host)
        self.adjustSize()
        below = anchor.mapTo(host, QPoint(0, anchor.height() + 4))
        x = min(max(0, below.x()), max(0, host.width() - self.width()))
        y = below.y()
        if (y + self.height()) > host.height():
            y = anchor.mapTo(host, QPoint(0, 0)).y() - self.height() - 4
        self.move(x, max(0, y))
        self.raise_()
        self.show()


class InstantInfoButton(QLabel):
    """Material info glyph. Hover shows a prebuilt note with no tooltip delay."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hint = _InstantHint(self)
        self.setFixedSize(_ICON_SIZE, _ICON_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide()
        self.apply_active_palette()

    def apply_active_palette(self) -> None:
        self.setPixmap(material_pixmap("info", active_palette().bonus_chip_text, size=_ICON_SIZE))
        self._hint.apply_active_palette()

    def set_hint(self, text: str | None) -> None:
        if (text is None) or (text == ""):
            self._hint.hide()
            self.hide()
            return
        self._hint.set_text(text)
        self.show()

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hint.show_for(self)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hint.hide()
        super().leaveEvent(event)

    def hideEvent(self, event) -> None:  # noqa: N802
        self._hint.hide()
        super().hideEvent(event)
