"""OS shell integration: taskbar / Dock identity and icon sizes."""

from __future__ import annotations

import sys

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
