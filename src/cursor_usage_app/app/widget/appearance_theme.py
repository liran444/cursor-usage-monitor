"""Resolve appearance preference (dark / light / system) to an active palette."""

from __future__ import annotations

from cursor_usage_app.app.widget.colors import ThemeName, active_theme, set_active_theme
from cursor_usage_app.settings.app_settings import ThemeId


def system_prefers_dark_theme() -> bool:
    """True when the OS reports dark mode (or when unknown, from the app palette)."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance()
    if app is None:
        return True

    hints = app.styleHints()
    scheme = hints.colorScheme()
    if scheme == Qt.ColorScheme.Dark:
        return True
    if scheme == Qt.ColorScheme.Light:
        return False

    window = app.palette().color(app.palette().ColorRole.Window)
    return window.lightness() < 128


def resolve_theme_preference(preference: ThemeId) -> ThemeName:
    if preference == "light":
        return "light"
    if preference == "dark":
        return "dark"
    if system_prefers_dark_theme():
        return "dark"
    return "light"


def apply_theme_preference(preference: ThemeId) -> ThemeName:
    resolved = resolve_theme_preference(preference)
    set_active_theme(resolved)
    return resolved


def applied_theme_matches_preference(preference: ThemeId) -> bool:
    return active_theme() == resolve_theme_preference(preference)
