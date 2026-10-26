"""Info icon that shows its note immediately, inside the same window.

Qt's QToolTip waits before appearing and can stall this frameless window.
The note is a child of the usage card, so hover does not open another window.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from cursor_usage_app.app.widget.colors import active_palette
from cursor_usage_app.app.widget.instant_hint import InstantHint
from cursor_usage_app.app.widget.material_icons import material_pixmap

_ICON_SIZE = 14


class InstantInfoButton(QLabel):
    """Material info glyph. Hover shows a prebuilt note with no tooltip delay."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hint = InstantHint(self)
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
