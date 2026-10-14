"""Appearance theme: persisted choice, stylesheets, and the settings switcher."""

import os

import pytest

from cursor_usage_app.app.widget import colors
from cursor_usage_app.app.widget.colors import DARK, LIGHT, active_theme, root_stylesheet, set_active_theme
from cursor_usage_app.settings.app_settings import AppSettings, load_app_settings, save_app_settings

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)


def test_dark_stylesheet_keeps_preview_colors() -> None:
    css = root_stylesheet(DARK)
    assert "#2b2b2d" in css
    assert "#16e7ee" in css
    assert "#38393c" in css
    assert colors.CYAN.name() == DARK.cyan
    assert colors.AMBER.name() == "#e6d3b0"
    assert colors.TEXT_PRIMARY.name() == DARK.text_primary


def test_light_stylesheet_uses_light_surfaces() -> None:
    css = root_stylesheet(LIGHT)
    assert "#ffffff" in css
    assert "#1a1c1f" in css
    assert "#0e7490" in css
    assert LIGHT.bg_window == "#f3f4f6"
    assert "#2b2b2d" not in css
    assert "#16e7ee" not in css


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_settings_popup_offers_independent_theme_and_tray_choices(qapp) -> None:
    from cursor_usage_app.app.widget.tray_settings_popup import TraySettingsPopup

    popup = TraySettingsPopup()
    popup.radio_theme_system.setChecked(True)
    popup.radio_total.setChecked(True)
    assert popup.radio_theme_system.isChecked() is True
    assert popup.radio_theme_dark.isChecked() is False
    assert popup.radio_total.isChecked() is True

    popup.radio_theme_dark.setChecked(True)
    assert popup.radio_theme_dark.isChecked() is True
    assert popup.radio_theme_system.isChecked() is False
    assert popup.radio_total.isChecked() is True
    assert popup.radio_personal.isChecked() is False


def test_theme_choice_restyles_card_without_user_settings(qapp, monkeypatch, tmp_path) -> None:
    from cursor_usage_app.app.widget.usage_widget import UsageWidget

    path = tmp_path / "settings.json"
    save_app_settings(AppSettings(theme="dark"), path)
    previous = active_theme()
    widget = UsageWidget()

    def fake_mutate(mutator, settings_path=None):
        updated = mutator(load_app_settings(path))
        save_app_settings(updated, path)
        return updated

    monkeypatch.setattr(
        "cursor_usage_app.app.widget.usage_widget.mutate_app_settings",
        fake_mutate,
    )
    try:
        widget._ensure_settings_popup()
        widget._app_settings = AppSettings(theme="dark")
        widget._theme_group.blockSignals(True)
        widget._radio_theme_dark.setChecked(True)
        widget._theme_group.blockSignals(False)

        widget._radio_theme_light.setChecked(True)

        assert load_app_settings(path).theme == "light"
        assert active_theme() == "light"
        assert "#1a1c1f" in widget.styleSheet()
        assert "#2b2b2d" not in widget.styleSheet()
        assert widget._personal_bar._fill_color.name() == LIGHT.cyan
        assert "#ffffff" in widget._settings_popup.styleSheet()
        assert widget._radio_theme_light.isChecked() is True
        refresh_pm = widget._refresh_frames[0].pixmap(18, 18)
        refresh_color = refresh_pm.toImage().pixelColor(9, 9)
        assert refresh_color.red() < 80
        team_pm = widget._team_icon.pixmap()
        team_color = team_pm.toImage().pixelColor(8, 8)
        assert team_color.green() < 140
    finally:
        set_active_theme(previous)
        widget._apply_active_theme()
