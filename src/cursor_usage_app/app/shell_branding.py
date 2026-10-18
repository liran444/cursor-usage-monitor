"""OS shell integration: taskbar / Dock identity and icon sizes."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon

_APP_USER_MODEL_ID = "LiranDekamhi.CursorUsageMonitor.1"
_SHELL_ICON_SIZES = (16, 20, 24, 32, 48, 64, 128, 256)


def configure_process_for_shell() -> None:
    """Windows: decouple taskbar entry from python.exe and use our window icon."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        return


def app_icon_path() -> Path:
    """Static app mark. The tray keeps its own live usage ring."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "assets" / "app-icon.png"
    return Path(__file__).resolve().parent.parent / "assets" / "app-icon.png"


def load_app_icon() -> QIcon:
    """Window, taskbar, and Dock mark. Not the system-tray usage ring."""
    path = app_icon_path()
    if not path.is_file():
        return QIcon()
    return QIcon(str(path))


def icon_for_shell(base: QIcon) -> QIcon:
    """Build a QIcon with sizes Windows/macOS expect for the taskbar / Dock."""
    if base.isNull():
        return base
    shell = QIcon()
    for size in _SHELL_ICON_SIZES:
        pixmap = base.pixmap(size, size)
        if not pixmap.isNull():
            shell.addPixmap(pixmap)
    if shell.isNull():
        return base
    return shell
