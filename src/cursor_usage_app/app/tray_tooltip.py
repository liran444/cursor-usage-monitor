"""Tray tooltip text from cache envelope."""

from __future__ import annotations

from cursor_usage_app.app.widget.formatting import format_datetime_display, format_percent
from cursor_usage_app.cache.usage_cache import CacheEnvelope, CacheEnvelopeError, CacheEnvelopeOk


def build_tray_tooltip(envelope: CacheEnvelope | None) -> str:
    if envelope is None:
        return "Cursor Usage\nTOTAL: —\nAPI: —\nAUTO: —\nLast fetch: —"

    fetched = format_datetime_display(envelope.fetched_at)

    if isinstance(envelope, CacheEnvelopeOk):
        plan = envelope.data.plan_percents
        return (
            "Cursor Usage\n"
            f"TOTAL: {format_percent(plan.total_percent_used)}\n"
            f"API: {format_percent(plan.api_percent_used)}\n"
            f"AUTO: {format_percent(plan.auto_percent_used)}\n"
            f"Last fetch: {fetched}"
        )

    if isinstance(envelope, CacheEnvelopeError):
        code = envelope.error.code
        if code in ("not_authenticated", "invalid_token"):
            status = "!"
        else:
            status = "—"
        return (
            "Cursor Usage\n"
            f"TOTAL: {status}\n"
            f"API: {status}\n"
            f"AUTO: {status}\n"
            f"Last fetch: {fetched}"
        )

    return f"Cursor Usage\nLast fetch: {fetched}"
