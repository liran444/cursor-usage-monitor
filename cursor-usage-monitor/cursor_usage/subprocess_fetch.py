"""Spawn fetch subprocess (PyInstaller-safe)."""

from __future__ import annotations

import subprocess
import sys


def spawn_fetch() -> None:
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "fetch"]
    else:
        cmd = [sys.executable, "-m", "cursor_usage.__main__", "fetch"]
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
