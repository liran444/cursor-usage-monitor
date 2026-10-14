"""Run standalone usage widget."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from cursor_usage_app.app.shell_branding import configure_process_for_shell
from cursor_usage_app.app.tray_ring import render_tray_ring_icon, tray_ring_display_from_envelope
from cursor_usage_app.app.widget.fetch_worker import load_cache
from cursor_usage_app.app.widget.usage_window import UsageWindow, apply_shell_icon
from cursor_usage_app.cache.usage_cache import default_cache_path
from cursor_usage_app.settings.app_settings import load_app_settings


def run_widget(argv: list[str] | None = None) -> int:
    args = list(argv or [])
    fixture_path: Path | None = None
    if "--fixture" in args:
        idx = args.index("--fixture")
        if idx + 1 < len(args):
            fixture_path = Path(args[idx + 1])

    configure_process_for_shell()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationName("Cursor Usage")
    app.setFont(QFont("Segoe UI", 9))

    window = UsageWindow()
    widget = window.widget()
    widget.reload_from_cache()
    settings = load_app_settings()
    envelope = load_cache(default_cache_path())
    display = tray_ring_display_from_envelope(envelope, mode=settings.tray_display_mode)
    apply_shell_icon(render_tray_ring_icon(display), window=window)

    env_fixture = os.environ.get("CURSOR_USAGE_WIDGET_FIXTURE")
    if env_fixture:
        widget.load_fixture_file(Path(env_fixture))
    elif fixture_path is not None:
        widget.load_fixture_file(fixture_path)

    window.show()
    return app.exec()
