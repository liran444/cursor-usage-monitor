"""QApplication helpers."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication


def ensure_qapplication() -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication(sys.argv)
