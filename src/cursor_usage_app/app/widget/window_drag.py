"""Frameless window drag helpers (compositor move + client fallback)."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QLineEdit,
    QScrollBar,
    QWidget,
)

_INTERACTIVE_TYPES = (
    QAbstractButton,
    QLineEdit,
    QComboBox,
    QAbstractSpinBox,
    QAbstractSlider,
    QScrollBar,
)


def mouse_target_blocks_window_drag(target: QWidget | None) -> bool:
    """True when the click target is a control that must keep normal mouse handling."""
    widget = target
    while widget is not None:
        if isinstance(widget, _INTERACTIVE_TYPES):
            return True
        widget = widget.parentWidget()
    return False


def drag_start_threshold_pixels() -> int:
    """Pixels the cursor must move before a press becomes a window drag."""
    app = QApplication.instance()
    if app is None:
        return 10
    return max(4, app.startDragDistance())


def drag_move_exceeds_threshold(press_global: QPoint, current_global: QPoint) -> bool:
    delta = current_global - press_global
    limit = drag_start_threshold_pixels()
    return (delta.x() * delta.x()) + (delta.y() * delta.y()) >= (limit * limit)


def try_start_window_system_move(host: QWidget, event: QMouseEvent) -> bool:
    """Ask the compositor to move the window (required on many Wayland sessions)."""
    if not (event.buttons() & Qt.MouseButton.LeftButton):
        return False
    handle = host.windowHandle()
    if handle is None:
        return False
    return handle.startSystemMove()


def manual_drag_offset(host: QWidget, event: QMouseEvent) -> QPoint:
    return manual_drag_offset_from_global(host, event.globalPosition().toPoint())


def manual_drag_offset_from_global(host: QWidget, press_global: QPoint) -> QPoint:
    return press_global - host.frameGeometry().topLeft()


def apply_manual_drag(host: QWidget, event: QMouseEvent, drag_offset: QPoint) -> None:
    host.move(event.globalPosition().toPoint() - drag_offset)
