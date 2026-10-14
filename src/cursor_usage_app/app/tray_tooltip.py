"""Tray tooltip text from cache envelope."""

from __future__ import annotations

from cursor_usage_app.app.widget.formatting import (
    format_datetime_display,
    format_percent,
    format_pool_percent,
    format_usd,
)
from cursor_usage_app.cache.usage_cache import CacheEnvelope, CacheEnvelopeError, CacheEnvelopeOk
from cursor_usage_app.settings.app_settings import DEFAULT_TRAY_DISPLAY_MODE, TrayDisplayMode


def build_tray_tooltip(
    envelope: CacheEnvelope | None,
    mode: TrayDisplayMode = DEFAULT_TRAY_DISPLAY_MODE,
) -> str:
    if envelope is None:
        if mode == "personal":
            return "Cursor Usage\nPersonal: —\nLast fetch: —"
        return "Cursor Usage\nTOTAL: —\nAPI: —\nAUTO: —\nLast fetch: —"

    fetched = format_datetime_display(envelope.fetched_at)

    if isinstance(envelope, CacheEnvelopeOk):
        if mode == "personal":
            personal = envelope.data.personal
            personal_pct = format_pool_percent(personal.used_usd, personal.limit_usd)
            personal_line = (
                f"Personal: {format_usd(personal.used_usd)} / {format_usd(personal.limit_usd)} "
                f"({format_percent(personal_pct)})"
            )
            return (
                "Cursor Usage\n"
                f"{personal_line}\n"
                f"Last fetch: {fetched}"
            )

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
        if mode == "personal":
            return (
                "Cursor Usage\n"
                f"Personal: {status}\n"
                f"Last fetch: {fetched}"
            )
        return (
            "Cursor Usage\n"
            f"TOTAL: {status}\n"
            f"API: {status}\n"
            f"AUTO: {status}\n"
            f"Last fetch: {fetched}"
        )

    return f"Cursor Usage\nLast fetch: {fetched}"
