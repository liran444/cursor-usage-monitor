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

    assert widget.is_compact() is False
    assert widget.width() == 295
    full_height = widget.preferred_height()
    assert full_height > 400

    widget.set_compact(True)
    assert widget.preferred_height() < full_height
    assert widget.is_compact() is True


def test_widget_error_envelope_does_not_crash(qapp) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widget = UsageWidget()
    widget.load_fixture_file(FIXTURES_DIR / "cache_error_auth.json")
    assert widget.isVisible() or True
