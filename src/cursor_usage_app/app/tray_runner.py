"""Run tray application entry."""

from __future__ import annotations

import os
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from cursor_usage_app.app.shell_branding import configure_process_for_shell
from cursor_usage_app.app.single_instance import SingleInstanceGuard
from cursor_usage_app.app.tray_controller import TrayController


def run_tray(argv: list[str] | None = None) -> int:
    _ = argv
    configure_process_for_shell()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Cursor Usage")
    app.setFont(QFont("Segoe UI", 9))

    controller_holder: list[TrayController] = []

    def on_peer_message(payload: bytes) -> None:
        if controller_holder:
            controller_holder[0].handle_peer_message(payload)

    guard = SingleInstanceGuard(on_peer_message=on_peer_message)
    if not guard.try_acquire():
        return 0

    controller = TrayController()
    controller_holder.append(controller)
    controller.show_tray()

    smoke_ms = os.environ.get("CURSOR_USAGE_TRAY_SMOKE_MS")
    if smoke_ms is not None:
        from PySide6.QtCore import QTimer

        try:
            delay = int(smoke_ms)
        except ValueError:
            delay = 1500
        QTimer.singleShot(delay, app.quit)

    code = app.exec()
    guard.release()
    return code
