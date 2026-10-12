"""Domain models for usage display (UI-agnostic)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class PlanPercents:
    total_percent_used: float | None
    api_percent_used: float | None
    auto_percent_used: float | None


@dataclass(frozen=True)
class UsagePool:
    used_usd: float | None
    limit_usd: float | None

    @property
    def has_limit(self) -> bool:
        return self.limit_usd is not None and self.limit_usd > 0


@dataclass(frozen=True)
class OnDemandDisplay:
    """Derived on-demand card fields for widget/tray."""

    show_card: bool
    progress_percent: float | None
    pool_kind: Literal["team", "personal"] | None
    personal_on_demand_used_usd: float | None
    on_demand_used_usd: float | None


@dataclass(frozen=True)
class UsageSnapshot:
    billing_cycle_end: str | None
    personal: UsagePool
    plan_percents: PlanPercents
    team_pool: UsagePool | None
    personal_on_demand: UsagePool | None
    team_on_demand: UsagePool | None
    on_demand_display: OnDemandDisplay

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UsageSnapshot:
        plan = data.get("plan_percents") or {}
        personal = data.get("personal") or {}
        on_demand = data.get("on_demand_display") or {}
        team_pool = data.get("team_pool")
        personal_od = data.get("personal_on_demand")
        team_od = data.get("team_on_demand")

        return cls(
            billing_cycle_end=data.get("billing_cycle_end"),
            personal=UsagePool(
                used_usd=personal.get("used_usd"),
                limit_usd=personal.get("limit_usd"),
            ),
            plan_percents=PlanPercents(
                total_percent_used=plan.get("total_percent_used"),
                api_percent_used=plan.get("api_percent_used"),
                auto_percent_used=plan.get("auto_percent_used"),
            ),
            team_pool=(
                UsagePool(
                    used_usd=team_pool.get("used_usd"),
                    limit_usd=team_pool.get("limit_usd"),
                )
                if team_pool is not None
                else None
            ),
            personal_on_demand=(
                UsagePool(
                    used_usd=personal_od.get("used_usd"),
                    limit_usd=personal_od.get("limit_usd"),
                )
                if personal_od is not None
                else None
            ),
            team_on_demand=(
                UsagePool(
                    used_usd=team_od.get("used_usd"),
                    limit_usd=team_od.get("limit_usd"),
                )
                if team_od is not None
                else None
            ),
            on_demand_display=OnDemandDisplay(
                show_card=bool(on_demand.get("show_card")),
                progress_percent=on_demand.get("progress_percent"),
                pool_kind=on_demand.get("pool_kind"),
                personal_on_demand_used_usd=on_demand.get("personal_on_demand_used_usd"),
                on_demand_used_usd=on_demand.get("on_demand_used_usd"),
            ),
        )
