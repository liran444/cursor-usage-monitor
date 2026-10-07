"""Map usage-summary JSON to normalized status cache."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _cents_to_usd(cents: int | float | None) -> float | None:
    if cents is None:
        return None
    return round(float(cents) / 100.0, 2)


def _percent(used: int | None, limit: int | None) -> int | None:
    if used is None or limit is None or limit <= 0:
        return None
    return round(float(used) / float(limit) * 100.0)


def _api_percent(value: int | float | None) -> int | None:
    if value is None:
        return None
    return round(float(value))


def _pool_from_on_demand(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data or not isinstance(data, dict):
        return None
    used = data.get("used")
    limit = data.get("limit")
    remaining = data.get("remaining")
    if used is None and limit is None:
        return None
    used_c = int(used) if used is not None else None
    limit_c = int(limit) if limit is not None else None
    rem_c = int(remaining) if remaining is not None else None
    return {
        "usedUsd": _cents_to_usd(used_c),
        "limitUsd": _cents_to_usd(limit_c),
        "remainingUsd": _cents_to_usd(rem_c),
        "percentUsed": _percent(used_c, limit_c),
        "percentRemaining": _percent(rem_c, limit_c) if rem_c is not None else None,
    }


def map_usage_summary(payload: dict[str, Any]) -> dict[str, Any]:
    plan = (payload.get("individualUsage") or {}).get("plan") or {}
    used_c = plan.get("used")
    limit_c = plan.get("limit")
    remaining_c = plan.get("remaining")

    used_int = int(used_c) if used_c is not None else None
    limit_int = int(limit_c) if limit_c is not None else None
    rem_int = int(remaining_c) if remaining_c is not None else None

    personal = {
        "usedUsd": _cents_to_usd(used_int),
        "limitUsd": _cents_to_usd(limit_int),
        "remainingUsd": _cents_to_usd(rem_int),
        "percentUsed": _percent(used_int, limit_int),
        "percentRemaining": _percent(rem_int, limit_int) if rem_int is not None else None,
    }

    team_usage = payload.get("teamUsage")
    team_pool = None
    if isinstance(team_usage, dict):
        team_pool = _pool_from_on_demand(team_usage.get("onDemand"))

    dashboard = {
        "autoPercentUsed": _api_percent(plan.get("autoPercentUsed")),
        "apiPercentUsed": _api_percent(plan.get("apiPercentUsed")),
        "totalPercentUsed": _api_percent(plan.get("totalPercentUsed")),
    }

    on_demand = (payload.get("individualUsage") or {}).get("onDemand") or {}
    personal_on_demand_usd = _cents_to_usd(
        int(on_demand["used"]) if on_demand.get("used") is not None else None
    )

    return {
        "ok": True,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "billingCycleEnd": payload.get("billingCycleEnd"),
        "personalIncluded": personal,
        "personalOnDemandUsd": personal_on_demand_usd,
        "teamPool": team_pool,
        "dashboardPercents": dashboard,
        "membershipType": payload.get("membershipType"),
        "limitType": payload.get("limitType"),
        "error": None,
    }


def error_status(error_code: str, message: str | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "billingCycleEnd": None,
        "personalIncluded": {
            "usedUsd": None,
            "limitUsd": None,
            "remainingUsd": None,
            "percentUsed": None,
            "percentRemaining": None,
        },
        "personalOnDemandUsd": None,
        "teamPool": None,
        "dashboardPercents": {
            "autoPercentUsed": None,
            "apiPercentUsed": None,
            "totalPercentUsed": None,
        },
        "membershipType": None,
        "limitType": None,
        "error": error_code if message is None else f"{error_code}: {message}",
    }
