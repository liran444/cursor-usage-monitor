"""Horizontal progress bar widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from cursor_usage_app.app.widget import colors


class HorizontalBar(QWidget):
    def __init__(self, fill_color: QColor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fill_color = fill_color
        self._percent: float | None = None
        self.setFixedHeight(5)

    def set_percent(self, value: float | None) -> None:
        self._percent = value
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = float(self.width())
        h = float(self.height())
        radius = h / 2.0
        track = QRectF(0.0, 0.0, w, h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(colors.BAR_TRACK)
        painter.drawRoundedRect(track, radius, radius)

        if self._percent is not None and self._percent > 0.0:
            pct = min(100.0, max(0.0, self._percent))
            fill_w = w * pct / 100.0
            fill = QRectF(0.0, 0.0, fill_w, h)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._fill_color)
            painter.drawRoundedRect(fill, radius, radius)
