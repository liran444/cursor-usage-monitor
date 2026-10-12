"""Orchestrate fetch + cache write."""

from __future__ import annotations

import os
from pathlib import Path

from cursor_usage_app.api.client import UsageSummaryClient, UsageSummaryHttpError
from cursor_usage_app.api.usage_summary import fetch_usage_snapshot
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.cache.usage_cache import (
    CacheEnvelopeError,
    CacheEnvelopeOk,
    CacheError,
    default_cache_path,
    utc_now_iso,
    write_cache_envelope,
)

_TEST_TOKEN_ENV = "CURSOR_USAGE_TOKEN_TEST"


def resolve_session_token(store: SessionStore | None = None) -> str | None:
    """Load token from session store; tests may use CURSOR_USAGE_TOKEN_TEST."""
    env_token = os.environ.get(_TEST_TOKEN_ENV)
    if env_token is not None:
        stripped = env_token.strip()
        if stripped != "":
            return stripped

    session_store = store or SessionStore()
    return session_store.get_token()


def run_fetch(
    cache_path: Path | None = None,
    client: UsageSummaryClient | None = None,
    store: SessionStore | None = None,
) -> int:
    """
    Fetch usage-summary and write cache envelope.

    Returns process exit code (0 success, 1 failure).
    """
    path = cache_path or default_cache_path()
    token = resolve_session_token(store=store)
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
