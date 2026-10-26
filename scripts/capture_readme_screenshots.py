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

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _REPO_ROOT / "tests" / "fixtures"
_OUTPUT = _REPO_ROOT / "docs" / "images"


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


def _capture_one(window: UsageWindow, path: Path) -> None:
    window.resize_for_content()
    window.show()
    QApplication.processEvents()
    window.repaint()
    QApplication.processEvents()
    pixmap = window.grab()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not pixmap.save(str(path), "PNG"):
        raise RuntimeError(f"Failed to write {path}")


def main() -> int:
    configure_process_for_shell()
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
        if shot.compact:
            widget.set_compact(True)
        else:
            widget.set_compact(False)
        out = _OUTPUT / shot.filename
        _capture_one(window, out)
        print(out)

    QTimer.singleShot(0, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
