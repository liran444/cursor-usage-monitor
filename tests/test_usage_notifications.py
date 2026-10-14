from cursor_usage_app.domain.models import (
    OnDemandDisplay,
    PlanPercents,
    UsagePool,
    UsageSnapshot,
)
from cursor_usage_app.settings.app_settings import AppSettings, UsageNotificationState, load_app_settings, save_app_settings
from cursor_usage_app.usage_notifications import (
    acknowledge_thresholds,
    format_notification_message,
    thresholds_already_reached,
    thresholds_to_notify,
    usage_percent_for_section,
)


def _snapshot(**kwargs) -> UsageSnapshot:
    defaults = {
        "billing_cycle_end": "2026-11-01T00:00:00Z",
        "personal": UsagePool(used_usd=25.0, limit_usd=50.0),
        "plan_percents": PlanPercents(
            total_percent_used=55.0,
            api_percent_used=40.0,
            auto_percent_used=10.0,
        ),
        "team_pool": UsagePool(used_usd=10.0, limit_usd=100.0),
        "personal_on_demand": None,
        "team_on_demand": None,
        "on_demand_display": OnDemandDisplay(
            show_card=True,
            progress_percent=80.0,
            pool_kind="personal",
            personal_on_demand_used_usd=8.0,
            on_demand_used_usd=8.0,
        ),
    }
    defaults.update(kwargs)
    return UsageSnapshot(**defaults)


def test_usage_percent_for_sections() -> None:
    snap = _snapshot()
    assert usage_percent_for_section(snap, "personal") == 50.0
    assert usage_percent_for_section(snap, "team") == 10.0
    assert usage_percent_for_section(snap, "plan_total") == 55.0
    assert usage_percent_for_section(snap, "on_demand") == 80.0


def test_thresholds_to_notify_skips_already_fired() -> None:
    fired = frozenset({"personal:50"})
    assert thresholds_to_notify(55.0, "personal", fired) == []
    assert thresholds_to_notify(76.0, "personal", fired) == [75]


def test_format_notification_message_has_no_current_percent_parenthetical() -> None:
    body = format_notification_message("personal", 50)
    assert body == "Personal usage reached 50%."
    assert "(" not in body


def test_thresholds_already_reached_at_eighty_percent() -> None:
    assert thresholds_already_reached(80.0) == [50, 75]


def test_acknowledge_on_enable_leaves_only_higher_thresholds_to_notify() -> None:
    state = UsageNotificationState()
    state = acknowledge_thresholds(state, "personal", thresholds_already_reached(80.0))
    assert thresholds_to_notify(80.0, "personal", state.fired_keys) == []
    assert thresholds_to_notify(91.0, "personal", state.fired_keys) == [90]


def test_notification_settings_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = AppSettings(
        tray_display_mode="personal",
        usage_notifications={"on_demand": True, "team": False},
        usage_notification_state=UsageNotificationState(
            billing_cycle_end="2026-11-01T00:00:00Z",
            fired_keys=frozenset({"personal:50"}),
        ),
    )
    save_app_settings(settings, path)
    loaded = load_app_settings(path)
    assert loaded.tray_display_mode == "personal"
    assert loaded.usage_notifications == {"on_demand": True, "team": False}
    assert loaded.usage_notification_state.billing_cycle_end == "2026-11-01T00:00:00Z"
    assert loaded.usage_notification_state.fired_keys == frozenset({"personal:50"})


def test_invalid_tray_mode_still_loads_notifications(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        '{"tray_display_mode": "unknown", "usage_notifications": {"personal": true}}',
        encoding="utf-8",
    )
    loaded = load_app_settings(path)
    assert loaded.tray_display_mode == "total_percent"
    assert loaded.usage_notifications == {"personal": True}
