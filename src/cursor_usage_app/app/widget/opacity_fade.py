"""Animate QGraphicsOpacityEffect for smooth dimming."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


class OpacityFader:
    """Fade widgets in/out via opacity; removes the effect when fully bright."""

    def __init__(self, duration_ms: int = 300) -> None:
        self._duration_ms = duration_ms
        self._running: dict[int, QPropertyAnimation] = {}

    def fade_to(
        self,
        widget: QWidget,
        target: float,
        *,
        remove_at_full: bool = False,
    ) -> None:
        key = id(widget)
        running = self._running.pop(key, None)
        if running is not None:
            running.stop()

        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            if target >= 1.0 and remove_at_full:
                widget.setGraphicsEffect(None)
                return
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(1.0)
            widget.setGraphicsEffect(effect)

        start = effect.opacity()
        if abs(start - target) < 0.02:
            if remove_at_full and target >= 1.0:
                widget.setGraphicsEffect(None)
            return

        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(self._duration_ms)
        animation.setStartValue(start)
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def _finished() -> None:
            self._running.pop(key, None)
            if remove_at_full and target >= 1.0:
                widget.setGraphicsEffect(None)

        animation.finished.connect(_finished)
        self._running[key] = animation
        animation.start()
