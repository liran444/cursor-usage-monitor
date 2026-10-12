"""Pure math for segmented TOTAL ring (testable without Qt)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanArcSegments:
    """Arc spans on a 0–100 scale (degrees = fraction * 360 / 100)."""

    total_span: float
    api_span: float
    auto_span: float
    degraded_single_color: bool


def compute_plan_arc_segments(
    total_percent: float | None,
    api_percent: float | None,
    auto_percent: float | None,
) -> PlanArcSegments:
    """
    TOTAL arc length = total_percent (clamped 0–100).

    Within TOTAL: API = api_percent, remainder up to total = AUTO.
    If api + auto > total, scale API/AUTO proportionally inside the total arc.
    If only total is present, render single-color (degraded) mode.
    """
    if total_percent is None:
        return PlanArcSegments(
            total_span=0.0,
            api_span=0.0,
            auto_span=0.0,
            degraded_single_color=True,
        )

    total = _clamp(total_percent)
    if api_percent is None and auto_percent is None:
        return PlanArcSegments(
            total_span=total,
            api_span=total,
            auto_span=0.0,
            degraded_single_color=True,
        )

    api = _clamp(api_percent if api_percent is not None else 0.0)
    auto = _clamp(auto_percent if auto_percent is not None else 0.0)
    segment_sum = api + auto
    if segment_sum <= 0.0:
        return PlanArcSegments(
            total_span=total,
            api_span=0.0,
            auto_span=0.0,
            degraded_single_color=False,
        )

    if segment_sum > total and total > 0.0:
        scale = total / segment_sum
        api = api * scale
        auto = auto * scale
    else:
        api = min(api, total)
        auto = max(0.0, total - api)

    return PlanArcSegments(
        total_span=total,
        api_span=api,
        auto_span=auto,
        degraded_single_color=False,
    )


def _clamp(value: float) -> float:
    return min(100.0, max(0.0, value))
