from cursor_usage_app.domain.mapper import UsageSummaryMapper
from cursor_usage_app.domain.models import PlanPercents


def test_infer_total_from_api_and_auto_when_total_missing() -> None:
    plan = PlanPercents(
        total_percent_used=None,
        api_percent_used=0.0,
        auto_percent_used=0.0,
    ).with_inferred_total_if_missing()

    assert plan.total_percent_used == 0.0


def test_mapper_infers_zero_total_when_api_omits_total_percent() -> None:
    snapshot = UsageSummaryMapper.from_api_payload(
        {
            "individualUsage": {
                "plan": {
                    "apiPercentUsed": 0.0,
                    "autoPercentUsed": 0.0,
                },
            },
        },
    )

    assert snapshot.plan_percents.total_percent_used == 0.0
    assert snapshot.plan_percents.api_percent_used == 0.0
    assert snapshot.plan_percents.auto_percent_used == 0.0
