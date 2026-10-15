"""Tray ring icon: color bands and center label (testable helpers + Qt render)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPen, QPixmap

# Dark-palette constants. The tray icon ignores the widget theme so the
# ring stays readable on a dark taskbar.
from cursor_usage_app.app.widget import colors
from cursor_usage_app.app.widget.formatting import format_pool_percent
from cursor_usage_app.cache.usage_cache import CacheEnvelope, CacheEnvelopeError, CacheEnvelopeOk
from cursor_usage_app.settings.app_settings import DEFAULT_TRAY_DISPLAY_MODE, TrayDisplayMode

_ICON_SIZE = 64
_RING_WIDTH = 6.0

TrayCenterKind = Literal["percent", "auth", "other", "empty"]


@dataclass(frozen=True)
class TrayRingDisplay:
    """What to draw in the tray ring."""

    center_kind: TrayCenterKind
    ring_percent: float | None
    center_text: str


def ring_arc_color_for_percent(percent: float) -> QColor:
    """Color bands: cyan → amber → coral as usage rises."""
    value = min(100.0, max(0.0, percent))
    if value < 50.0:
        return colors.CYAN
    if value < 80.0:
        return colors.AMBER
    return colors.CORAL


def tray_ring_display_from_envelope(
    envelope: CacheEnvelope | None,
    mode: TrayDisplayMode = DEFAULT_TRAY_DISPLAY_MODE,
) -> TrayRingDisplay:
    if envelope is None:
        return TrayRingDisplay(center_kind="empty", ring_percent=None, center_text="—")

    if isinstance(envelope, CacheEnvelopeOk):
        if mode == "personal":
            personal = envelope.data.personal
            personal_pct = format_pool_percent(personal.used_usd, personal.limit_usd)
            if personal_pct is None:
                return TrayRingDisplay(center_kind="other", ring_percent=None, center_text="—")
            return TrayRingDisplay(
                center_kind="percent",
                ring_percent=personal_pct,
                center_text=f"{round(personal_pct)}",
            )

        total = envelope.data.plan_percents.total_percent_used
        if total is None:
            return TrayRingDisplay(center_kind="other", ring_percent=None, center_text="—")
        return TrayRingDisplay(
            center_kind="percent",
            ring_percent=total,
            center_text=f"{round(total)}",
        )

    if isinstance(envelope, CacheEnvelopeError):
        code = envelope.error.code
        if code in ("not_authenticated", "invalid_token"):
            return TrayRingDisplay(center_kind="auth", ring_percent=None, center_text="!")
        return TrayRingDisplay(center_kind="other", ring_percent=None, center_text="—")

    return TrayRingDisplay(center_kind="other", ring_percent=None, center_text="—")


def tray_ring_display_for_session(
    envelope: CacheEnvelope | None,
    has_token: bool,
    mode: TrayDisplayMode = DEFAULT_TRAY_DISPLAY_MODE,
) -> TrayRingDisplay:
    """Tray chrome from cache, but never show usage when no session token is stored."""
    if not has_token:
        return TrayRingDisplay(center_kind="auth", ring_percent=None, center_text="!")
    return tray_ring_display_from_envelope(envelope, mode=mode)


def render_tray_ring_icon(display: TrayRingDisplay) -> QIcon:
    image = QImage(_ICON_SIZE, _ICON_SIZE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    margin = 6.0
    rect = QRectF(margin, margin, _ICON_SIZE - 2 * margin, _ICON_SIZE - 2 * margin)

    pen_track = QPen(colors.TRACK, _RING_WIDTH)
    pen_track.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen_track)
    painter.drawArc(rect, 0, 360 * 16)

    if display.center_kind == "percent" and display.ring_percent is not None:
        span = min(100.0, max(0.0, display.ring_percent))
        if span > 0.0:
            arc_color = ring_arc_color_for_percent(span)
            pen_arc = QPen(arc_color, _RING_WIDTH)
            pen_arc.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_arc)
            start_angle = 90 * 16
            sweep = -int(span * 360 / 100 * 16)
            painter.drawArc(rect, start_angle, sweep)

    painter.setPen(colors.TEXT_PRIMARY)
    font = QFont()
    font.setPixelSize(18 if display.center_text == "!" else 16)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, display.center_text)

    painter.end()
    return QIcon(QPixmap.fromImage(image))
