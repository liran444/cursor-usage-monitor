from cursor_usage_app.app.widget.view_model import view_model_from_envelope
from cursor_usage_app.cache.usage_cache import CacheEnvelopeError, CacheError, CacheEnvelopeOk, utc_now_iso
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from fixture_loader import load_fixture


def test_ok_envelope_shows_team_and_on_demand() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_team_pool.json"))
    vm = view_model_from_envelope(
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()),
    )
    assert vm.phase == "ok"
    assert vm.show_team_row is True
    assert vm.show_on_demand_card is True
    assert vm.inline_message is None


def test_personal_only_hides_team_row() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    vm = view_model_from_envelope(
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()),
    )
    assert vm.show_team_row is False
    assert vm.show_on_demand_card is True


def test_auth_error_inline_message() -> None:
    vm = view_model_from_envelope(
        CacheEnvelopeError(
            ok=False,
            error=CacheError(code="not_authenticated", message="No session token available"),
            fetched_at=utc_now_iso(),
        ),
    )
    assert vm.phase == "error"
    assert vm.inline_message is not None
    assert "token" in vm.inline_message.lower()
