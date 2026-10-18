"""Frameless window drag helpers (compositor move + client fallback)."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QAbstractSpinBox,
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


def try_start_window_system_move(host: QWidget, event: QMouseEvent) -> bool:
    """Ask the compositor to move the window (required on many Wayland sessions)."""
    if event.button() != Qt.MouseButton.LeftButton:
        return False
    handle = host.windowHandle()
    if handle is None:
        return False
    return handle.startSystemMove()


def manual_drag_offset(host: QWidget, event: QMouseEvent) -> QPoint:
    return event.globalPosition().toPoint() - host.frameGeometry().topLeft()


def apply_manual_drag(host: QWidget, event: QMouseEvent, drag_offset: QPoint) -> None:
    host.move(event.globalPosition().toPoint() - drag_offset)
