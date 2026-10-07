"""Locale-aware display formatting for ISO-8601 timestamps."""

from __future__ import annotations

import locale
from datetime import datetime, timezone

_lc_time_configured = False


def _ensure_lc_time() -> None:
    global _lc_time_configured
    if _lc_time_configured:
        return
    for candidate in ("", "C.UTF-8", "en_US.UTF-8"):
        try:
            locale.setlocale(locale.LC_TIME, candidate)
            break
        except locale.Error:
            continue
    _lc_time_configured = True


def parse_iso_datetime(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _strftime_locale(dt: datetime) -> str:
    _ensure_lc_time()
    if hasattr(locale, "nl_langinfo"):
        try:
            return dt.strftime(locale.nl_langinfo(locale.D_T_FMT))
        except (ValueError, AttributeError):
            pass
    return dt.strftime("%c")


def format_datetime_local(value: str | None) -> str | None:
    """Format a UTC ISO-8601 timestamp for display in the system locale and local timezone."""
    if not value:
        return None
    try:
        dt = parse_iso_datetime(value).astimezone()
    except (TypeError, ValueError):
        return value
    return _strftime_locale(dt)
