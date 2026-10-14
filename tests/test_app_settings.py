import json

from cursor_usage_app.settings.app_settings import (
    AppSettings,
    UsageNotificationState,
    load_app_settings,
    mutate_app_settings,
    save_app_settings,
)


def test_load_missing_file_returns_default(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = load_app_settings(path)
    assert settings.tray_display_mode == "total_percent"
    assert settings.theme == "dark"


def test_save_and_load_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    save_app_settings(AppSettings(tray_display_mode="personal"), path)
    loaded = load_app_settings(path)
    assert loaded.tray_display_mode == "personal"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["tray_display_mode"] == "personal"


def test_invalid_json_returns_default(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("not json", encoding="utf-8")
    settings = load_app_settings(path)
    assert settings.tray_display_mode == "total_percent"


def test_unknown_mode_returns_default(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"tray_display_mode": "unknown"}', encoding="utf-8")
    settings = load_app_settings(path)
    assert settings.tray_display_mode == "total_percent"


def test_mutate_app_settings_preserves_notification_state(tmp_path) -> None:
    path = tmp_path / "settings.json"
    save_app_settings(
        AppSettings(
            usage_notifications={"personal": True},
            usage_notification_state=UsageNotificationState(
                billing_cycle_end="2026-11-01T00:00:00Z",
                fired_keys=frozenset({"personal:50", "personal:75"}),
            ),
        ),
        path,
    )
    mutate_app_settings(
        lambda current: current.with_usage_notification(section_id="team", enabled=True),
        path,
    )
    loaded = load_app_settings(path)
    assert loaded.usage_notifications == {"personal": True, "team": True}
    assert loaded.usage_notification_state.billing_cycle_end == "2026-11-01T00:00:00Z"
    assert loaded.usage_notification_state.fired_keys == frozenset({"personal:50", "personal:75"})


def test_with_tray_display_mode_preserves_notifications() -> None:
    base = AppSettings(
        tray_display_mode="total_percent",
        usage_notifications={"on_demand": True},
        theme="light",
    )
    updated = base.with_tray_display_mode("personal")
    assert updated.tray_display_mode == "personal"
    assert updated.usage_notifications == {"on_demand": True}
    assert updated.theme == "light"


def test_dark_theme_is_omitted_from_saved_json(tmp_path) -> None:
    path = tmp_path / "settings.json"
    save_app_settings(AppSettings(), path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert "theme" not in raw
    assert load_app_settings(path).theme == "dark"


def test_light_theme_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    save_app_settings(AppSettings(theme="light", tray_display_mode="personal"), path)
    loaded = load_app_settings(path)
    assert loaded.theme == "light"
    assert loaded.tray_display_mode == "personal"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["theme"] == "light"


def test_unknown_theme_returns_dark(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"theme": "sepia"}', encoding="utf-8")
    assert load_app_settings(path).theme == "dark"


def test_with_theme_preserves_other_settings() -> None:
    base = AppSettings(
        tray_display_mode="personal",
        usage_notifications={"team": True},
        usage_notification_state=UsageNotificationState(billing_cycle_end="2026-11-01T00:00:00Z"),
    )
    updated = base.with_theme("light")
    assert updated.theme == "light"
    assert updated.tray_display_mode == "personal"
    assert updated.usage_notifications == {"team": True}
    assert updated.usage_notification_state.billing_cycle_end == "2026-11-01T00:00:00Z"


def test_mutate_preserves_theme(tmp_path) -> None:
    path = tmp_path / "settings.json"
    save_app_settings(AppSettings(theme="light"), path)
    mutate_app_settings(lambda current: current.with_tray_display_mode("personal"), path)
    loaded = load_app_settings(path)
    assert loaded.theme == "light"
    assert loaded.tray_display_mode == "personal"
