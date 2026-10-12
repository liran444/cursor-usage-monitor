import json
from pathlib import Path

from cursor_usage_app.cache.usage_cache import (
    CacheEnvelopeError,
    CacheEnvelopeOk,
    CacheError,
    parse_cache_envelope,
    read_cache_envelope,
    write_cache_envelope,
)
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from fixture_loader import load_fixture


def test_cache_envelope_round_trip(tmp_path: Path) -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    path = tmp_path / "usage_cache.json"
    write_cache_envelope(
        path,
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at="2026-01-01T00:00:00+00:00"),
    )

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["ok"] is True
    assert "fetchedAt" in raw
    assert raw["data"]["billing_cycle_end"] == "2026-03-15T12:00:00.000Z"

    loaded = read_cache_envelope(path)
    assert loaded is not None
    assert loaded.ok is True
    assert loaded.data.plan_percents.total_percent_used == 42.0


def test_cache_error_envelope_shape(tmp_path: Path) -> None:
    path = tmp_path / "usage_cache.json"
    write_cache_envelope(
        path,
        CacheEnvelopeError(
            ok=False,
            error=CacheError(code="blocked_or_waf", message="HTML response"),
            fetched_at="2026-01-02T00:00:00+00:00",
        ),
    )
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw == {
        "ok": False,
        "error": {"code": "blocked_or_waf", "message": "HTML response"},
        "fetchedAt": "2026-01-02T00:00:00+00:00",
    }
    parsed = parse_cache_envelope(raw)
    assert parsed is not None
    assert parsed.ok is False
    assert parsed.error.code == "blocked_or_waf"
