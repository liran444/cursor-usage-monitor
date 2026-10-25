import pytest

from cursor_usage_app.app.widget.view_model import view_model_from_envelope
from cursor_usage_app.cache.usage_cache import CacheEnvelopeOk, utc_now_iso
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from fixture_loader import load_fixture


def test_enterprise_team_on_demand_example_payload() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(
        load_fixture("usage_summary_enterprise_team_on_demand.json"),
    )

    assert snapshot.billing_cycle_end == "2026-10-20T11:08:43.000Z"
    assert snapshot.personal.used_usd == 20.0
    assert snapshot.personal.limit_usd == 20.0
    assert snapshot.personal_plan_bonus is not None
    assert snapshot.personal_plan_bonus.bonus_usd == pytest.approx(5.92)
    assert snapshot.personal_plan_bonus.total_pool_usd == pytest.approx(25.92)
    assert snapshot.plan_percents.total_percent_used == 32.4
    assert snapshot.plan_percents.api_percent_used == 32.4
    assert snapshot.plan_percents.auto_percent_used == 0.0

    assert snapshot.personal_on_demand is not None
    assert snapshot.personal_on_demand.used_usd == 0.0
    assert snapshot.personal_on_demand.has_limit is False

    assert snapshot.team_on_demand is not None
    assert snapshot.team_on_demand.used_usd == pytest.approx(1278.47)
    assert snapshot.team_on_demand.limit_usd == pytest.approx(1278.0)

    assert snapshot.team_pool is not None
    assert snapshot.team_pool.used_usd == pytest.approx(1278.47)
    assert snapshot.team_pool.limit_usd == pytest.approx(1278.0)

    assert snapshot.on_demand_display.show_card is False

    vm = view_model_from_envelope(
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()),
    )
    assert vm.show_team_row is True
    assert vm.show_on_demand_card is False


def test_enterprise_team_on_demand_with_personal_on_demand() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(
        load_fixture("usage_summary_enterprise_team_and_personal_on_demand.json"),
    )

    assert snapshot.billing_cycle_end == "2026-11-20T11:08:43.000Z"
    assert snapshot.personal.used_usd == 20.0
    assert snapshot.personal.limit_usd == 20.0
    assert snapshot.plan_percents.total_percent_used == pytest.approx(52.2625)

    assert snapshot.team_pool is not None
    assert snapshot.team_pool.used_usd == pytest.approx(43.08)
    assert snapshot.team_pool.limit_usd == pytest.approx(1278.0)
    assert snapshot.team_on_demand is not None
    assert snapshot.team_on_demand.used_usd == snapshot.team_pool.used_usd
    assert snapshot.team_on_demand.limit_usd == snapshot.team_pool.limit_usd

    assert snapshot.personal_on_demand is not None
    assert snapshot.personal_on_demand.used_usd == 8.5
    assert snapshot.personal_on_demand.limit_usd == 50.0

    display = snapshot.on_demand_display
    assert display.show_card is True
    assert display.pool_kind == "personal"
    assert display.progress_percent == pytest.approx(17.0)
    assert display.on_demand_used_usd == 8.5

    vm = view_model_from_envelope(
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()),
    )
    assert vm.show_team_row is True
    assert vm.show_on_demand_card is True
