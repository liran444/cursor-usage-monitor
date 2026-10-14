"""Tray display settings as a popup under the gear button."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QRadioButton, QVBoxLayout, QWidget

from cursor_usage_app.settings.app_settings import default_settings_path

_POPUP_WIDTH = 248

_POPUP_STYLESHEET = """
#traySettingsPopup {
    background-color: #38393c;
    border: 1px solid #52545a;
    border-radius: 10px;
}
#traySettingsPopup QLabel {
    background: transparent;
    border: none;
    color: #f4f4f5;
}
#traySettingsPopup QLabel#sectionTitle {
    font-size: 14px;
    font-weight: 600;
}
#traySettingsPopup QLabel#mutedLabel {
    color: #c4c4c6;
    font-size: 11px;
}
#traySettingsPopup QLabel#settingsPathLabel {
    color: #9a9a9e;
    font-size: 10px;
}
#traySettingsPopup QRadioButton {
    color: #ececee;
    font-size: 12px;
    spacing: 6px;
}
#traySettingsPopup QRadioButton::indicator {
    width: 14px;
    height: 14px;
}
"""


class TraySettingsPopup(QFrame):
    """Frameless popup; closes on outside click (Qt.Popup)."""

    dismissed_via_anchor = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        anchor: QWidget | None = None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._anchor = anchor
        self.setObjectName("traySettingsPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(_POPUP_STYLESHEET)
        self.setFixedWidth(_POPUP_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("Tray display")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        hint = QLabel("Tray icon and hover tooltip. Changes apply immediately.")
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.radio_total = QRadioButton("Total %")
        self.radio_personal = QRadioButton("Personal usage")
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.addButton(self.radio_total)
        self.button_group.addButton(self.radio_personal)
        layout.addWidget(self.radio_total)
        layout.addWidget(self.radio_personal)

        path_label = QLabel(f"Saved to:\n{default_settings_path()}")
        path_label.setObjectName("settingsPathLabel")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)

    def position_below(self, anchor: QWidget) -> None:
        """Align popup top-right under the anchor button."""
        self.adjustSize()
        global_bottom_right = anchor.mapToGlobal(anchor.rect().bottomRight())
        x = global_bottom_right.x() - self.width()
        y = global_bottom_right.y() + 4
        self.move(x, y)

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        anchor = self._anchor
        if anchor is None:
            return
        local = anchor.mapFromGlobal(QCursor.pos())
        if anchor.rect().contains(local):
            self.dismissed_via_anchor.emit()
