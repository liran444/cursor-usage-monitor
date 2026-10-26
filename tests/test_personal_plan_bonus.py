import os

import pytest

from cursor_usage_app.app.widget.formatting import (
    format_personal_bonus_chip,
    format_personal_bonus_tooltip,
)
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from cursor_usage_app.domain.models import PersonalPlanBonus
from fixture_loader import load_fixture


def test_mapper_parses_plan_breakdown_bonus() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(
        load_fixture("usage_summary_enterprise_team_and_personal_on_demand.json"),
    )

    assert snapshot.personal_plan_bonus is not None
    assert snapshot.personal_plan_bonus.bonus_usd == pytest.approx(21.81)
    assert snapshot.personal_plan_bonus.total_pool_usd == pytest.approx(41.81)


def test_mapper_omits_bonus_when_breakdown_missing() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_personal_only.json"))
    assert snapshot.personal_plan_bonus is None


def test_format_personal_bonus_chip() -> None:
    bonus = PersonalPlanBonus(bonus_usd=21.81, total_pool_usd=41.81)
    assert format_personal_bonus_chip(bonus) == "+$21.81"
    assert format_personal_bonus_tooltip(bonus) == "Used bonus credit · $41.81 total pool"
    assert format_personal_bonus_chip(None) is None
