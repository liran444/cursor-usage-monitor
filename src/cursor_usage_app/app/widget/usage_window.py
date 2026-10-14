"""Frameless floating window hosting UsageWidget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QIcon, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from cursor_usage_app.app.shell_branding import icon_for_shell
from cursor_usage_app.app.tray_ring import TrayRingDisplay, render_tray_ring_icon
from cursor_usage_app.app.widget.colors import active_palette
from cursor_usage_app.app.widget.usage_widget import UsageWidget
from cursor_usage_app.auth.session_store import SessionStore

_WIDGET_WIDTH = 303
_WINDOW_TITLE = "Cursor Usage"


def apply_shell_icon(icon: QIcon, window: QWidget | None = None) -> None:
    """Keep taskbar / Dock icon in sync with the tray ring."""
    shell_icon = icon_for_shell(icon)
    app = QApplication.instance()
    if app is not None:
        app.setWindowIcon(shell_icon)
    if window is not None:
        window.setWindowIcon(shell_icon)


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
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
        )
        self.setWindowTitle(_WINDOW_TITLE)
        apply_shell_icon(
            render_tray_ring_icon(
                TrayRingDisplay(center_kind="empty", ring_percent=None, center_text="—"),
            ),
            window=self,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._card = UsageWidget(self, cache_path=cache_path, store=store)
        self._card.hide_requested.connect(self.hide)
        self._card.minimize_requested.connect(self.showMinimized)
        self._card.compact_changed.connect(lambda _c: self.resize_for_content())

        self._card.ensurePolished()
        self.ensurePolished()
        self.resize_for_content()
        if auto_center:
            self._center_on_screen()

    def widget(self) -> UsageWidget:
        return self._card

    def resize_for_content(self) -> None:
        w = self._card.preferred_width() + 4
        h = self._card.preferred_height() + 4
        self.setFixedSize(w, h)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        palette = active_palette()
        painter.setBrush(QColor(palette.bg_window))
        painter.setPen(QPen(QColor(palette.border_window), 1))
        painter.drawRoundedRect(rect, 18, 18)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        # Fit the card to the frame. Re-measuring text here runs after the first
        # paint and shifts margins by a few pixels.
        inset = 2
        self._card.move(inset, inset)
        self._card.setFixedSize(
            max(1, self.width() - (inset * 2)),
            max(1, self.height() - (inset * 2)),
        )

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
