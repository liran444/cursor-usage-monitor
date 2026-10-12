"""Fetch usage-summary and map to domain snapshot."""

from __future__ import annotations

from cursor_usage_app.api.client import UsageSummaryClient, UsageSummaryHttpError
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from cursor_usage_app.domain.models import UsageSnapshot


def fetch_usage_snapshot(session_token: str, client: UsageSummaryClient | None = None) -> UsageSnapshot:
    """Fetch remote usage-summary and return a mapped UsageSnapshot."""
    http = client or UsageSummaryClient()
    try:
        raw = http.fetch_raw(session_token)
    except UsageSummaryHttpError:
        raise

    return UsageSummaryMapper.from_api_payload(raw)
