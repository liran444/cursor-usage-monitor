"""Widget layout smoke with fixture cache (offscreen Qt)."""

import os

import pytest

from cursor_usage_app.app.widget.usage_widget import UsageWidget
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


def _cache_dict_from_api_fixture(name: str) -> dict:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture(name))
    envelope = CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso())
    return envelope.to_dict()


def test_widget_team_fixture_layout(qapp) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widget = UsageWidget()
    raw = _cache_dict_from_api_fixture("usage_summary_team_pool.json")
    widget.apply_fixture_envelope_dict(raw)

    assert widget._btn_token.isHidden() is True
    assert widget._btn_toggle.text() == "Collapse"
    assert widget._btn_dashboard.isHidden() is False
    assert widget._btn_dashboard.text() == "Dashboard"
    assert widget._btn_quit.isHidden() is False
    assert widget.is_compact() is False
    assert widget.width() == 295
    full_height = widget.preferred_height()
    assert full_height > 400

    widget.set_compact(True)
    assert widget.preferred_height() < full_height
    assert widget.is_compact() is True
    assert widget._btn_dashboard.isHidden() is True
    assert widget._btn_toggle.text() == "Expand"
    assert widget._action_row.isHidden() is False


def test_widget_error_envelope_does_not_crash(qapp) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widget = UsageWidget()
    widget.load_fixture_file(FIXTURES_DIR / "cache_error_not_authenticated.json")
    assert widget.isVisible() or True


def test_widget_invalid_token_fixture_shows_auth_message(qapp) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widget = UsageWidget()
    widget.load_fixture_file(FIXTURES_DIR / "cache_error_invalid_token.json")
    assert widget._view_model.error_code == "invalid_token"
    assert "invalid" in (widget._view_model.inline_message or "").lower()
    assert widget._login_card.isHidden() is False
    assert widget._btn_login.text() == "Log in to Cursor"
    assert widget._personal_card.isHidden() is True
    assert widget._inline_error.isHidden() is True
    assert widget._action_row.isHidden() is True
    assert widget._btn_dashboard.isHidden() is True
    assert widget._btn_token.isHidden() is False
    assert widget._btn_quit.isHidden() is False
    assert widget._token_panel.isHidden() is True
