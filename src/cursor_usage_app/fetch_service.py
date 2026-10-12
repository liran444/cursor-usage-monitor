"""Orchestrate fetch + cache write (Phase 1: token from env only)."""

from __future__ import annotations

import os
from pathlib import Path

from cursor_usage_app.api.client import UsageSummaryClient, UsageSummaryHttpError
from cursor_usage_app.api.usage_summary import fetch_usage_snapshot
from cursor_usage_app.cache.usage_cache import (
    CacheEnvelopeError,
    CacheEnvelopeOk,
    CacheError,
    default_cache_path,
    utc_now_iso,
    write_cache_envelope,
)

_PHASE1_TOKEN_ENV = "CURSOR_USAGE_TOKEN_TEST"


def resolve_phase1_session_token() -> str | None:
    """Session source until Phase 2 session_store is wired."""
    token = os.environ.get(_PHASE1_TOKEN_ENV)
    if token is None:
        return None
    stripped = token.strip()
    if stripped == "":
        return None
    return stripped


def run_fetch(cache_path: Path | None = None, client: UsageSummaryClient | None = None) -> int:
    """
    Fetch usage-summary and write cache envelope.

    Returns process exit code (0 success, 1 failure).
    """
    path = cache_path or default_cache_path()
    token = resolve_phase1_session_token()
    fetched_at = utc_now_iso()

    if token is None:
        write_cache_envelope(
            path,
            CacheEnvelopeError(
                ok=False,
                error=CacheError(
                    code="not_authenticated",
                    message="No session token available",
                ),
                fetched_at=fetched_at,
            ),
        )
        return 1

    try:
        snapshot = fetch_usage_snapshot(token, client=client)
    except UsageSummaryHttpError as exc:
        write_cache_envelope(
            path,
            CacheEnvelopeError(
                ok=False,
                error=CacheError(code=_normalize_error_code(exc.code), message=exc.message),
                fetched_at=fetched_at,
            ),
        )
        return 1

    write_cache_envelope(
        path,
        CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=fetched_at),
    )
    return 0


def _normalize_error_code(code: str) -> str:
    if code in ("not_authenticated", "invalid_token", "network", "blocked_or_waf", "unknown"):
        return code
    return "unknown"
