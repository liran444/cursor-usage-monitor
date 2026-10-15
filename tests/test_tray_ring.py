from cursor_usage_app.app.tray_ring import (
    ring_arc_color_for_percent,
    tray_ring_display_for_session,
    tray_ring_display_from_envelope,
)
from cursor_usage_app.app.widget import colors
from cursor_usage_app.cache.usage_cache import (
    CacheEnvelopeError,
    CacheEnvelopeOk,
    CacheError,
)
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from fixture_loader import load_fixture


def test_ring_color_bands() -> None:
    assert ring_arc_color_for_percent(10.0) == colors.CYAN
    assert ring_arc_color_for_percent(49.9) == colors.CYAN
    assert ring_arc_color_for_percent(50.0) == colors.AMBER
    assert ring_arc_color_for_percent(79.9) == colors.AMBER
    assert ring_arc_color_for_percent(80.0) == colors.CORAL


def test_tray_display_ok_shows_integer_percent() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    envelope = CacheEnvelopeOk(ok=True, data=snapshot, fetched_at="2026-01-01T00:00:00+00:00")
    display = tray_ring_display_from_envelope(envelope)
    assert display.center_kind == "percent"
    assert display.center_text == "42"
    assert display.ring_percent == 42.0


def test_tray_display_personal_mode_uses_pool_percent() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    envelope = CacheEnvelopeOk(ok=True, data=snapshot, fetched_at="2026-01-01T00:00:00+00:00")
    display = tray_ring_display_from_envelope(envelope, mode="personal")
    assert display.center_kind == "percent"
    assert display.center_text == "60"
    assert display.ring_percent == 60.0


def test_tray_display_auth_shows_exclamation() -> None:
    envelope = CacheEnvelopeError(
        ok=False,
        error=CacheError(code="not_authenticated", message="x"),
        fetched_at="2026-01-01T00:00:00+00:00",
    )
    display = tray_ring_display_from_envelope(envelope)
    assert display.center_kind == "auth"
    assert display.center_text == "!"


def test_tray_display_for_session_ignores_stale_ok_without_token() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    envelope = CacheEnvelopeOk(ok=True, data=snapshot, fetched_at="2026-01-01T00:00:00+00:00")
    display = tray_ring_display_for_session(envelope, has_token=False)
    assert display.center_kind == "auth"
    assert display.center_text == "!"


def test_tray_display_network_shows_dash() -> None:
    envelope = CacheEnvelopeError(
        ok=False,
        error=CacheError(code="network", message="x"),
        fetched_at="2026-01-01T00:00:00+00:00",
    )
    display = tray_ring_display_from_envelope(envelope)
    assert display.center_kind == "other"
    assert display.center_text == "—"
