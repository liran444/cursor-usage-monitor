"""Usage widget UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = ["UsageWindow"]

if TYPE_CHECKING:
    from cursor_usage_app.app.widget.usage_window import UsageWindow


def __getattr__(name: str):
    if name == "UsageWindow":
        from cursor_usage_app.app.widget.usage_window import UsageWindow

        return UsageWindow
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
