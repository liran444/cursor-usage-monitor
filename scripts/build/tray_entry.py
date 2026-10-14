"""PyInstaller entry: windowed tray app (no console on Windows)."""

from __future__ import annotations

import sys

from cursor_usage_app.app.tray_runner import run_tray

if __name__ == "__main__":
    sys.exit(run_tray())
