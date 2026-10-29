"""Widget settings as a popup under the gear button or beside the tray icon."""

from __future__ import annotations

import time

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QMouseEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from cursor_usage_app.app.widget.colors import popup_stylesheet
from cursor_usage_app.settings.app_settings import default_settings_path

_POPUP_WIDTH = 248
_SHELL_DISMISS_GRACE_S = 0.35
_SHELL_WINDOW_FLAGS = (
    Qt.WindowType.Tool
    | Qt.WindowType.FramelessWindowHint
    | Qt.WindowType.WindowStaysOnTopHint
)


def popup_top_left(
    anchor: QPoint,
    popup_width: int,
    popup_height: int,
    available: QRect,
    margin: int = 8,
) -> QPoint:
    """Place a popup on-screen beside a tray or menu-bar anchor.

    Windows trays sit on the bottom edge, so there is room above. GNOME and
    macOS menus sit on the top edge, so the same "always above" placement
    lands off-screen. Prefer the side that has room, then clamp.
    """
    if (popup_width <= 0) or (popup_height <= 0) or available.isEmpty():
        return QPoint(available.x(), available.y())

    space_above = anchor.y() - available.y()
    space_below = (available.y() + available.height()) - anchor.y()
    if (space_below >= (popup_height + margin)) or (space_below >= space_above):
        y = anchor.y() + margin
    else:
        y = anchor.y() - popup_height - margin
    x = anchor.x() - popup_width
    max_x = available.x() + max(0, available.width() - popup_width)
    max_y = available.y() + max(0, available.height() - popup_height)
    x = min(max(x, available.x()), max_x)
    y = min(max(y, available.y()), max_y)
    return QPoint(x, y)


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
        self._shell_mode = False
        self._changing_role = False
        self._was_active = False
        self._accept_dismiss_at = 0.0
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

        self.radio_theme_system = QRadioButton("System")
        self.radio_theme_dark = QRadioButton("Dark")
        self.radio_theme_light = QRadioButton("Light")
        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_group.addButton(self.radio_theme_system)
        self.theme_group.addButton(self.radio_theme_dark)
        self.theme_group.addButton(self.radio_theme_light)
        layout.addWidget(self.radio_theme_system)
        layout.addWidget(self.radio_theme_dark)
        layout.addWidget(self.radio_theme_light)

        layout.addWidget(_section_rule())

        title = QLabel("Tray display")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        hint = QLabel("Tray icon and hover tooltip")
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
            self.radio_theme_system,
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

    def show_below_anchor(self, anchor: QWidget) -> None:
        """Gear-button popup. The host window is on screen, so Qt.Popup can close on outside click."""
        self._shell_mode = False
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, False)
        app = QGuiApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        host = anchor.window() or anchor
        self._set_window_role(host, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.position_below(anchor)
        self.show()

    def show_near_point(self, point: QPoint) -> None:
        """Tray-menu popup. A top-level tool window stays visible on Linux and macOS.

        Qt.Popup parented to the hidden main window is not mapped on X11/Wayland,
        and placing it above a top menu bar puts it off-screen.
        """
        self._shell_mode = True
        self._was_active = False
        self._accept_dismiss_at = time.monotonic() + _SHELL_DISMISS_GRACE_S
        self._set_window_role(None, _SHELL_WINDOW_FLAGS)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        self.adjustSize()
        self.move(_on_screen_top_left(point, self.width(), self.height()))
        self.show()
        self.raise_()
        self.activateWindow()

    def position_near_global(self, point: QPoint) -> None:
        """Place the popup on the screen that contains ``point``."""
        self.adjustSize()
        self.move(_on_screen_top_left(point, self.width(), self.height()))

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() != QEvent.Type.ActivationChange:
            return
        if (not self._shell_mode) or (not self.isVisible()):
            self._was_active = self.isActiveWindow()
            return
        now_active = self.isActiveWindow()
        if self._was_active and (not now_active) and (time.monotonic() >= self._accept_dismiss_at):
            self.hide()
        self._was_active = now_active

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if self._shell_mode and (event.key() == Qt.Key.Key_Escape):
            self.hide()
            return
        super().keyPressEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if (
            self._shell_mode
            and self.isVisible()
            and (time.monotonic() >= self._accept_dismiss_at)
            and (event.type() == QEvent.Type.MouseButtonPress)
            and isinstance(event, QMouseEvent)
        ):
            if not self.frameGeometry().contains(event.globalPosition().toPoint()):
                self.hide()
        return False

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._shell_mode:
            return
        app = QGuiApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    def hideEvent(self, event) -> None:  # noqa: N802
        app = QGuiApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().hideEvent(event)
        if self._changing_role:
            return
        anchor = self._anchor
        if anchor is None:
            return
        local = anchor.mapFromGlobal(QCursor.pos())
        if anchor.rect().contains(local):
            self.dismissed_via_anchor.emit()

    def _set_window_role(self, parent: QWidget | None, flags: Qt.WindowType) -> None:
        self._changing_role = True
        try:
            self.setParent(parent, flags)
        finally:
            self._changing_role = False


def _on_screen_top_left(point: QPoint, popup_width: int, popup_height: int) -> QPoint:
    screen = QGuiApplication.screenAt(point)
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    if screen is None:
        return QPoint(point.x(), point.y())
    return popup_top_left(point, popup_width, popup_height, screen.availableGeometry())


def _section_rule() -> QWidget:
    line = QWidget()
    line.setObjectName("sectionRule")
    line.setFixedHeight(1)
    return line
