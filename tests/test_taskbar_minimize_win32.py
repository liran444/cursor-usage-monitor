"""Windows taskbar can minimize the frameless window (needs a real window station)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Win32 taskbar style")

_REPO = Path(__file__).resolve().parents[1]


def test_frameless_window_has_minimize_box_and_accepts_sc_minimize() -> None:
    script = r"""
import ctypes
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from cursor_usage_app.app.shell_branding import configure_process_for_shell
from cursor_usage_app.app.widget.usage_window import UsageWindow

configure_process_for_shell()
app = QApplication(sys.argv)
window = UsageWindow(auto_center=False)
window.show()
app.processEvents()
hwnd = int(window.winId())
style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
if not (style & 0x00020000):
    raise SystemExit("WS_MINIMIZEBOX missing")
ctypes.windll.user32.SendMessageW(hwnd, 0x0112, 0xF020, 0)
app.processEvents()
if not (window.windowState() & Qt.WindowState.WindowMinimized):
    raise SystemExit("SC_MINIMIZE did not minimize")
ctypes.windll.user32.SendMessageW(hwnd, 0x0112, 0xF120, 0)
app.processEvents()
if window.windowState() & Qt.WindowState.WindowMinimized:
    raise SystemExit("SC_RESTORE did not restore")
"""
    env = os.environ.copy()
    env.pop("QT_QPA_PLATFORM", None)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=_REPO,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
