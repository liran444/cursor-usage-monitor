"""System appearance preference resolves to dark or light."""

import os

import pytest

from cursor_usage_app.app.widget.appearance_theme import (
    apply_theme_preference,
    resolve_theme_preference,
    system_prefers_dark_theme,
)
from cursor_usage_app.app.widget.colors import active_theme, set_active_theme

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_resolve_fixed_themes() -> None:
    assert resolve_theme_preference("dark") == "dark"
    assert resolve_theme_preference("light") == "light"


def test_resolve_system_follows_os(qapp, monkeypatch) -> None:
    monkeypatch.setattr(
        "cursor_usage_app.app.widget.appearance_theme.system_prefers_dark_theme",
        lambda: True,
    )
    assert resolve_theme_preference("system") == "dark"
    monkeypatch.setattr(
        "cursor_usage_app.app.widget.appearance_theme.system_prefers_dark_theme",
        lambda: False,
    )
    assert resolve_theme_preference("system") == "light"


def test_apply_theme_preference_sets_active_palette(qapp, monkeypatch) -> None:
    previous = active_theme()
    try:
        monkeypatch.setattr(
            "cursor_usage_app.app.widget.appearance_theme.system_prefers_dark_theme",
            lambda: False,
        )
        assert apply_theme_preference("system") == "light"
        assert active_theme() == "light"
    finally:
        set_active_theme(previous)


def test_system_prefers_dark_is_boolean(qapp) -> None:
    assert system_prefers_dark_theme() in (True, False)
