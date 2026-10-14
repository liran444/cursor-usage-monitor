"""Widget settings as a popup under the gear button."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QRadioButton, QVBoxLayout, QWidget

from cursor_usage_app.app.widget.colors import popup_stylesheet
from cursor_usage_app.settings.app_settings import default_settings_path

_POPUP_WIDTH = 248


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
        self.apply_active_palette()
        self.setFixedWidth(_POPUP_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        appearance = QLabel("Appearance")
        appearance.setObjectName("sectionTitle")
        layout.addWidget(appearance)

        appearance_hint = QLabel("Light or dark colors for this window.")
        appearance_hint.setObjectName("mutedLabel")
        appearance_hint.setWordWrap(True)
        layout.addWidget(appearance_hint)

        self.radio_theme_dark = QRadioButton("Dark")
        self.radio_theme_light = QRadioButton("Light")
        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_group.addButton(self.radio_theme_dark)
        self.theme_group.addButton(self.radio_theme_light)
        theme_row = QHBoxLayout()
        theme_row.setContentsMargins(0, 0, 0, 0)
        theme_row.setSpacing(12)
        theme_row.addWidget(self.radio_theme_dark)
        theme_row.addWidget(self.radio_theme_light)
        theme_row.addStretch()
        layout.addLayout(theme_row)

        layout.addSpacing(8)

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

        for button in (
            self.radio_theme_dark,
            self.radio_theme_light,
            self.radio_total,
            self.radio_personal,
        ):
            button.setAutoExclusive(False)

        path_label = QLabel(f"Saved to:\n{default_settings_path()}")
        path_label.setObjectName("settingsPathLabel")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)

    def apply_active_palette(self) -> None:
        self.setStyleSheet(popup_stylesheet())

    def position_below(self, anchor: QWidget) -> None:
        """Align popup top-right under the anchor button."""
        self.adjustSize()
        global_bottom_right = anchor.mapToGlobal(anchor.rect().bottomRight())
        x = global_bottom_right.x() - self.width()
        y = global_bottom_right.y() + 4
        self.move(x, y)

    def position_near_global(self, point: QPoint) -> None:
        """Place popup above the point, right-aligned (e.g. tray context menu)."""
        self.adjustSize()
        x = point.x() - self.width()
        y = point.y() - self.height() - 8
        self.move(x, y)

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        anchor = self._anchor
        if anchor is None:
            return
        local = anchor.mapFromGlobal(QCursor.pos())
        if anchor.rect().contains(local):
            self.dismissed_via_anchor.emit()
