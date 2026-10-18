"""Shell branding helpers."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from cursor_usage_app.app.shell_branding import app_icon_path, icon_for_shell, load_app_icon
from cursor_usage_app.app.tray_ring import TrayRingDisplay, render_tray_ring_icon

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_load_app_icon_is_the_static_mark(qapp) -> None:
    assert app_icon_path().is_file()
    icon = load_app_icon()
    assert not icon.isNull()
    assert not icon.pixmap(48).isNull()


def test_icon_for_shell_adds_standard_sizes(qapp) -> None:
    base = render_tray_ring_icon(
        TrayRingDisplay(center_kind="percent", ring_percent=10.0, center_text="10"),
    )
    shell = icon_for_shell(base)
    for size in (16, 32, 48):
        assert not shell.pixmap(size).isNull()
