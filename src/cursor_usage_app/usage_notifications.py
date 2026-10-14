"""Usage threshold notifications (Qt-free)."""

from __future__ import annotations

from cursor_usage_app.app.widget.formatting import format_pool_percent
from cursor_usage_app.domain.models import UsageSnapshot

USAGE_NOTIFICATION_THRESHOLDS: tuple[int, ...] = (50, 75, 90, 100)

# Stable keys persisted across sessions; sections may be hidden in the widget UI.
USAGE_NOTIFICATION_SECTION_IDS: tuple[str, ...] = (
    "personal",
    "team",
    "plan_total",
    "on_demand",
)

SECTION_DISPLAY_NAMES: dict[str, str] = {
    "personal": "Personal",
    "team": "Team",
    "plan_total": "Total usage",
    "on_demand": "On demand",
}


def usage_percent_for_section(snapshot: UsageSnapshot, section_id: str) -> float | None:
    if section_id == "personal":
        return format_pool_percent(snapshot.personal.used_usd, snapshot.personal.limit_usd)
    if section_id == "team":
        if snapshot.team_pool is None:
            return None
        return format_pool_percent(snapshot.team_pool.used_usd, snapshot.team_pool.limit_usd)
    if section_id == "plan_total":
        return snapshot.plan_percents.total_percent_used
    if section_id == "on_demand":
        od = snapshot.on_demand_display
        if not od.show_card:
            return None
        return od.progress_percent
    return None


def notification_fired_key(section_id: str, threshold: int) -> str:
    return f"{section_id}:{threshold}"


def thresholds_to_notify(
    percent: float | None,
    section_id: str,
    fired_keys: frozenset[str],
) -> list[int]:
    """Return thresholds newly reached at or above ``percent`` that are not yet in ``fired_keys``."""
    if percent is None:
        return []
    ordered = sorted(USAGE_NOTIFICATION_THRESHOLDS)
    return [
        threshold
        for threshold in ordered
        if (percent >= threshold and notification_fired_key(section_id, threshold) not in fired_keys)
    ]


def format_notification_message(section_id: str, threshold: int, percent: float | None) -> str:
    label = SECTION_DISPLAY_NAMES.get(section_id, section_id)
    pct_text = f"{round(percent)}%" if percent is not None else f"{threshold}%"
    return f"{label} usage reached {threshold}% ({pct_text})."
