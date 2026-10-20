"""Donut gauges matching the design preview: thick flat-ended arcs, labels inside."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from cursor_usage_app.app.widget.colors import active_palette
from cursor_usage_app.app.widget.gauge_segments import compute_plan_arc_segments

_RING_WIDTH = 11.0
_GAUGE_SIZE = 74


class DonutGauge(QWidget):
    """Single-color ring. Tag sits above the percent, both inside the hole."""

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
        self.setFixedSize(_GAUGE_SIZE, _GAUGE_SIZE)

    def set_percent(self, value: float | None) -> None:
        self._percent = value
        self.update()

    def set_arc_color(self, color: QColor) -> None:
        self._arc_color = color
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = _ring_rect(self.width(), self.height(), _RING_WIDTH)
        _draw_track(painter, rect, _RING_WIDTH)
        span = 0.0 if self._percent is None else min(100.0, max(0.0, self._percent))
        if span > 0.0:
            _draw_arc(painter, rect, 90.0, span, self._arc_color, _RING_WIDTH)
        label = "—" if self._percent is None else f"{round(self._percent)}%"
        _draw_center_stack(painter, self.rect(), self._tag, label)


class SegmentedTotalGauge(QWidget):
    """TOTAL ring. API segment matches the API gauge; the remainder is violet (AUTO)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._total_percent: float | None = None
        self._segments = compute_plan_arc_segments(None, None, None)
        self.setFixedSize(_GAUGE_SIZE, _GAUGE_SIZE)

    def set_plan_percents(
        self,
        total: float | None,
        api: float | None,
        auto: float | None,
    ) -> None:
        self._total_percent = total
        self._segments = compute_plan_arc_segments(total, api, auto)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = _ring_rect(self.width(), self.height(), _RING_WIDTH)
        _draw_track(painter, rect, _RING_WIDTH)
        segments = self._segments
        center_value = _total_gauge_center_label(self._total_percent, segments.total_span)
        if segments.total_span <= 0.0:
            _draw_center_stack(painter, self.rect(), "TOTAL", center_value)
            return

        palette = active_palette()
        start_deg = 90.0
        if segments.degraded_single_color:
            _draw_arc(painter, rect, start_deg, segments.total_span, QColor(palette.cyan), _RING_WIDTH)
        elif segments.auto_span <= 0.0:
            _draw_arc(painter, rect, start_deg, segments.total_span, QColor(palette.api_gauge), _RING_WIDTH)
        elif segments.api_span <= 0.0:
            _draw_arc(painter, rect, start_deg, segments.total_span, QColor(palette.violet), _RING_WIDTH)
        else:
            _draw_arc(painter, rect, start_deg, segments.api_span, QColor(palette.api_gauge), _RING_WIDTH)
            auto_start = start_deg - (segments.api_span * 360.0 / 100.0)
            _draw_arc(painter, rect, auto_start, segments.auto_span, QColor(palette.violet), _RING_WIDTH)

        _draw_center_stack(painter, self.rect(), "TOTAL", center_value)


class MiniTotalGauge(QWidget):
    """Compact-mode mini ring (arc only; the percent is shown beside it)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._segments = compute_plan_arc_segments(None, None, None)
        self.setFixedSize(22, 22)

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
        width = 4.0
        rect = _ring_rect(self.width(), self.height(), width)
        _draw_track(painter, rect, width)
        segments = self._segments
        if segments.total_span <= 0.0:
            return
        palette = active_palette()
        single_auto = (not segments.degraded_single_color) and (segments.api_span <= 0.0)
        color = QColor(palette.violet if single_auto else palette.api_gauge)
        _draw_arc(painter, rect, 90.0, segments.total_span, color, width)


def _total_gauge_center_label(total_percent: float | None, total_span: float) -> str:
    if total_percent is None:
        return "—"
    if total_span <= 0.0:
        return "0%"
    return f"{round(total_span)}%"


def _ring_rect(width: int, height: int, stroke: float) -> QRectF:
    side = float(min(width, height))
    inset = stroke / 2.0 + 1.0
    return QRectF(inset, inset, side - 2 * inset, side - 2 * inset)


def _draw_track(painter: QPainter, rect: QRectF, stroke: float) -> None:
    pen = QPen(QColor(active_palette().track), stroke)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(rect)


def _draw_arc(
    painter: QPainter,
    rect: QRectF,
    start_deg: float,
    span_percent: float,
    color: QColor,
    stroke: float,
) -> None:
    pen = QPen(color, stroke)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    start_angle = int(round(start_deg * 16))
    sweep = -int(round(span_percent * 360.0 / 100.0 * 16))
    if sweep == 0 and span_percent > 0.0:
        sweep = -8
    painter.drawArc(rect, start_angle, sweep)


def _draw_center_stack(painter: QPainter, bounds, tag: str, value: str) -> None:
    rect = QRectF(bounds)
    tag_font = QFont("Segoe UI")
    tag_font.setPixelSize(8)
    tag_font.setWeight(QFont.Weight.DemiBold)
    tag_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.6)
    painter.setFont(tag_font)
    painter.setPen(QColor(active_palette().gauge_tag))
    tag_rect = QRectF(rect.left(), rect.center().y() - 16, rect.width(), 12)
    painter.drawText(tag_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, tag)

    value_font = QFont("Segoe UI")
    value_font.setPixelSize(15)
    value_font.setWeight(QFont.Weight.Bold)
    painter.setFont(value_font)
    painter.setPen(QColor(active_palette().text_primary))
    value_rect = QRectF(rect.left(), rect.center().y() - 2, rect.width(), 18)
    painter.drawText(value_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, value)
