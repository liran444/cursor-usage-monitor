"""Capture README widget screenshots from tests/fixtures (dev tool)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from cursor_usage_app.app.shell_branding import configure_process_for_shell
from cursor_usage_app.app.widget.appearance_theme import apply_theme_preference
from cursor_usage_app.app.widget.usage_window import UsageWindow
from cursor_usage_app.settings import app_settings as app_settings_module
from cursor_usage_app.settings.app_settings import AppSettings, save_app_settings

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _REPO_ROOT / "tests" / "fixtures"
_OUTPUT = _REPO_ROOT / "docs" / "images"
_CAPTURE_SETTINGS = _REPO_ROOT / "build" / "capture_settings.json"


@dataclass(frozen=True)
class Shot:
    filename: str
    fixture: str
    compact: bool = False


_SHOTS = (
    Shot("readme-enterprise-expanded.png", "usage_summary_enterprise_team_and_personal_on_demand.json"),
    Shot("readme-team.png", "usage_summary_team_pool.json"),
    Shot("readme-personal.png", "usage_summary_personal_only.json"),
    Shot("readme-compact.png", "usage_summary_team_pool.json", compact=True),
    Shot("readme-sign-in.png", "cache_error_not_authenticated.json"),
)


def _use_capture_settings() -> None:
    """Ignore the developer's tray default so each shot controls expanded vs compact."""
    _CAPTURE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    save_app_settings(AppSettings(widget_default_display="expanded"), _CAPTURE_SETTINGS)

    def _path() -> Path:
        return _CAPTURE_SETTINGS

    app_settings_module.default_settings_path = _path


def _capture_one(window: UsageWindow, path: Path, *, compact: bool) -> None:
    widget = window.widget()
    widget.set_compact(compact)
    window.resize_for_content()
    window.show()
    # show() may apply saved default display; each shot's layout wins here.
    widget.set_compact(compact)
    window.resize_for_content()
    QApplication.processEvents()
    window.repaint()
    QApplication.processEvents()
    pixmap = window.grab()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not pixmap.save(str(path), "PNG"):
        raise RuntimeError(f"Failed to write {path}")


def main() -> int:
    configure_process_for_shell()
    _use_capture_settings()
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))

    apply_theme_preference("dark")
    window = UsageWindow(auto_center=False)
    widget = window.widget()
    widget._apply_active_theme()

    for shot in _SHOTS:
        fixture_path = _FIXTURES / shot.fixture
        if not fixture_path.is_file():
            raise FileNotFoundError(fixture_path)
        widget.load_fixture_file(fixture_path)
        out = _OUTPUT / shot.filename
        _capture_one(window, out, compact=shot.compact)
        print(out)

    QTimer.singleShot(0, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
