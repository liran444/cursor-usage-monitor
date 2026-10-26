"""In-window hover hint (matches bonus info popup; avoids QToolTip on frameless windows)."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from cursor_usage_app.app.widget.colors import active_palette


def overlay_host(anchor: QWidget) -> QWidget:
    """Largest ancestor that is still inside the top-level window."""
    host = anchor
    parent = anchor.parentWidget()
    window = anchor.window()
    while (parent is not None) and (parent is not window):
        host = parent
        parent = parent.parentWidget()
    return host


class InstantHint(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("instantInfoHint")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self._label = QLabel()
        self._label.setObjectName("instantInfoHintText")
        layout.addWidget(self._label)
        self.apply_active_palette()
        self.hide()

    def apply_active_palette(self) -> None:
        palette = active_palette()
        self.setStyleSheet(
            f"""
            QFrame#instantInfoHint {{
                background-color: {palette.popup_bg};
                border: 1px solid {palette.popup_border};
                border-radius: 6px;
            }}
            QLabel#instantInfoHintText {{
                color: {palette.popup_title};
                background: transparent;
                border: none;
                font-size: 11px;
            }}
            """
        )

    def set_text(self, text: str) -> None:
        self._label.setText(text)
        self.adjustSize()

    def show_for(self, anchor: QWidget) -> None:
        host = overlay_host(anchor)
        if self.parentWidget() is not host:
            self.setParent(host)
        self.adjustSize()
        below = anchor.mapTo(host, QPoint(0, anchor.height() + 4))
        x = min(max(0, below.x()), max(0, host.width() - self.width()))
        y = below.y()
        if (y + self.height()) > host.height():
            y = anchor.mapTo(host, QPoint(0, 0)).y() - self.height() - 4
        self.move(x, max(0, y))
        self.raise_()
        self.show()
