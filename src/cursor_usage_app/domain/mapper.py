"""Map usage-summary JSON to UsageSnapshot."""

from __future__ import annotations

import logging
from typing import Any

from cursor_usage_app.domain.models import (
    OnDemandDisplay,
    PersonalPlanBonus,
    PlanPercents,
    UsagePool,
    UsageSnapshot,
)

_logger = logging.getLogger(__name__)


class UsageSummaryMapper:
    @staticmethod
    def from_api_payload(payload: dict[str, Any]) -> UsageSnapshot:
        individual = _as_dict(payload.get("individualUsage"))
        team = _as_dict(payload.get("teamUsage"))
        plan = _as_dict(individual.get("plan"))

        personal_used = _to_usd_from_api_cents(individual.get("used"))
        personal_limit = _to_usd_from_api_cents(individual.get("limit"))
        if personal_used is None and personal_limit is None:
            personal_used = _to_usd_from_api_cents(plan.get("used"))
            personal_limit = _to_usd_from_api_cents(plan.get("limit"))
        personal = UsagePool(
            used_usd=personal_used,
            limit_usd=personal_limit,
        )
        plan_percents = PlanPercents(
            total_percent_used=_to_float(plan.get("totalPercentUsed")),
            api_percent_used=_to_float(plan.get("apiPercentUsed")),
            auto_percent_used=_to_float(plan.get("autoPercentUsed")),
        ).with_inferred_total_if_missing()

        personal_on_demand = _pool_from_on_demand(_as_dict(individual.get("onDemand")))
        team_on_demand = _pool_from_on_demand(_as_dict(team.get("onDemand")))
        team_pool = _team_pool_from_usage(team, team_on_demand)

        on_demand_display = _build_on_demand_display(personal_on_demand=personal_on_demand)
        personal_plan_bonus = _personal_plan_bonus_from_plan(plan)

        _log_segment_clamp_if_needed(plan_percents)

        return UsageSnapshot(
            billing_cycle_end=_optional_str(payload.get("billingCycleEnd")),
            personal=personal,
            plan_percents=plan_percents,
            team_pool=team_pool,
            personal_on_demand=personal_on_demand,
            team_on_demand=team_on_demand,
            on_demand_display=on_demand_display,
            personal_plan_bonus=personal_plan_bonus,
        )


def _personal_plan_bonus_from_plan(plan: dict[str, Any]) -> PersonalPlanBonus | None:
    breakdown = _as_dict(plan.get("breakdown"))
    bonus_usd = _to_usd_from_api_cents(breakdown.get("bonus"))
    total_pool_usd = _to_usd_from_api_cents(breakdown.get("total"))
    if bonus_usd is None or total_pool_usd is None:
        return None
    if bonus_usd <= 0 or total_pool_usd <= 0:
        return None
    return PersonalPlanBonus(bonus_usd=bonus_usd, total_pool_usd=total_pool_usd)


def _team_pool_from_usage(
    team: dict[str, Any],
    team_on_demand: UsagePool | None,
) -> UsagePool | None:
    if not team:
        return None
    explicit = UsagePool(
        used_usd=_to_usd_from_api_cents(team.get("used")),
        limit_usd=_to_usd_from_api_cents(team.get("limit")),
    )
    if _pool_meaningful(explicit):
        return explicit
    if team_on_demand is not None and _pool_meaningful(team_on_demand):
        return UsagePool(
            used_usd=team_on_demand.used_usd,
            limit_usd=team_on_demand.limit_usd,
        )
    return None


def _build_on_demand_display(personal_on_demand: UsagePool | None) -> OnDemandDisplay:
    personal_usd = personal_on_demand.used_usd if personal_on_demand else None

    if personal_on_demand is None or not personal_on_demand.has_limit:
        return OnDemandDisplay(
            show_card=False,
            progress_percent=None,
            pool_kind=None,
            personal_on_demand_used_usd=personal_usd,
            on_demand_used_usd=None,
        )

    used = personal_on_demand.used_usd
    limit = personal_on_demand.limit_usd
    progress = _percent(used, limit)
    return OnDemandDisplay(
        show_card=True,
        progress_percent=progress,
        pool_kind="personal",
        personal_on_demand_used_usd=personal_usd,
        on_demand_used_usd=used,
    )


def _pool_from_on_demand(on_demand: dict[str, Any]) -> UsagePool | None:
    if not on_demand:
        return None
    used_usd = _to_usd_from_api_cents(on_demand.get("used"))
    limit_usd = _to_usd_from_api_cents(on_demand.get("limit"))
    if (limit_usd is None or limit_usd <= 0) and used_usd is not None:
        remaining_usd = _to_usd_from_api_cents(on_demand.get("remaining"))
        if remaining_usd is not None and remaining_usd >= 0:
            limit_usd = used_usd + remaining_usd
    pool = UsagePool(used_usd=used_usd, limit_usd=limit_usd)
    if pool.has_limit:
        return pool
    if pool.used_usd is not None:
        return pool
    return None


def _pool_meaningful(pool: UsagePool) -> bool:
    return pool.has_limit or (pool.used_usd is not None and pool.used_usd > 0)


def _percent(used: float | None, limit: float | None) -> float | None:
    if used is None or limit is None or limit <= 0:
        return None
    return min(100.0, max(0.0, (used / limit) * 100.0))


def _log_segment_clamp_if_needed(plan: PlanPercents) -> None:
    total = plan.total_percent_used
    api = plan.api_percent_used
    auto = plan.auto_percent_used
    if total is None or api is None or auto is None:
        return
    if (api + auto) > total + 0.01:
        _logger.debug(
            "apiPercentUsed + autoPercentUsed exceeds totalPercentUsed; UI will clamp segments",
            extra={"api": api, "auto": auto, "total": total},
        )


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_usd_from_api_cents(value: Any) -> float | None:
    """usage-summary monetary fields are integer (or fractional) cents."""
    raw = _to_float(value)
    if raw is None:
        return None
    return raw / 100.0


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)
