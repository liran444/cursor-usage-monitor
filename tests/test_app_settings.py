import json

from cursor_usage_app.settings.app_settings import AppSettings, load_app_settings, save_app_settings


def test_load_missing_file_returns_default(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = load_app_settings(path)
    assert settings.tray_display_mode == "total_percent"


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
