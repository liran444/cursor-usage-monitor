"""Login card grows when status lines appear (offscreen Qt)."""

import os

import pytest

from cursor_usage_app.app.widget.usage_window import UsageWindow
from cursor_usage_app.app.widget.usage_widget import UsageWidget
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.cache.usage_cache import CacheEnvelopeOk, utc_now_iso
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from fixture_loader import FIXTURES_DIR, load_fixture

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


def test_import_unchanged_token_does_not_claim_session_saved(qapp, fake_keyring, tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::existing-cookie")
    widget = UsageWidget(store=store)
    widget.load_fixture_file(FIXTURES_DIR / "cache_error_invalid_token.json")
    widget._login_waiting = True

    widget._on_import_success("user_01::existing-cookie")

    assert widget._login_waiting is True
    assert widget._login_verify_pending is False
    assert "Session saved" not in widget._login_status.text()
    assert "Still waiting" in widget._login_status.text()


def test_import_new_token_verifies_before_login_flow_ends(qapp, fake_keyring, tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::stale")
    widget = UsageWidget(store=store)
    widget.load_fixture_file(FIXTURES_DIR / "cache_error_invalid_token.json")
    widget._login_waiting = True

    widget._on_import_success("user_01::fresh-from-browser")

    assert widget._login_waiting is True
    assert widget._login_verify_pending is True
    assert widget._login_status.text() == "Verifying session…"

    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    envelope = CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso())
    widget.apply_envelope(envelope)
    widget._finish_login_after_fetch()

    assert widget._login_waiting is False
    assert widget._login_status.isHidden() is True


def test_tray_reopen_keeps_login_error_and_token_panel_height(qapp, fake_keyring, tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    store = SessionStore(fallback_path=tmp_path / "session_token")
    window = UsageWindow(auto_center=False, store=store)
    widget = window.widget()
    widget.load_fixture_file(FIXTURES_DIR / "cache_error_invalid_token.json")
    widget._login_error.setText(
        "Automatic import cannot read Chromium cookies on this PC (Windows encryption). "
        "Paste WorkosCursorSessionToken below from DevTools."
    )
    widget._login_error.show()
    widget.show_token_editor()
    window.show()
    window.resize_for_content()
    tall_height = window.height()

    window.hide()
    short_height = widget._measure_browser_login_height()

    window.show()
    window.resize_for_content()
    widget._relayout_browser_login_after_show()

    assert window.height() >= tall_height - 4
    assert widget._login_error.minimumHeight() > 40
    assert short_height >= tall_height - 8
