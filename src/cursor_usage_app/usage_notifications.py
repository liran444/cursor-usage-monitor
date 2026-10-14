"""Usage threshold notifications (Qt-free)."""

from __future__ import annotations

from collections.abc import Iterable

from cursor_usage_app.app.widget.formatting import format_pool_percent
from cursor_usage_app.domain.models import UsageSnapshot
from cursor_usage_app.settings.app_settings import UsageNotificationState

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


def thresholds_already_reached(percent: float | None) -> list[int]:
    """Return configured thresholds at or below current usage (in ascending order)."""
    if percent is None:
        return []
    return [threshold for threshold in sorted(USAGE_NOTIFICATION_THRESHOLDS) if percent >= threshold]


def notification_state_for_cycle(
    state: UsageNotificationState,
    billing_cycle_end: str | None,
) -> UsageNotificationState:
    if state.billing_cycle_end == billing_cycle_end:
        return state
    return UsageNotificationState(billing_cycle_end=billing_cycle_end, fired_keys=frozenset())


def acknowledge_thresholds(
    state: UsageNotificationState,
    section_id: str,
    thresholds: Iterable[int],
) -> UsageNotificationState:
    new_keys = set(state.fired_keys)
    for threshold in thresholds:
        new_keys.add(notification_fired_key(section_id, threshold))
    if new_keys == state.fired_keys:
        return state
    return UsageNotificationState(
        billing_cycle_end=state.billing_cycle_end,
        fired_keys=frozenset(new_keys),
    )


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


def format_notification_message(section_id: str, threshold: int) -> str:
    label = SECTION_DISPLAY_NAMES.get(section_id, section_id)
    return f"{label} usage reached {threshold}%."
