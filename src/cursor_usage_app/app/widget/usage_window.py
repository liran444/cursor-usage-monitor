"""Frameless floating window hosting UsageWidget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from cursor_usage_app.app.widget import colors
from cursor_usage_app.app.widget.usage_widget import UsageWidget
from cursor_usage_app.auth.session_store import SessionStore

_WIDGET_WIDTH = 295


class UsageWindow(QWidget):
    def __init__(
        self,
        cache_path: Path | None = None,
        store: SessionStore | None = None,
        auto_center: bool = True,
    ) -> None:
        super().__init__()
        self._drag_offset = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._card = UsageWidget(self, cache_path=cache_path, store=store)
        self._card.hide_requested.connect(self.hide)
        self._card.compact_changed.connect(lambda _c: self.resize_for_content())

        self.resize_for_content()
        if auto_center:
            self._center_on_screen()

    def widget(self) -> UsageWidget:
        return self._card

    def resize_for_content(self) -> None:
        h = self._card.preferred_height() + 4
        self.setFixedSize(_WIDGET_WIDTH + 4, h)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(colors.BG_WINDOW)
        painter.setPen(QPen(colors.BORDER_WINDOW, 1))
        painter.drawRoundedRect(rect, 18, 18)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._card.move(2, 2)
        self._card.setFixedWidth(_WIDGET_WIDTH)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if (event.buttons() & Qt.MouseButton.LeftButton) and self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def _center_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.move(
            geo.x() + (geo.width() - self.width()) // 2,
            geo.y() + (geo.height() - self.height()) // 2,
        )

    def position_near_cursor(self) -> None:
        """Place window above the cursor (session-only; persisted in Phase 5)."""
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = cursor_pos.x() - self.width() // 2
        y = cursor_pos.y() - self.height() - 16
        x = max(geo.x(), min(x, geo.right() - self.width()))
        y = max(geo.y(), min(y, geo.bottom() - self.height()))
        self.move(x, y)
