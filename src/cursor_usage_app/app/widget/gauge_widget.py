"""Donut gauge widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from cursor_usage_app.app.widget import colors
from cursor_usage_app.app.widget.gauge_segments import PlanArcSegments, compute_plan_arc_segments


class DonutGauge(QWidget):
    """Single-color ring gauge with centered percent and optional tag."""

    def __init__(
        self,
        tag: str,
        arc_color: QColor,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tag = tag
        self._arc_color = arc_color
        self._percent: float | None = None
        self.setMinimumSize(72, 72)

    def set_percent(self, value: float | None) -> None:
        self._percent = value
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height())
        margin = 4.0
        rect = QRectF(margin, margin, side - 2 * margin, side - 2 * margin)

        pen_track = QPen(colors.TRACK, 6.0)
        pen_track.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track)
        painter.drawArc(rect, 0, 360 * 16)

        span = 0.0
        if self._percent is not None:
            span = min(100.0, max(0.0, self._percent))

        if span > 0.0:
            pen_arc = QPen(self._arc_color, 6.0)
            pen_arc.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arc)
            start_angle = 90 * 16
            sweep = -int(span * 360 / 100 * 16)
            painter.drawArc(rect, start_angle, sweep)

        painter.setPen(colors.TEXT_PRIMARY)
        font = QFont(self.font())
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        label = "—" if self._percent is None else f"{round(self._percent)}%"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

        tag_font = QFont(self.font())
        tag_font.setPointSize(7)
        painter.setFont(tag_font)
        painter.setPen(colors.TEXT_MUTED)
        tag_rect = QRectF(rect.left(), rect.bottom() - 2, rect.width(), 14)
        painter.drawText(tag_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._tag)


class SegmentedTotalGauge(QWidget):
    """TOTAL ring with API (cyan) + AUTO (violet) segments."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._segments = compute_plan_arc_segments(None, None, None)
        self.setMinimumSize(88, 88)

    def set_plan_percents(
        self,
        total: float | None,
        api: float | None,
        auto: float | None,
    ) -> None:
        self._segments = compute_plan_arc_segments(total, api, auto)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height())
        margin = 4.0
        rect = QRectF(margin, margin, side - 2 * margin, side - 2 * margin)

        pen_track = QPen(colors.TRACK, 7.0)
        pen_track.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track)
        painter.drawArc(rect, 0, 360 * 16)

        segments = self._segments
        if segments.total_span <= 0.0:
            self._draw_center_label(painter, rect, "—")
            return

        start_deg = 90.0
        if segments.degraded_single_color:
            self._draw_arc_span(painter, rect, start_deg, segments.total_span, colors.CYAN)
        else:
            if segments.api_span > 0.0:
                self._draw_arc_span(painter, rect, start_deg, segments.api_span, colors.CYAN)
            if segments.auto_span > 0.0:
                auto_start = start_deg - (segments.api_span * 360.0 / 100.0)
                self._draw_arc_span(painter, rect, auto_start, segments.auto_span, colors.VIOLET)

        display = f"{round(segments.total_span)}%"
        self._draw_center_label(painter, rect, display)

        tag_font = QFont(self.font())
        tag_font.setPointSize(7)
        painter.setFont(tag_font)
        painter.setPen(colors.TEXT_MUTED)
        tag_rect = QRectF(rect.left(), rect.bottom() - 2, rect.width(), 14)
        painter.drawText(tag_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "TOTAL")

    def _draw_arc_span(
        self,
        painter: QPainter,
        rect: QRectF,
        start_deg: float,
        span_percent: float,
        color: QColor,
    ) -> None:
        pen = QPen(color, 7.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        start_angle = int(start_deg * 16)
        sweep = -int(span_percent * 360 / 100 * 16)
        painter.drawArc(rect, start_angle, sweep)

    def _draw_center_label(self, painter: QPainter, rect: QRectF, text: str) -> None:
        painter.setPen(colors.TEXT_PRIMARY)
        font = QFont(self.font())
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


class MiniTotalGauge(SegmentedTotalGauge):
    """Compact-mode mini ring."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(48, 48)
        self.setMaximumSize(56, 56)
