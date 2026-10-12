import pytest

from cursor_usage_app.domain.mapper import UsageSummaryMapper
from fixture_loader import load_fixture


def test_team_pool_on_demand_uses_team_progress() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_team_pool.json"))

    assert snapshot.billing_cycle_end == "2026-04-01T00:00:00.000Z"
    assert snapshot.personal.used_usd == 18.75
    assert snapshot.personal.limit_usd == 20.0
    assert snapshot.plan_percents.total_percent_used == 64.0
    assert snapshot.plan_percents.api_percent_used == 38.0
    assert snapshot.plan_percents.auto_percent_used == 26.0

    assert snapshot.team_pool is not None
    assert snapshot.team_pool.used_usd == 412.5
    assert snapshot.team_pool.limit_usd == 800.0

    display = snapshot.on_demand_display
    assert display.show_card is True
    assert display.pool_kind == "team"
    assert display.progress_percent == pytest.approx(27.5)
    assert display.personal_on_demand_used_usd == 4.25
    assert display.on_demand_used_usd == 55.0


def test_personal_only_on_demand_card() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))

    assert snapshot.team_pool is None
    display = snapshot.on_demand_display
    assert display.show_card is True
    assert display.pool_kind == "personal"
    assert display.progress_percent == pytest.approx(7.0)
    assert display.on_demand_used_usd == 3.5


def test_personal_pool_from_plan_when_individual_totals_missing() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_plan_pool.json"))

    assert snapshot.personal.used_usd == pytest.approx(3.16)
    assert snapshot.personal.limit_usd == pytest.approx(20.0)
    assert snapshot.plan_percents.total_percent_used == pytest.approx(0.638383838383838)
    assert snapshot.personal_on_demand is not None
    assert snapshot.personal_on_demand.used_usd == 0.0
    assert snapshot.on_demand_display.show_card is False


def test_hides_on_demand_when_absent() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_no_on_demand.json"))

    assert snapshot.on_demand_display.show_card is False
    assert snapshot.personal_on_demand is None
    assert snapshot.team_on_demand is None
