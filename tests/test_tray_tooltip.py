from cursor_usage_app.app.tray_tooltip import build_tray_tooltip
from cursor_usage_app.cache.usage_cache import (
    CacheEnvelopeError,
    CacheEnvelopeOk,
    CacheError,
)
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from fixture_loader import load_fixture


def test_tooltip_ok_includes_plan_percents() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    envelope = CacheEnvelopeOk(ok=True, data=snapshot, fetched_at="2026-01-01T12:00:00+00:00")
    text = build_tray_tooltip(envelope)
    assert "TOTAL: 42%" in text
    assert "API:" in text
    assert "AUTO:" in text
    assert "Last fetch:" in text


def test_tooltip_personal_mode_shows_personal_usage() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    envelope = CacheEnvelopeOk(ok=True, data=snapshot, fetched_at="2026-01-01T12:00:00+00:00")
    text = build_tray_tooltip(envelope, mode="personal")
    assert "Personal: $12.00 / $20.00 (60%)" in text
    assert "TOTAL:" not in text
    assert "Last fetch:" in text


def test_tooltip_auth_error_uses_exclamation() -> None:
    envelope = CacheEnvelopeError(
        ok=False,
        error=CacheError(code="invalid_token", message="bad"),
        fetched_at="2026-01-01T12:00:00+00:00",
    )
    text = build_tray_tooltip(envelope)
    assert "TOTAL: !" in text
