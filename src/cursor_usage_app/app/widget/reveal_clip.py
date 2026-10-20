"""Clip widgets to a revealed size without reflowing their contents."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize
from PySide6.QtWidgets import QSizePolicy, QWidget

_QT_MAX = 16777215


class TopClip(QWidget):
    """Shows only the top `height` pixels of its children.

    Children keep the size they were given. The clip widget's own rect hides
    the rest; a shorter clip does not ask the layout to squeeze or restack them.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._shown = 0
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def shown_height(self) -> int:
        return self._shown

    def set_shown_height(self, height: int) -> None:
        shown = max(0, int(height))
        self._shown = shown
        if shown <= 0:
            self.setFixedHeight(0)
            self.hide()
            if self.mask().isEmpty() is False:
                self.clearMask()
            self._notify_geometry()
            return
        if self.isHidden():
            self.show()
        if self.height() != shown or self.maximumHeight() != shown:
            self.setFixedHeight(shown)
        if self.mask().isEmpty() is False:
            self.clearMask()
        self._notify_geometry()

    def _notify_geometry(self) -> None:
        self.updateGeometry()

    def sizeHint(self) -> QSize:  # noqa: N802
        width = self.width()
        if width <= 0:
            width = super().sizeHint().width()
        return QSize(max(0, width), self._shown)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self.sizeHint()


class TrailingSlot(QWidget):
    """Horizontal slot that closes from the leading edge.

    At rest the child fills the slot the layout assigned, matching a normal
    stretch button. While revealing, the child keeps that full width and stays
    pinned to the trailing edge so its label does not reflow or slide.
    """

    def __init__(self, leading: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._leading = leading
        self._fraction = 1.0
        self._span = 0
        self._child: QWidget | None = None
        self._placing = False
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

    def set_child(self, child: QWidget) -> None:
        child.setParent(self)
        self._child = child
        self._place()

    def fraction(self) -> float:
        return self._fraction

    def note_span(self) -> None:
        """Remember the width the layout gave this slot while it was fully open."""
        if self.width() > self._leading:
            self._span = self.width()

    def set_fraction(self, fraction: float) -> None:
        fraction = min(1.0, max(0.0, fraction))
        if fraction >= 1.0 and self._fraction >= 1.0 and self.isVisible():
            return
        self._fraction = fraction
        if self._fraction >= 1.0:
            self.setMinimumWidth(0)
            self.setMaximumWidth(_QT_MAX)
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            self.updateGeometry()
            self.show()
        else:
            if self._span <= self._leading:
                self.note_span()
            shown = self._shown_width()
            if shown <= 0:
                self.setFixedWidth(0)
                self.hide()
                if self.mask().isEmpty() is False:
                    self.clearMask()
                return
            self.show()
            if self.width() != shown or self.maximumWidth() != shown:
                self.setFixedWidth(shown)
        self._place()
        self.updateGeometry()

    def sizeHint(self) -> QSize:  # noqa: N802
        return self._hint_size(minimum=False)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self._hint_size(minimum=True)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._placing:
            return
        if self._fraction >= 1.0 and self.width() > self._leading:
            self._span = self.width()
        self._place()

    def _hint_size(self, *, minimum: bool) -> QSize:
        child = self._child
        if child is None:
            return QSize(0, 0)
        child_size = child.minimumSizeHint() if minimum else child.sizeHint()
        if self._fraction < 1.0:
            return QSize(self._shown_width(), child_size.height())
        return QSize(self._leading + child_size.width(), child_size.height())

    def _shown_width(self) -> int:
        span = self._span
        if span <= self._leading:
            child = self._child
            natural = child.sizeHint().width() if child is not None else 0
            span = self._leading + natural
        if self._fraction <= 0.0:
            return 0
        if self._fraction >= 1.0:
            return span
        return max(0, int(round(span * self._fraction)))

    def _place(self) -> None:
        child = self._child
        if child is None:
            return
        self._placing = True
        # Use the hint, not the widget's current height. A button that has not
        # been laid out still reports the default 480px geometry.
        height = child.sizeHint().height()
        if height <= 0:
            height = max(0, child.minimumSizeHint().height())
        if self._fraction >= 1.0:
            width = self.width()
            if width <= self._leading:
                width = self._leading + child.sizeHint().width()
            else:
                self._span = width
            button_width = max(0, width - self._leading)
            self._move_child(child, self._leading, button_width, height)
            if self.mask().isEmpty() is False:
                self.clearMask()
            self._set_fixed_height(height)
            self._placing = False
            return
        span = self._span if self._span > self._leading else self._leading + child.sizeHint().width()
        button_width = max(0, span - self._leading)
        shown = self._shown_width()
        self._move_child(child, shown - button_width, button_width, height)
        self._set_fixed_height(height)
        if self.mask().isEmpty() is False:
            self.clearMask()
        self._placing = False

    def _move_child(self, child: QWidget, x: int, width: int, height: int) -> None:
        geometry = QRect(x, 0, width, height)
        if child.geometry() != geometry:
            child.setGeometry(geometry)

    def _set_fixed_height(self, height: int) -> None:
        if self.height() != height or self.maximumHeight() != height:
            self.setFixedHeight(height)
