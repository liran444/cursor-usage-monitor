from cursor_usage_app.app.widget.view_model import shows_browser_login, view_model_from_envelope, view_model_loading
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


def test_team_on_demand_only_shows_on_demand_not_team_row() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(
        load_fixture("usage_summary_team_on_demand_only.json"),
    )
    vm = view_model_from_envelope(
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()),
    )
    assert vm.show_team_row is False
    assert vm.show_on_demand_card is True


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
    assert "log in" in vm.inline_message.lower()


def test_invalid_token_offers_browser_login() -> None:
    from cursor_usage_app.app.widget.view_model import shows_browser_login

    vm = view_model_from_envelope(
        CacheEnvelopeError(
            ok=False,
            error=CacheError(code="invalid_token", message="expired"),
            fetched_at=utc_now_iso(),
        ),
    )
    assert shows_browser_login(vm, has_stored_token=True) is True


def test_ok_snapshot_does_not_offer_browser_login() -> None:
    from cursor_usage_app.app.widget.view_model import shows_browser_login

    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    vm = view_model_from_envelope(
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()),
    )
    assert shows_browser_login(vm, has_stored_token=False) is False


def test_loading_keeps_snapshot_and_has_no_banner() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    previous = view_model_from_envelope(
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()),
    )
    loading = view_model_loading(previous)
    assert loading.phase == "loading"
    assert loading.snapshot is previous.snapshot
    assert loading.inline_message is None

    empty = view_model_loading(None)
    assert empty.snapshot is None
    assert empty.inline_message is None
    assert shows_browser_login(empty, has_stored_token=True) is False
