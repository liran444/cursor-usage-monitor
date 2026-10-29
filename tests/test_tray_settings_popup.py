"""Tray settings popup placement for bottom trays and top menu bars."""

import os
import time

import pytest
from PySide6.QtCore import QEvent, QPoint, QRect, Qt
from PySide6.QtGui import QMouseEvent

from cursor_usage_app.app.widget.tray_settings_popup import TraySettingsPopup, popup_top_left

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)

_POPUP = (248, 280)


def test_top_menu_bar_places_popup_below_anchor() -> None:
    available = QRect(0, 40, 1920, 1040)
    origin = popup_top_left(QPoint(1800, 8), *_POPUP, available)

    assert origin.y() >= available.y()
    assert (origin.y() + _POPUP[1]) <= (available.y() + available.height())
    assert origin.x() >= available.x()


def test_bottom_tray_places_popup_above_anchor() -> None:
    available = QRect(0, 0, 1920, 1000)
    origin = popup_top_left(QPoint(1800, 1040), *_POPUP, available)

    assert origin.y() < 1040
    assert (origin.y() + _POPUP[1]) <= (available.y() + available.height())
    assert origin.y() >= available.y()


def test_popup_is_clamped_when_anchor_is_on_the_left_edge() -> None:
    available = QRect(0, 0, 800, 600)
    origin = popup_top_left(QPoint(10, 300), *_POPUP, available)

    assert origin.x() == available.x()
    assert origin.x() + _POPUP[0] <= available.x() + available.width()


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_tray_then_widget_gear_recreates_popup_after_shell_dismiss(qapp) -> None:
    from cursor_usage_app.app.widget.usage_window import UsageWindow

    window = UsageWindow(auto_center=False)
    window.hide()
    qapp.processEvents()

    widget = window.widget()
    widget.open_settings_panel(at_global=QPoint(20, 4))
    qapp.processEvents()

    popup = widget._settings_popup
    assert isinstance(popup, TraySettingsPopup)
    assert popup.parentWidget() is None

    time.sleep(0.4)
    outside = popup.frameGeometry().bottomRight() + QPoint(40, 40)
    press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        outside,
        outside,
        outside,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    popup.eventFilter(qapp, press)
    qapp.processEvents()
    assert not popup.isVisible()

    window.show()
    qapp.processEvents()
    widget._toggle_settings_popup()
    qapp.processEvents()

    gear_popup = widget._settings_popup
    assert gear_popup is not popup
    assert isinstance(gear_popup, TraySettingsPopup)
    assert gear_popup.isVisible()
    assert gear_popup.parentWidget() is window
    assert gear_popup.windowFlags() & Qt.WindowType.Popup


def test_tray_open_uses_toplevel_tool_window_while_main_window_is_hidden(qapp) -> None:
    from cursor_usage_app.app.widget.usage_window import UsageWindow

    window = UsageWindow(auto_center=False)
    window.hide()
    qapp.processEvents()

    window.widget().open_settings_panel(at_global=QPoint(20, 4))
    qapp.processEvents()

    popup = window.widget()._settings_popup
    assert isinstance(popup, TraySettingsPopup)
    assert popup.isVisible()
    assert popup.parentWidget() is None
    flags = popup.windowFlags()
    assert flags & Qt.WindowType.Tool
    assert flags & Qt.WindowType.WindowStaysOnTopHint
    assert popup.testAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
    screen = qapp.primaryScreen()
    assert screen is not None
    assert screen.availableGeometry().contains(popup.geometry().topLeft())
