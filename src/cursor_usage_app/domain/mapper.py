"""Map usage-summary JSON to UsageSnapshot."""

from __future__ import annotations

import logging
from typing import Any

from cursor_usage_app.domain.models import (
    OnDemandDisplay,
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
        )

        team_pool: UsagePool | None = None
        if team:
            team_pool = UsagePool(
                used_usd=_to_usd_from_api_cents(team.get("used")),
                limit_usd=_to_usd_from_api_cents(team.get("limit")),
            )
            if not _pool_meaningful(team_pool):
                team_pool = None

        personal_on_demand = _pool_from_on_demand(_as_dict(individual.get("onDemand")))
        team_on_demand = _pool_from_on_demand(_as_dict(team.get("onDemand")))

        on_demand_display = _build_on_demand_display(
            personal_on_demand=personal_on_demand,
            team_on_demand=team_on_demand,
        )

        _log_segment_clamp_if_needed(plan_percents)

        return UsageSnapshot(
            billing_cycle_end=_optional_str(payload.get("billingCycleEnd")),
            personal=personal,
            plan_percents=plan_percents,
            team_pool=team_pool,
            personal_on_demand=personal_on_demand,
            team_on_demand=team_on_demand,
            on_demand_display=on_demand_display,
        )


def _build_on_demand_display(
    personal_on_demand: UsagePool | None,
    team_on_demand: UsagePool | None,
) -> OnDemandDisplay:
    personal_usd = personal_on_demand.used_usd if personal_on_demand else None

    if not _on_demand_card_visible(personal_on_demand, team_on_demand):
        return OnDemandDisplay(
            show_card=False,
            progress_percent=None,
            pool_kind=None,
            personal_on_demand_used_usd=personal_usd,
            on_demand_used_usd=None,
        )

    if team_on_demand is not None and team_on_demand.has_limit:
        used = team_on_demand.used_usd
        limit = team_on_demand.limit_usd
        progress = _percent(used, limit)
        return OnDemandDisplay(
            show_card=True,
            progress_percent=progress,
            pool_kind="team",
            personal_on_demand_used_usd=personal_usd,
            on_demand_used_usd=used,
        )

    if personal_on_demand is not None and personal_on_demand.has_limit:
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

    return OnDemandDisplay(
        show_card=False,
        progress_percent=None,
        pool_kind=None,
        personal_on_demand_used_usd=personal_usd,
        on_demand_used_usd=None,
    )


def _on_demand_card_visible(
    personal_on_demand: UsagePool | None,
    team_on_demand: UsagePool | None,
) -> bool:
    if personal_on_demand is not None and personal_on_demand.has_limit:
        return True
    if team_on_demand is not None and team_on_demand.has_limit:
        return True
    return False


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
