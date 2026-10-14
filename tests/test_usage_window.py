"""UsageWindow shell integration (window flags, title)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt

from cursor_usage_app.app.tray_ring import TrayRingDisplay, render_tray_ring_icon
from cursor_usage_app.app.widget.usage_window import UsageWindow, apply_shell_icon

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)


@pytest.fixture
def qapp():
    import os as _os

    _os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_usage_window_is_normal_frameless_shell_window(qapp) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    window = UsageWindow(auto_center=False)
    expected = Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
    assert window.windowFlags() == expected
    assert window.windowTitle() == "Cursor Usage"
    assert not window.windowIcon().isNull()


def test_minimize_button_minimizes_shell_window(qapp) -> None:
    window = UsageWindow(auto_center=False)
    window.show()
    window.widget().minimize_requested.emit()
    qapp.processEvents()
    assert window.windowState() & Qt.WindowState.WindowMinimized


def test_apply_shell_icon_updates_app_and_window(qapp) -> None:
    window = UsageWindow(auto_center=False)
    icon = render_tray_ring_icon(
        TrayRingDisplay(center_kind="percent", ring_percent=42.0, center_text="42"),
    )
    apply_shell_icon(icon, window=window)
    assert not window.windowIcon().pixmap(48).isNull()
    assert not qapp.windowIcon().pixmap(48).isNull()
    assert window.windowIcon().pixmap(48).size() == icon.pixmap(48).size()
