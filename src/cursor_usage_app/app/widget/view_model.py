"""Map cache envelope to widget display state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cursor_usage_app.cache.usage_cache import CacheEnvelope, CacheEnvelopeError, CacheEnvelopeOk
from cursor_usage_app.domain.models import UsageSnapshot

UiPhase = Literal["loading", "ok", "error"]


@dataclass(frozen=True)
class WidgetViewModel:
    phase: UiPhase
    snapshot: UsageSnapshot | None
    error_code: str | None
    error_message: str | None
    fetched_at: str | None
    inline_message: str | None

    @property
    def show_team_row(self) -> bool:
        if self.snapshot is None or self.snapshot.team_pool is None:
            return False
        pool = self.snapshot.team_pool
        return pool.has_limit or (pool.used_usd is not None and pool.used_usd > 0)

    @property
    def show_on_demand_card(self) -> bool:
        if self.snapshot is None:
            return False
        return self.snapshot.on_demand_display.show_card


def view_model_from_envelope(envelope: CacheEnvelope | None) -> WidgetViewModel:
    if envelope is None:
        return WidgetViewModel(
            phase="error",
            snapshot=None,
            error_code="unknown",
            error_message="No cached data yet. Use Refresh or set a session token.",
            fetched_at=None,
            inline_message="No cached data yet. Use Refresh or set a session token.",
        )

    if isinstance(envelope, CacheEnvelopeOk):
        return WidgetViewModel(
            phase="ok",
            snapshot=envelope.data,
            error_code=None,
            error_message=None,
            fetched_at=envelope.fetched_at,
            inline_message=None,
        )

    if isinstance(envelope, CacheEnvelopeError):
        return _view_model_from_error(envelope)

    return WidgetViewModel(
        phase="error",
        snapshot=None,
        error_code="unknown",
        error_message="Invalid cache",
        fetched_at=None,
        inline_message="Could not read cache.",
    )


def view_model_loading(previous: WidgetViewModel | None = None) -> WidgetViewModel:
    return WidgetViewModel(
        phase="loading",
        snapshot=previous.snapshot if previous is not None else None,
        error_code=None,
        error_message=None,
        fetched_at=previous.fetched_at if previous is not None else None,
        inline_message="Refreshing…",
    )


def _view_model_from_error(envelope: CacheEnvelopeError) -> WidgetViewModel:
    code = envelope.error.code
    message = envelope.error.message
    inline = _inline_for_code(code, message)
    return WidgetViewModel(
        phase="error",
        snapshot=None,
        error_code=code,
        error_message=message,
        fetched_at=envelope.fetched_at,
        inline_message=inline,
    )


def _inline_for_code(code: str, message: str) -> str:
    if code == "not_authenticated":
        return "Not signed in. Set a session token to fetch usage."
    if code == "invalid_token":
        return "Session token invalid or expired. Set a new token."
    if code == "network":
        return f"Network error: {message}"
    if code == "blocked_or_waf":
        return "Request blocked. Try again later or sign in via browser."
    return message or "Something went wrong."
