"""Login card grows when status lines appear (offscreen Qt)."""

import os

import pytest

from cursor_usage_app.app.widget.usage_widget import UsageWidget
from fixture_loader import FIXTURES_DIR

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


def test_login_status_increases_preferred_height_when_widget_is_fixed(qapp, monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widget = UsageWidget()
    widget.load_fixture_file(FIXTURES_DIR / "cache_error_not_authenticated.json")
    width = widget.preferred_width()
    base_height = widget.preferred_height()
    widget.setFixedSize(width, base_height)

    widget._login_status.setText(
        "Sign in in the browser, then return to this window. "
        "The session is read automatically."
    )
    widget._login_status.show()

    assert widget.preferred_height() > base_height


def test_start_browser_login_resizes_without_opening_browser(qapp, monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr("cursor_usage_app.app.widget.usage_widget.webbrowser.open", lambda _url: None)

    widget = UsageWidget()
    widget.load_fixture_file(FIXTURES_DIR / "cache_error_not_authenticated.json")
    width = widget.preferred_width()
    base_height = widget.preferred_height()
    widget.setFixedSize(width, base_height)

    widget._start_browser_login()
    widget._resize_to_mode()

    assert widget.height() > base_height
    assert widget._login_status.isHidden() is False
