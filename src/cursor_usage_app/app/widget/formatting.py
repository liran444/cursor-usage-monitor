"""Display formatting for widget (no Qt)."""

from __future__ import annotations

from datetime import datetime


def format_usd(value: float | None) -> str:
    if value is None:
        return "—"
    return f"${value:,.2f}"


def format_percent(value: float | None, digits: int = 0) -> str:
    if value is None:
        return "—"
    if digits == 0:
        return f"{round(value)}%"
    return f"{value:.{digits}f}%"


def format_pool_percent(used: float | None, limit: float | None) -> float | None:
    if used is None or limit is None or limit <= 0:
        return None
    return min(100.0, max(0.0, (used / limit) * 100.0))


def format_datetime_display(iso_value: str | None) -> str:
    """Format as 'Thu 8 Oct 2026 at 12:52:28' (24h, no timezone name)."""
    if iso_value is None or iso_value.strip() == "":
        return "—"
    text = iso_value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return iso_value
    local = dt.astimezone()
    return local.strftime("%a %d %b %Y at %H:%M:%S")
